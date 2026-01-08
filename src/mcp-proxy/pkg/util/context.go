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

// Package util ...
package util

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"mcp_proxy/pkg/constant"
)

// SetBkUsername ...
func SetBkUsername(c *gin.Context, userName string) {
	c.Set(string(constant.BkUsername), userName)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BkUsername, userName))
	}
}

// SetBkAppCode ...
func SetBkAppCode(c *gin.Context, appCode string) {
	c.Set(string(constant.BkAppCode), appCode)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BkAppCode, appCode))
	}
}

// GetBkAppCode ...
func GetBkAppCode(c *gin.Context) string {
	appCode, ok := c.Get(string(constant.BkAppCode))
	if !ok {
		return ""
	}
	return appCode.(string)
}

// GetAppCode is an alias for GetBkAppCode
func GetAppCode(c *gin.Context) string {
	return GetBkAppCode(c)
}

// GetAppCodeFromContext gets app code from context
func GetAppCodeFromContext(ctx context.Context) string {
	if appCode, ok := ctx.Value(constant.BkAppCode).(string); ok {
		return appCode
	}
	return ""
}

// GetUsernameFromContext gets username from context
func GetUsernameFromContext(ctx context.Context) string {
	if username, ok := ctx.Value(constant.BkUsername).(string); ok {
		return username
	}
	return ""
}

// SetInnerJWTToken ...
func SetInnerJWTToken(c *gin.Context, jwtToken string) {
	c.Set(string(constant.BkGatewayInnerJWT), jwtToken)
	if c.Request != nil {
		c.Request = c.Request.WithContext(
			context.WithValue(c.Request.Context(), constant.BkGatewayInnerJWT, jwtToken))
	}
}

// SetMCPServerID ...
func SetMCPServerID(c *gin.Context, mcpServerID int) {
	c.Set(string(constant.MCPServerID), mcpServerID)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.MCPServerID, mcpServerID))
	}
}

// SetMCPServerName ...
func SetMCPServerName(c *gin.Context, mcpServerName string) {
	c.Set(string(constant.MCPServerName), mcpServerName)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.MCPServerName, mcpServerName))
	}
}

// GetMCPServerName ...
func GetMCPServerName(c *gin.Context) string {
	mcpServerName, ok := c.Get(string(constant.MCPServerName))
	if !ok {
		return ""
	}
	return mcpServerName.(string)
}

// GetMCPServerID ...
func GetMCPServerID(c *gin.Context) int {
	mcpServerID, ok := c.Get(string(constant.MCPServerID))
	if !ok {
		return 0
	}
	return mcpServerID.(int)
}

// GetMCPServerIDFromContext gets MCP server ID from context
func GetMCPServerIDFromContext(ctx context.Context) int {
	if mcpServerID, ok := ctx.Value(constant.MCPServerID).(int); ok {
		return mcpServerID
	}
	return 0
}

// SetGatewayID ...
func SetGatewayID(c *gin.Context, gatewayID int) {
	c.Set(string(constant.GatewayID), gatewayID)
	if c.Request != nil {
		c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.GatewayID, gatewayID))
	}
}

// GetGatewayID ...
func GetGatewayID(c *gin.Context) int {
	mcpServerID, ok := c.Get(string(constant.GatewayID))
	if !ok {
		return 0
	}
	return mcpServerID.(int)
}

// GetGatewayIDFromContext ...
func GetGatewayIDFromContext(ctx context.Context) int {
	gatewayID, ok := ctx.Value(constant.GatewayID).(int)
	if !ok {
		return 0
	}
	return gatewayID
}

// GetInnerJWTTokenFromContext ...
func GetInnerJWTTokenFromContext(ctx context.Context) string {
	jwtToken := ctx.Value(constant.BkGatewayInnerJWT)
	if innerJwt, ok := jwtToken.(string); ok {
		return innerJwt
	}
	return ""
}

// SetBkApiTimeout ...
func SetBkApiTimeout(c *gin.Context, timeout int) {
	c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BkApiTimeout, timeout))
}

// GetBkApiTimeout returns the timeout duration for the BK API call
func GetBkApiTimeout(ctx context.Context) time.Duration {
	// Get the timeout value from the context
	timeout, ok := ctx.Value(constant.BkApiTimeout).(int)
	if !ok || timeout == 0 {
		// default timeout is 5 minute
		return 5 * time.Minute
	}
	return time.Duration(timeout) * time.Second
}

// SetBkApiAllowedHeaders ... 设置允许的请求头
func SetBkApiAllowedHeaders(c *gin.Context, allowedHeaders string) {
	allowedHeadersMap := make(map[string]string)
	for _, header := range strings.Split(allowedHeaders, ",") {
		header = strings.TrimSpace(header)
		if header == "" {
			continue
		}
		allowedHeadersMap[header] = c.Request.Header.Get(header)
	}
	// 默认添加 mcp-server 相关请求头
	allowedHeadersMap[constant.BkApiMCPServerIDKey] = fmt.Sprintf("%d", GetMCPServerID(c))
	allowedHeadersMap[constant.BkApiMCPServerNameKey] = GetMCPServerName(c)
	c.Request = c.Request.WithContext(context.WithValue(c.Request.Context(), constant.BkApiAllowedHeaders,
		allowedHeadersMap))
}

// GetBkApiAllowedHeaders ... 获取允许的请求头
func GetBkApiAllowedHeaders(ctx context.Context) map[string]string {
	// Get the timeout value from the context
	allowedHeaders, ok := ctx.Value(constant.BkApiAllowedHeaders).(map[string]string)
	if !ok {
		return map[string]string{}
	}
	return allowedHeaders
}

// JWTClaimsForLazySigning 用于延迟签发 JWT 的 claims 信息
type JWTClaimsForLazySigning struct {
	AppCode      string
	AppVerified  bool
	Username     string
	UserVerified bool
	Issuer       string
	Audience     []string
}

// SetJWTClaimsForLazySigning 保存 JWT claims 和私钥到 context，用于延迟签发
func SetJWTClaimsForLazySigning(c *gin.Context, claims *JWTClaimsForLazySigning, privateKey []byte) {
	c.Set(string(constant.BkGatewayJWTClaims), claims)
	c.Set(string(constant.BkGatewayPrivateKey), privateKey)
	if c.Request != nil {
		ctx := c.Request.Context()
		ctx = context.WithValue(ctx, constant.BkGatewayJWTClaims, claims)
		ctx = context.WithValue(ctx, constant.BkGatewayPrivateKey, privateKey)
		c.Request = c.Request.WithContext(ctx)
	}
}

// GetJWTClaimsFromContext 从 context 获取 JWT claims
func GetJWTClaimsFromContext(ctx context.Context) *JWTClaimsForLazySigning {
	if claims, ok := ctx.Value(constant.BkGatewayJWTClaims).(*JWTClaimsForLazySigning); ok {
		return claims
	}
	return nil
}

// GetPrivateKeyFromContext 从 context 获取私钥
func GetPrivateKeyFromContext(ctx context.Context) []byte {
	if key, ok := ctx.Value(constant.BkGatewayPrivateKey).([]byte); ok {
		return key
	}
	return nil
}
