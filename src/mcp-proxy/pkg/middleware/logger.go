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

package middleware

import (
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/sentry"
	"mcp_proxy/pkg/util"
)

// APILogger is a middleware to log request
// 优化：移除 bodyLogWriter 避免 SSE 长连接场景下的内存泄露
// 详细的请求/响应参数由 MCP 层的日志中间件记录
func APILogger() gin.HandlerFunc {
	logger := logging.GetAPILogger()

	return func(c *gin.Context) {
		start := time.Now()

		// set mcp server info to context
		mcpName := c.Param("name")
		if mcpName != "" {
			mcp, err := cacheimpls.GetMCPServerByName(c.Request.Context(), mcpName)
			if err != nil {
				util.BadRequestErrorJSONResponse(c, fmt.Sprintf("get mcp by name %s failed: %v", mcpName, err))
				c.Abort()
				return
			}
			util.SetMCPServerID(c, mcp.ID)
			util.SetMCPServerName(c, mcpName)
			util.SetGatewayID(c, mcp.GatewayID)
		}

		c.Next()

		// Calculate latency in microseconds
		duration := time.Since(start)

		status := c.Writer.Status()

		fields := []zap.Field{
			zap.Int("gateway_id", util.GetGatewayID(c)),
			zap.String("mcp_server_name", mcpName),
			zap.Int("mcp_server_id", util.GetMCPServerID(c)),
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.Int("status", status),
			zap.String("latency", duration.String()),
			zap.String("request_id", c.GetString(util.RequestIDKey)),
			zap.String("instance_id", c.GetString(util.InstanceIDKey)),
			zap.String("client_ip", c.ClientIP()),
			zap.String("app_code", util.GetAppCode(c)),
		}

		// only send 5xx err to sentry
		if status >= http.StatusInternalServerError {
			sentry.ReportToSentry(
				fmt.Sprintf("%s %s", c.Request.Method, c.Request.URL.Path),
				map[string]interface{}{
					"fields": fields,
				},
			)
		}

		logger.Info("-", fields...)
	}
}
