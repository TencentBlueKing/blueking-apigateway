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
	"fmt"
	"time"

	"github.com/TencentBlueKing/gopkg/stringx"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"go.uber.org/zap"

	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/sentry"
	"mcp_proxy/pkg/util"
)

// LoggingMiddleware returns a middleware that logs all MCP method calls with timing information.
func LoggingMiddleware(serverName string) mcp.Middleware {
	logger := logging.GetAPILogger()

	return func(next mcp.MethodHandler) mcp.MethodHandler {
		return func(ctx context.Context, method string, req mcp.Request) (mcp.Result, error) {
			start := time.Now()

			// Call the next handler
			result, err := next(ctx, method, req)

			// Calculate latency in microseconds (与 logger.go 保持一致)
			duration := time.Since(start)

			hasError := err != nil

			// 序列化请求参数
			var params string
			if req != nil {
				if paramsBytes, marshalErr := json.Marshal(req.GetParams()); marshalErr == nil {
					params = stringx.Truncate(string(paramsBytes), 2048)
				}
			}

			// 序列化响应结果
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

			// 从 context 获取更多信息
			gatewayID := util.GetGatewayIDFromContext(ctx)
			mcpServerID := util.GetMCPServerIDFromContext(ctx)
			requestID := util.GetRequestIDFromContext(ctx)
			appCode := util.GetAppCodeFromContext(ctx)
			username := util.GetUsernameFromContext(ctx)

			// 获取 session ID
			var sessionID string
			if ss, ok := req.GetSession().(*mcp.ServerSession); ok && ss != nil {
				sessionID = ss.ID()
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
				zap.String("app_code", appCode),
				zap.String("username", username),
			}

			if hasError {
				fields = append(fields, zap.Error(err))
				// 上报错误到 sentry
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

// AddLoggingMiddleware adds logging middleware to the MCP server
func AddLoggingMiddleware(server *mcp.Server, serverName string) {
	server.AddReceivingMiddleware(LoggingMiddleware(serverName))
}
