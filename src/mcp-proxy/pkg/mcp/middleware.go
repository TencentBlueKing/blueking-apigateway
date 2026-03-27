/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package mcp

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/TencentBlueKing/gopkg/stringx"
	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.uber.org/zap"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/sentry"
	"mcp_proxy/pkg/infra/trace"
	"mcp_proxy/pkg/metric"
	"mcp_proxy/pkg/util"
)

// knownJSONRPCErrorCodes maps standard JSON-RPC error codes to human-readable categories.
// Codes outside this set are normalized to "other" to prevent high-cardinality issues.
var knownJSONRPCErrorCodes = map[int64]string{
	-32700: "parse_error",
	-32600: "invalid_request",
	-32601: "method_not_found",
	-32602: "invalid_params",
	-32603: "internal_error",
}

// matchErrorCodeName converts a JSON-RPC error code to a bounded label value.
func matchErrorCodeName(code int64) string {
	if name, ok := knownJSONRPCErrorCodes[code]; ok {
		return name
	}
	return strconv.FormatInt(code, 10)
}

// LoggingMiddleware returns a middleware that logs all MCP method calls with timing information.
func LoggingMiddleware(serverName string) mcp.Middleware {
	logger := logging.GetAPILogger()

	return func(next mcp.MethodHandler) mcp.MethodHandler {
		return func(ctx context.Context, method string, req mcp.Request) (mcp.Result, error) {
			start := time.Now()

			// Call the next handler
			result, err := next(ctx, method, req)

			duration := time.Since(start)

			hasError := err != nil

			// Resolve truncation limits from config
			logTruncate := config.G.McpServer.LogTruncate

			// Serialize request params and calculate body sizes
			var params string
			var requestBodySize int64
			if req != nil {
				if paramsBytes, marshalErr := json.Marshal(req.GetParams()); marshalErr == nil {
					requestBodySize = int64(len(paramsBytes))
					params = stringx.Truncate(string(paramsBytes), logTruncate.GetAPILogRequestSize())
				}
			}

			// Serialize response result with truncation
			// 正常响应截断到 APILogResponseSize，错误响应截断到 APILogErrorResponseSize（保留更多诊断信息）
			var response string
			var responseBodySize int64
			if result != nil {
				if resultBytes, marshalErr := json.Marshal(result); marshalErr == nil {
					responseBodySize = int64(len(resultBytes))
					if hasError {
						response = stringx.Truncate(string(resultBytes), logTruncate.GetAPILogErrorResponseSize())
					} else {
						response = stringx.Truncate(string(resultBytes), logTruncate.GetAPILogResponseSize())
					}
				}
			}

			// Retrieve extra info from context
			gatewayID := util.GetGatewayIDFromContext(ctx)
			gatewayName := util.GetGatewayNameFromContext(ctx)
			mcpServerID := util.GetMCPServerIDFromContext(ctx)
			requestID := util.GetRequestIDFromContext(ctx)
			xRequestID := util.GetXRequestIDFromContext(ctx)
			appCode := util.GetAppCodeFromContext(ctx)
			username := util.GetUsernameFromContext(ctx)
			clientIP := util.GetClientIPFromContext(ctx)
			clientID := util.GetClientIDFromContext(ctx)

			// Get session ID and client_id from session's InitializeParams
			var sessionID string
			if req != nil {
				if ss, ok := req.GetSession().(*mcp.ServerSession); ok && ss != nil {
					sessionID = ss.ID()
					// Enrich client_id with clientInfo from initialize handshake
					if initParams := ss.InitializeParams(); initParams != nil && initParams.ClientInfo != nil {
						clientID = initParams.ClientInfo.Name
					}
				}
			}

			// Extract tool_name for tools/call
			var toolName string
			if method == "tools/call" {
				toolName = extractToolName(req)
			}

			// trace_id 来自 HTTP 层（otelgin middleware）注入的 span，与 TracingMiddleware 属于同一条 trace
			traceID := trace.GetTraceIDFromContext(ctx)

			fields := []zap.Field{
				// 链路标识
				zap.String("request_id", requestID),
				zap.String("x_request_id", xRequestID),
				zap.String("session_id", sessionID),
				// 网关信息
				zap.Int("gateway_id", gatewayID),
				zap.String("gateway_name", gatewayName),
				// MCP 请求信息
				zap.String("mcp_server_name", serverName),
				zap.Int("mcp_server_id", mcpServerID),
				zap.String("mcp_method", method),
				// 调用方信息
				zap.String("app_code", appCode),
				zap.String("bk_username", username),
				zap.String("client_ip", clientIP),
				zap.String("client_id", clientID),
				// Tool 特有字段
				zap.String("tool_name", toolName),
				// 请求/响应内容
				zap.String("params", params),
				zap.String("response", response),
				// 体积信息
				zap.Int64("request_body_size", requestBodySize),
				zap.Int64("response_body_size", responseBodySize),
				// 性能
				zap.String("latency", duration.String()),
			}

			// 仅在 trace_id 非空时附加，避免日志中出现空 trace_id 字段
			if traceID != "" {
				fields = append(fields, zap.String("trace_id", traceID))
			}

			if hasError {
				fields = append(fields, zap.Error(err))
				// Only report server-side errors to Sentry, skip client errors
				// (parse_error, invalid_request, method_not_found, invalid_params)
				if shouldReportToSentry(err) {
					sentry.ReportToSentry(
						fmt.Sprintf("MCP %s %s", serverName, method),
						map[string]string{
							"mcp_server_name": serverName,
							"mcp_method":      method,
							"gateway_name":    gatewayName,
							"app_code":        appCode,
						},
						map[string]interface{}{
							"request_id":    requestID,
							"x_request_id":  xRequestID,
							"session_id":    sessionID,
							"gateway_id":    gatewayID,
							"mcp_server_id": mcpServerID,
							"client_ip":     clientIP,
							"client_id":     clientID,
							"bk_username":   username,
							"tool_name":     toolName,
							"params":        params,
							"response":      response,
							"latency":       duration.String(),
							"error":         err.Error(),
						},
					)
				}
			}

			logger.Info("-", fields...)

			return result, err
		}
	}
}

