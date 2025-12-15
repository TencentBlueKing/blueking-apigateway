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

package util

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/constant"
)

func TestSetAndGetBkUsername(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetBkUsername(c, "test-user")

	// Get from gin context
	username, exists := c.Get(string(constant.BkUsername))
	assert.True(t, exists)
	assert.Equal(t, "test-user", username)

	// Get from request context
	usernameFromCtx := c.Request.Context().Value(constant.BkUsername)
	assert.Equal(t, "test-user", usernameFromCtx)
}

func TestSetAndGetBkAppCode(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetBkAppCode(c, "test-app")

	// Get from gin context
	appCode := GetBkAppCode(c)
	assert.Equal(t, "test-app", appCode)

	// Get from request context
	appCodeFromCtx := c.Request.Context().Value(constant.BkAppCode)
	assert.Equal(t, "test-app", appCodeFromCtx)
}

func TestGetBkAppCode_NotSet(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	appCode := GetBkAppCode(c)
	assert.Empty(t, appCode)
}

func TestSetAndGetInnerJWTToken(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetInnerJWTToken(c, "test-jwt-token")

	// Get from gin context
	token, exists := c.Get(string(constant.BkGatewayInnerJWT))
	assert.True(t, exists)
	assert.Equal(t, "test-jwt-token", token)

	// Get from request context
	tokenFromCtx := GetInnerJWTTokenFromContext(c.Request.Context())
	assert.Equal(t, "test-jwt-token", tokenFromCtx)
}

func TestGetInnerJWTTokenFromContext_NotSet(t *testing.T) {
	ctx := context.Background()
	token := GetInnerJWTTokenFromContext(ctx)
	assert.Empty(t, token)
}

func TestSetAndGetMCPServerID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetMCPServerID(c, 123)

	// Get from gin context
	serverID := GetMCPServerID(c)
	assert.Equal(t, 123, serverID)

	// Get from request context
	serverIDFromCtx := c.Request.Context().Value(constant.MCPServerID)
	assert.Equal(t, 123, serverIDFromCtx)
}

func TestGetMCPServerID_NotSet(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	serverID := GetMCPServerID(c)
	assert.Equal(t, 0, serverID)
}

func TestSetAndGetMCPServerName(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetMCPServerName(c, "test-server")

	// Get from gin context
	serverName := GetMCPServerName(c)
	assert.Equal(t, "test-server", serverName)

	// Get from request context
	serverNameFromCtx := c.Request.Context().Value(constant.MCPServerName)
	assert.Equal(t, "test-server", serverNameFromCtx)
}

func TestGetMCPServerName_NotSet(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	serverName := GetMCPServerName(c)
	assert.Empty(t, serverName)
}

func TestSetAndGetGatewayID(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetGatewayID(c, 456)

	// Get from gin context
	gatewayID := GetGatewayID(c)
	assert.Equal(t, 456, gatewayID)

	// Get from request context
	gatewayIDFromCtx := c.Request.Context().Value(constant.GatewayID)
	assert.Equal(t, 456, gatewayIDFromCtx)
}

func TestGetGatewayID_NotSet(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	gatewayID := GetGatewayID(c)
	assert.Equal(t, 0, gatewayID)
}

func TestSetAndGetBkApiTimeout(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetBkApiTimeout(c, 30)

	timeout := GetBkApiTimeout(c.Request.Context())
	assert.Equal(t, 30*time.Second, timeout)
}

func TestGetBkApiTimeout_Default(t *testing.T) {
	ctx := context.Background()
	timeout := GetBkApiTimeout(ctx)
	assert.Equal(t, 5*time.Minute, timeout)
}

func TestGetBkApiTimeout_Zero(t *testing.T) {
	ctx := context.WithValue(context.Background(), constant.BkApiTimeout, 0)
	timeout := GetBkApiTimeout(ctx)
	assert.Equal(t, 5*time.Minute, timeout) // Default when zero
}

func TestSetAndGetBkApiAllowedHeaders(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	// Set custom headers
	c.Request.Header.Set("X-Custom-Header", "custom-value")
	c.Request.Header.Set("X-Another-Header", "another-value")

	// Set MCP server info
	SetMCPServerID(c, 1)
	SetMCPServerName(c, "test-server")

	SetBkApiAllowedHeaders(c, "X-Custom-Header,X-Another-Header")

	headers := GetBkApiAllowedHeaders(c.Request.Context())
	assert.NotNil(t, headers)
	assert.Equal(t, "custom-value", headers["X-Custom-Header"])
	assert.Equal(t, "another-value", headers["X-Another-Header"])
	assert.Equal(t, "1", headers[constant.BkApiMCPServerIDKey])
	assert.Equal(t, "test-server", headers[constant.BkApiMCPServerNameKey])
}

func TestSetBkApiAllowedHeaders_EmptyString(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	SetMCPServerID(c, 1)
	SetMCPServerName(c, "test-server")

	SetBkApiAllowedHeaders(c, "")

	headers := GetBkApiAllowedHeaders(c.Request.Context())
	assert.NotNil(t, headers)
	// Should still have MCP server headers
	assert.Equal(t, "1", headers[constant.BkApiMCPServerIDKey])
	assert.Equal(t, "test-server", headers[constant.BkApiMCPServerNameKey])
}

func TestGetBkApiAllowedHeaders_NotSet(t *testing.T) {
	ctx := context.Background()
	headers := GetBkApiAllowedHeaders(ctx)
	assert.NotNil(t, headers)
	assert.Empty(t, headers)
}

func TestSetBkApiAllowedHeaders_WithSpaces(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	c.Request.Header.Set("X-Header-1", "value1")
	c.Request.Header.Set("X-Header-2", "value2")

	SetMCPServerID(c, 1)
	SetMCPServerName(c, "test-server")

	// Headers with spaces around commas
	SetBkApiAllowedHeaders(c, " X-Header-1 , X-Header-2 ")

	headers := GetBkApiAllowedHeaders(c.Request.Context())
	assert.NotNil(t, headers)
	// Note: The current implementation trims spaces from header names
	assert.Equal(t, "value1", headers["X-Header-1"])
	assert.Equal(t, "value2", headers["X-Header-2"])
}
