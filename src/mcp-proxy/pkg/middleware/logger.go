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
	"bytes"
	"fmt"
	"net/http"
	"time"

	"github.com/TencentBlueKing/gopkg/stringx"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/sentry"
	"mcp_proxy/pkg/util"
)

const (
	// MaxLogBodySize defines the maximum size for logging request/response bodies
	MaxLogBodySize = 2048 // 2KB
)

type bodyLogWriter struct {
	gin.ResponseWriter
	body *bytes.Buffer
}

// Write will write body and return the length of body
func (w bodyLogWriter) Write(b []byte) (int, error) {
	w.body.Write(b)
	return w.ResponseWriter.Write(b)
}

// APILogger is a middleware to log request
func APILogger() gin.HandlerFunc {
	logger := logging.GetAPILogger()

	return func(c *gin.Context) {
		fields := logContextFields(c)
		logger.Info("-", fields...)
	}
}

func logContextFields(c *gin.Context) []zap.Field {
	start := time.Now()
	// request body
	var body string
	requestBody, err := util.ReadRequestBody(c.Request)
	if err != nil {
		body = ""
	} else {
		body = util.TruncateBytesToString(requestBody, MaxLogBodySize)
	}

	newWriter := &bodyLogWriter{body: bytes.NewBufferString(""), ResponseWriter: c.Writer}
	c.Writer = newWriter

	// set inner app code
	mcpName := c.Param("name")
	if mcpName != "" {
		// get mcp_id by name
		mcp, err := cacheimpls.GetMCPServerByName(c.Request.Context(), mcpName)
		if err != nil {
			util.BadRequestErrorJSONResponse(c, fmt.Sprintf("get mcp by name %s failed: %v", mcpName, err))
			c.Abort()
			return nil
		}
		// set mcp_id to ctx
		util.SetMCPServerID(c, mcp.ID)
		// set mcp_name to ctx
		util.SetMCPServerName(c, mcpName)
		// set gateway_id to ctx
		util.SetGatewayID(c, mcp.GatewayID)
	}

	c.Next()

	duration := time.Since(start)

	latency := float64(duration) / float64(time.Microsecond)

	status := c.Writer.Status()

	params := stringx.Truncate(c.Request.URL.RawQuery, MaxLogBodySize)
	
	// Always truncate response body to prevent excessive log size
	responseBody := stringx.Truncate(newWriter.body.String(), MaxLogBodySize)
	
	fields := []zap.Field{
		zap.Int("gateway_id", util.GetGatewayID(c)),
		zap.String("mcp_server_name", mcpName),
		zap.Int("mcp_server_id", util.GetMCPServerID(c)),
		zap.String("method", c.Request.Method),
		zap.String("path", c.Request.URL.Path),
		zap.String("params", params),
		zap.String("body", body),
		zap.Int("status", status),
		zap.Float64("latency", latency),
		zap.String("request_id", c.GetString(util.RequestIDKey)),
		zap.String("instance_id", c.GetString(util.InstanceIDKey)),
		zap.String("client_ip", c.ClientIP()),
		zap.String("response_body", responseBody),
	}

	// only send 5xx err to sentry
	if status >= http.StatusInternalServerError {
		sentry.ReportToSentry(
			fmt.Sprintf("%s %s ", c.Request.Method, c.Request.URL.Path),
			map[string]interface{}{
				"fields": fields,
			},
		)
	}
	return fields
}