// AddLoggingMiddleware adds logging middleware to the MCP server.
func AddLoggingMiddleware(server *mcp.Server, serverName string) {
	server.AddReceivingMiddleware(LoggingMiddleware(serverName))
}

// MetricMiddleware returns a middleware that records MCP protocol-level Prometheus metrics.
// It tracks request counts, durations, tool calls, and error codes.
func MetricMiddleware(serverName string) mcp.Middleware {
	return func(next mcp.MethodHandler) mcp.MethodHandler {
		return func(ctx context.Context, method string, req mcp.Request) (mcp.Result, error) {
			start := time.Now()

			result, err := next(ctx, method, req)

			duration := time.Since(start)
			hasError := err != nil
			gatewayName := util.GetGatewayNameFromContext(ctx)

			// 1. MCPRequestTotal: method call count with error_code and error (0/1)
			errorLabel := "0"
			errorCode := "0"
			if hasError {
				errorLabel = "1"
				errorCode = "unknown"
				var jsonrpcErr *jsonrpc.Error
				if errors.As(err, &jsonrpcErr) {
					errorCode = matchErrorCodeName(jsonrpcErr.Code)
				}
			}
			metric.MCPRequestTotal.WithLabelValues(gatewayName, serverName, method, errorCode, errorLabel).Inc()

			// 2. MCPRequestDuration: method call latency (preserve sub-millisecond precision)
			metric.MCPRequestDuration.WithLabelValues(gatewayName, serverName, method).Observe(
				duration.Seconds() * 1000,
			)

			// 3. MCPToolCallTotal: per-tool breakdown for tools/call
			if method == "tools/call" {
				toolName := extractToolName(req)
				metric.MCPToolCallTotal.WithLabelValues(gatewayName, serverName, toolName, errorCode, errorLabel).Inc()
			}

			// 4. MCPSessionTotal: increment on successful initialize
			if method == "initialize" && !hasError {
				metric.MCPSessionTotal.WithLabelValues(gatewayName, serverName).Inc()
			}

			// 5. MCPErrorTotal: error count by error code (reuse errorCode from step 1)
			if hasError {
				metric.MCPErrorTotal.WithLabelValues(gatewayName, serverName, method, errorCode).Inc()
			}

			return result, err
		}
	}
}

// AddMetricMiddleware adds metric middleware to the MCP server.
func AddMetricMiddleware(server *mcp.Server, serverName string) {
	server.AddReceivingMiddleware(MetricMiddleware(serverName))
}

// clientErrorCodes are JSON-RPC error codes that indicate client-side issues
// and should NOT be reported to Sentry to avoid noise.
var clientErrorCodes = map[int64]struct{}{
	-32700: {}, // parse_error
	-32600: {}, // invalid_request
	-32601: {}, // method_not_found
	-32602: {}, // invalid_params
}

