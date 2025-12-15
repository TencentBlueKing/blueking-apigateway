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
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

func TestMCPServerHeaderMiddleware(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name            string
		timeout         string
		allowedHeaders  string
		expectedTimeout int
	}{
		{
			name:            "with timeout header",
			timeout:         "30",
			allowedHeaders:  "",
			expectedTimeout: 30,
		},
		{
			name:            "without timeout header",
			timeout:         "",
			allowedHeaders:  "",
			expectedTimeout: 0,
		},
		{
			name:            "with allowed headers",
			timeout:         "60",
			allowedHeaders:  "X-Custom-Header,X-Another-Header",
			expectedTimeout: 60,
		},
		{
			name:            "invalid timeout value",
			timeout:         "invalid",
			allowedHeaders:  "",
			expectedTimeout: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			if tt.timeout != "" {
				c.Request.Header.Set(constant.BkApiTimeoutHeaderKey, tt.timeout)
			}
			if tt.allowedHeaders != "" {
				c.Request.Header.Set(constant.BkApiAllowedHeadersKey, tt.allowedHeaders)
			}

			middleware := MCPServerHeaderMiddleware()
			middleware(c)

			// Check that timeout was set correctly
			timeout := util.GetBkApiTimeout(c.Request.Context())
			if tt.expectedTimeout == 0 {
				// Default timeout is 5 minutes
				assert.Equal(t, 5*60, int(timeout.Seconds()))
			} else {
				assert.Equal(t, tt.expectedTimeout, int(timeout.Seconds()))
			}
		})
	}
}

func TestMCPServerHeaderMiddleware_AllowedHeaders(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	// Set allowed headers and their values
	c.Request.Header.Set(constant.BkApiAllowedHeadersKey, "X-Custom-Header,X-Another-Header")
	c.Request.Header.Set("X-Custom-Header", "custom-value")
	c.Request.Header.Set("X-Another-Header", "another-value")

	// Set MCP server info for the middleware
	util.SetMCPServerID(c, 1)
	util.SetMCPServerName(c, "test-server")

	middleware := MCPServerHeaderMiddleware()
	middleware(c)

	// Check that allowed headers were extracted
	headers := util.GetBkApiAllowedHeaders(c.Request.Context())
	assert.NotNil(t, headers)
	assert.Equal(t, "custom-value", headers["X-Custom-Header"])
	assert.Equal(t, "another-value", headers["X-Another-Header"])
}
