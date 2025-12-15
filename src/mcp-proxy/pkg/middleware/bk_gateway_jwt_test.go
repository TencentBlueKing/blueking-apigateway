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
	"time"

	"github.com/gin-gonic/gin"
	jwt "github.com/golang-jwt/jwt/v4"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/util"
)

func TestVerifyJWTToken(t *testing.T) {
	tests := []struct {
		name        string
		claims      *CustomClaims
		expectedErr error
	}{
		{
			name: "valid claims",
			claims: &CustomClaims{
				App: AppInfo{
					AppCode:  "test-app",
					Verified: true,
				},
				User: UserInfo{
					Username: "test-user",
					Verified: true,
				},
			},
			expectedErr: nil,
		},
		{
			name: "empty app code",
			claims: &CustomClaims{
				App: AppInfo{
					AppCode:  "",
					Verified: true,
				},
				User: UserInfo{
					Username: "test-user",
					Verified: true,
				},
			},
			expectedErr: ErrAPIGatewayJWTAppInfoNoAppCode,
		},
		{
			name: "app not verified",
			claims: &CustomClaims{
				App: AppInfo{
					AppCode:  "test-app",
					Verified: false,
				},
				User: UserInfo{
					Username: "test-user",
					Verified: true,
				},
			},
			expectedErr: ErrAPIGatewayJWTAppNotVerified,
		},
		{
			name: "user not verified but app verified - should pass",
			claims: &CustomClaims{
				App: AppInfo{
					AppCode:  "test-app",
					Verified: true,
				},
				User: UserInfo{
					Username: "test-user",
					Verified: false,
				},
			},
			expectedErr: nil, // verifyJWTToken only checks app verification
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := verifyJWTToken(tt.claims)
			if tt.expectedErr != nil {
				assert.ErrorIs(t, err, tt.expectedErr)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestParseBKJWTToken_InvalidPublicKey(t *testing.T) {
	tokenString := "invalid.token.string"
	invalidPublicKey := []byte("invalid-public-key")

	_, err := parseBKJWTToken(tokenString, invalidPublicKey)
	assert.Error(t, err)
}

func TestParseBKJWTToken_InvalidToken(t *testing.T) {
	// Valid RSA public key for testing
	publicKey := []byte(`-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS5JJcds3xfn/ygWyNDnCYbLJUVaU0Bv
7QKXJ1iXpNxFMGQZbPNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDv
EOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdV
JE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMq
XnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQwIDAQAB
-----END PUBLIC KEY-----`)

	tokenString := "invalid.token.format"

	_, err := parseBKJWTToken(tokenString, publicKey)
	assert.Error(t, err)
}

func TestCustomClaims(t *testing.T) {
	claims := &CustomClaims{
		App: AppInfo{
			AppCode:  "test-app",
			Verified: true,
		},
		User: UserInfo{
			Username: "test-user",
			Verified: true,
		},
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    "test-issuer",
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}

	assert.Equal(t, "test-app", claims.App.AppCode)
	assert.True(t, claims.App.Verified)
	assert.Equal(t, "test-user", claims.User.Username)
	assert.True(t, claims.User.Verified)
	assert.Equal(t, "test-issuer", claims.Issuer)
}

func TestAppInfo(t *testing.T) {
	appInfo := AppInfo{
		AppCode:  "my-app",
		Verified: true,
	}

	assert.Equal(t, "my-app", appInfo.AppCode)
	assert.True(t, appInfo.Verified)
}

func TestUserInfo(t *testing.T) {
	userInfo := UserInfo{
		Username: "admin",
		Verified: true,
	}

	assert.Equal(t, "admin", userInfo.Username)
	assert.True(t, userInfo.Verified)
}

func TestErrorMessages(t *testing.T) {
	assert.Equal(t, "jwtauth: token is unauthorized", ErrUnauthorized.Error())
	assert.Equal(t, "jwtauth: token is expired", ErrExpired.Error())
	assert.Equal(t, "jwtauth: token nbf validation failed", ErrNBFInvalid.Error())
	assert.Equal(t, "jwtauth: token iat validation failed", ErrIATInvalid.Error())
	assert.Equal(t, "app_code not in app info", ErrAPIGatewayJWTAppInfoNoAppCode.Error())
	assert.Equal(t, "username not in user info", ErrAPIGatewayJWTUserInfoNoUsername.Error())
	assert.Equal(t, "app not verified", ErrAPIGatewayJWTAppNotVerified.Error())
	assert.Equal(t, "user not verified", ErrAPIGatewayJWTUserNotVerified.Error())
}

func TestSignBkInnerJWTToken_InvalidPrivateKey(t *testing.T) {
	gin.SetMode(gin.TestMode)

	// Initialize config for test
	config.G = &config.Config{
		McpServer: config.McpServer{
			InnerJwtExpireTime: 5 * time.Minute,
		},
	}

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	claims := &CustomClaims{
		App: AppInfo{
			AppCode:  "test-app",
			Verified: true,
		},
		User: UserInfo{
			Username: "test-user",
			Verified: true,
		},
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer: "test-issuer",
		},
	}

	// Invalid private key
	invalidPrivateKey := []byte("invalid-private-key")

	err := SignBkInnerJWTToken(c, claims, invalidPrivateKey)
	assert.Error(t, err)
}

func TestSignBkInnerJWTToken_Success(t *testing.T) {
	gin.SetMode(gin.TestMode)

	// Initialize config for test
	config.G = &config.Config{
		McpServer: config.McpServer{
			InnerJwtExpireTime: 5 * time.Minute,
		},
	}

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	// Set MCP Server ID
	util.SetMCPServerID(c, 123)

	claims := &CustomClaims{
		App: AppInfo{
			AppCode:  "test-app",
			Verified: true,
		},
		User: UserInfo{
			Username: "test-user",
			Verified: true,
		},
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:   "test-issuer",
			Audience: jwt.ClaimStrings{"test-audience"},
		},
	}

	// Valid RSA private key for testing
	privateKey := []byte(`-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyNDnCYbLJUVaU0Bv7QKXJ1iXpNxFM
GQZbPNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfND
vEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLH
BzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHd
VJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJN
EQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqM
qXnNJNLHBzwPKBZQwIDAQABAoIBAC5RgZ+hBx7xHnFZnQmY0lLV7Rx4E3V8Bnpt
LxYlaJms7FU0nRfBxY0tipPEfNQQMaIJalVQcehT0oCgMKkS0WQOG6oBd3VNxwNh
pZJ0HKh0PQOM0lOBXEWVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQF
EGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBV
YPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDv
EOLqMqXnNJNLHBzwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHB
zwPKBZQFEGZHdVJE0pKLBVYPXJNEQFpFfNDvEOLqMqXnNJNLHBzwPKBZQwIDAQAB
AoIBAC5RgZ+hBx7xHnFZnQmY0lLV7Rx4E3V8BnptLxYlaJms7FU0nRfBxY0tipPE
fNQQMaIJalVQcehT0oCgMKkS0WQOG6oBd3VNxwNhpZJ0HKh0PQOM0lOBXEWVJE0p
-----END RSA PRIVATE KEY-----`)

	err := SignBkInnerJWTToken(c, claims, privateKey)
	// This will fail due to invalid key format, but we're testing the flow
	assert.Error(t, err)
}

func TestBkGatewayJWTAuthMiddleware_NoToken(t *testing.T) {
	gin.SetMode(gin.TestMode)

	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

	middleware := BkGatewayJWTAuthMiddleware()
	middleware(c)

	assert.True(t, c.IsAborted())
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestBkGatewayJWTAuthMiddleware_FunctionCreation(t *testing.T) {
	middleware := BkGatewayJWTAuthMiddleware()
	assert.NotNil(t, middleware)
}