// shouldReportToSentry determines whether an MCP error should be reported to Sentry.
// Client errors (parse_error, invalid_request, method_not_found, invalid_params) are
// filtered out; only internal errors (-32603) and unknown errors are reported.
func shouldReportToSentry(err error) bool {
	if err == nil {
		return false
	}
	var jsonrpcErr *jsonrpc.Error
	if errors.As(err, &jsonrpcErr) {
		if _, isClient := clientErrorCodes[jsonrpcErr.Code]; isClient {
			return false
		}
	}
	return true
}

// extractToolName extracts the tool name from a tools/call request.
func extractToolName(req mcp.Request) string {
	if req == nil {
		return ""
	}
	params := req.GetParams()
	if params == nil {
		return ""
	}
	if callParams, ok := params.(*mcp.CallToolParamsRaw); ok {
		return callParams.Name
	}
	return ""
}

// SessionMetricMiddleware returns a middleware that tracks active MCP sessions.
// It decrements the session gauge when a session ends (notifications/cancelled).
//
// KNOWN LIMITATION: notifications/cancelled is an approximation. Clients that crash
// or lose network connectivity will NOT send this notification, causing the gauge to
// drift upward over time. When interpreting MCPSessionTotal in Grafana, treat it as a
// best-effort approximation rather than an exact count.
//
// TODO: A future improvement could use HTTP-layer disconnect detection (e.g., SSE
// connection close callback) for more accurate tracking of active sessions.
func SessionMetricMiddleware(serverName string) mcp.Middleware {
	return func(next mcp.MethodHandler) mcp.MethodHandler {
		return func(ctx context.Context, method string, req mcp.Request) (mcp.Result, error) {
			result, err := next(ctx, method, req)

			// Decrement session gauge on notifications/cancelled
			if method == "notifications/cancelled" {
				gatewayName := util.GetGatewayNameFromContext(ctx)
				metric.MCPSessionTotal.WithLabelValues(gatewayName, serverName).Dec()
			}

			return result, err
		}
	}
}

// AddSessionMetricMiddleware adds session metric middleware to the MCP server.
func AddSessionMetricMiddleware(server *mcp.Server, serverName string) {
	server.AddReceivingMiddleware(SessionMetricMiddleware(serverName))
}

// TracingMiddleware returns a middleware that creates OpenTelemetry spans for MCP method calls.
// Each span carries the MCP method, server name, gateway info, session ID, and error details.
func TracingMiddleware(serverName string) mcp.Middleware {
	return func(next mcp.MethodHandler) mcp.MethodHandler {
		return func(ctx context.Context, method string, req mcp.Request) (mcp.Result, error) {
			// Replace "/" with "." in method names to avoid issues with some trace backends
			spanName := fmt.Sprintf("mcp.%s", strings.ReplaceAll(method, "/", "."))
			ctx, span := trace.StartTrace(ctx, spanName)
			if span != nil {
				defer span.End()

				// Set common attributes
				span.SetAttributes(
					attribute.String("mcp.server_name", serverName),
					attribute.String("mcp.method", method),
				)

				// Add context attributes
				if gatewayName := util.GetGatewayNameFromContext(ctx); gatewayName != "" {
					span.SetAttributes(attribute.String("mcp.gateway_name", gatewayName))
				}
				if requestID := util.GetRequestIDFromContext(ctx); requestID != "" {
					span.SetAttributes(attribute.String("mcp.request_id", requestID))
				}
				if xRequestID := util.GetXRequestIDFromContext(ctx); xRequestID != "" {
					span.SetAttributes(attribute.String("mcp.x_request_id", xRequestID))
				}

				// Add session ID
				if req != nil {
					if ss, ok := req.GetSession().(*mcp.ServerSession); ok && ss != nil {
						span.SetAttributes(attribute.String("mcp.session_id", ss.ID()))
					}
				}

				// For tools/call, add tool name
				if method == "tools/call" {
					toolName := extractToolName(req)
					if toolName != "" {
						span.SetAttributes(attribute.String("mcp.tool_name", toolName))
					}
				}
			}

			result, err := next(ctx, method, req)

			if span != nil && err != nil {
				span.SetStatus(codes.Error, err.Error())
				span.RecordError(err)
				var jsonrpcErr *jsonrpc.Error
				if errors.As(err, &jsonrpcErr) {
					span.SetAttributes(attribute.Int64("mcp.error_code", jsonrpcErr.Code))
				}
			}

			return result, err
		}
	}
}

// AddTracingMiddleware adds tracing middleware to the MCP server.
func AddTracingMiddleware(server *mcp.Server, serverName string) {
	server.AddReceivingMiddleware(TracingMiddleware(serverName))
}
