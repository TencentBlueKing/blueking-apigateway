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
	"time"

	"github.com/TencentBlueKing/gopkg/stringx"
	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"go.uber.org/zap"

	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/sentry"
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

// normalizeErrorCode converts a JSON-RPC error code to a bounded label value.
func normalizeErrorCode(code int64) string {
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

			// Serialize request params
			var params string
			if req != nil {
				if paramsBytes, marshalErr := json.Marshal(req.GetParams()); marshalErr == nil {
					params = stringx.Truncate(string(paramsBytes), 2048)
				}
			}

			// Serialize response result
			var response string
			if result != nil {
				if resultBytes, marshalErr := json.Marshal(result); marshalErr == nil {
					if hasError {
						response = string(resultBytes)
					} else {
						response = stringx.Truncate(string(resultBytes), 1024)
					}
				}
			}

			// Retrieve extra info from context
			gatewayID := util.GetGatewayIDFromContext(ctx)
			mcpServerID := util.GetMCPServerIDFromContext(ctx)
			requestID := util.GetRequestIDFromContext(ctx)
			xRequestID := util.GetXRequestIDFromContext(ctx)
			appCode := util.GetAppCodeFromContext(ctx)
			username := util.GetUsernameFromContext(ctx)

			// Get session ID
			var sessionID string
			if req != nil {
				if ss, ok := req.GetSession().(*mcp.ServerSession); ok && ss != nil {
					sessionID = ss.ID()
				}
			}

			fields := []zap.Field{
				zap.Int("gateway_id", gatewayID),
				zap.String("mcp_server_name", serverName),
				zap.Int("mcp_server_id", mcpServerID),
				zap.String("mcp_method", method),
				zap.String("session_id", sessionID),
				zap.String("params", params),
				zap.String("latency", duration.String()),
				zap.String("response", response),
				zap.String("request_id", requestID),
				zap.String("x_request_id", xRequestID),
				zap.String("app_code", appCode),
				zap.String("username", username),
			}

			if hasError {
				fields = append(fields, zap.Error(err))
				// Report error to sentry
				sentry.ReportToSentry(
					fmt.Sprintf("MCP %s %s", serverName, method),
					map[string]interface{}{
						"fields": fields,
					},
				)
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

			// 1. MCPRequestTotal: method call count
			status := "ok"
			if hasError {
				status = "error"
			}
			metric.MCPRequestTotal.WithLabelValues(gatewayName, serverName, method, status).Inc()

			// 2. MCPRequestDuration: method call latency (preserve sub-millisecond precision)
			metric.MCPRequestDuration.WithLabelValues(gatewayName, serverName, method).Observe(
				duration.Seconds() * 1000,
			)

			// 3. MCPToolCallTotal: per-tool breakdown for tools/call
			if method == "tools/call" {
				toolName := extractToolName(req)
				metric.MCPToolCallTotal.WithLabelValues(gatewayName, serverName, toolName, status).Inc()
			}

			// 4. MCPSessionTotal: increment on successful initialize
			if method == "initialize" && !hasError {
				metric.MCPSessionTotal.WithLabelValues(gatewayName, serverName).Inc()
			}

			// 5. MCPErrorTotal: error count by error code
			if hasError {
				errorCode := "unknown"
				var jsonrpcErr *jsonrpc.Error
				if errors.As(err, &jsonrpcErr) {
					errorCode = normalizeErrorCode(jsonrpcErr.Code)
				}
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
// NOTE: notifications/cancelled is an approximation; clients that crash or lose network
// will not send this notification. A future improvement could use HTTP-layer disconnect
// detection for more accurate tracking.
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
