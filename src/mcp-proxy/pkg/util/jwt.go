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
	"fmt"
	"time"

	jwt "github.com/golang-jwt/jwt/v4"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
)

// InnerJWTClaims 内部 JWT claims 结构
type InnerJWTClaims struct {
	App  InnerAppInfo  `json:"app"`
	User InnerUserInfo `json:"user"`
	jwt.RegisteredClaims
}

// InnerAppInfo 应用信息
type InnerAppInfo struct {
	AppCode  string `json:"app_code"`
	Verified bool   `json:"verified"`
}

// InnerUserInfo 用户信息
type InnerUserInfo struct {
	Verified bool   `json:"verified"`
	Username string `json:"username"`
}

// SignInnerJWTFromContext 从 context 中获取 claims 并签发 inner JWT
// 这是延迟签发的核心函数，只有在调用外部 API 时才会执行
func SignInnerJWTFromContext(ctx context.Context) (string, error) {
	claims := GetJWTClaimsFromContext(ctx)
	if claims == nil {
		return "", fmt.Errorf("jwt claims not found in context")
	}
	privateKey := GetPrivateKeyFromContext(ctx)
	if privateKey == nil {
		return "", fmt.Errorf("private key not found in context")
	}

	// 获取 mcp_server_id
	mcpServerID := 0
	if id, ok := ctx.Value(constant.MCPServerID).(int); ok {
		mcpServerID = id
	}

	return SignInnerJWT(claims, privateKey, mcpServerID)
}

// SignInnerJWT 签发内部 JWT
func SignInnerJWT(claims *JWTClaimsForLazySigning, privateKeyText []byte, mcpServerID int) (string, error) {
	innerJwtClaims := InnerJWTClaims{
		App: InnerAppInfo{
			AppCode:  fmt.Sprintf(constant.BkVirtualAppCodeFormat, mcpServerID, claims.AppCode),
			Verified: claims.AppVerified,
		},
		User: InnerUserInfo{
			Username: claims.Username,
			Verified: claims.UserVerified,
		},
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    claims.Issuer,
			Audience:  jwt.ClaimStrings(claims.Audience),
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(config.G.McpServer.InnerJwtExpireTime)),
			NotBefore: jwt.NewNumericDate(time.Now()),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodRS512, innerJwtClaims)
	token.Header["kid"] = constant.OfficialGatewayName
	privateKey, err := ParsePrivateKey(privateKeyText)
	if err != nil {
		return "", err
	}
	return token.SignedString(privateKey)
}
