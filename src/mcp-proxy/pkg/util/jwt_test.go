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

package util_test

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"net/http"
	"net/http/httptest"
	"time"

	"github.com/gin-gonic/gin"
	jwt "github.com/golang-jwt/jwt/v4"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

var _ = Describe("JWT", func() {
	var privateKey *rsa.PrivateKey
	var privateKeyPEM []byte

	BeforeEach(func() {
		gin.SetMode(gin.TestMode)

		config.G = &config.Config{
			McpServer: config.McpServer{
				InnerJwtExpireTime: 5 * time.Minute,
			},
		}

		var err error
		privateKey, err = rsa.GenerateKey(rand.Reader, 2048)
		Expect(err).NotTo(HaveOccurred())

		privateKeyBytes := x509.MarshalPKCS1PrivateKey(privateKey)
		privateKeyPEM = pem.EncodeToMemory(&pem.Block{
			Type:  "RSA PRIVATE KEY",
			Bytes: privateKeyBytes,
		})
	})

	Describe("SignInnerJWT", func() {
		It("should sign token successfully with valid claims and private key", func() {
			claims := &util.JWTClaimsForLazySigning{
				AppCode:      "test-app",
				AppVerified:  true,
				Username:     "test-user",
				UserVerified: true,
				Issuer:       "test-issuer",
				Audience:     []string{"test-audience"},
			}

			tokenString, err := util.SignInnerJWT(claims, privateKeyPEM, 123)
			Expect(err).NotTo(HaveOccurred())
			Expect(tokenString).NotTo(BeEmpty())

			// 验证签发的 token 可以被解析
			parsedToken, err := jwt.ParseWithClaims(
				tokenString,
				&util.InnerJWTClaims{},
				func(token *jwt.Token) (interface{}, error) {
					return &privateKey.PublicKey, nil
				},
			)
			Expect(err).NotTo(HaveOccurred())
			Expect(parsedToken.Valid).To(BeTrue())

			// 验证 claims 内容
			parsedClaims, ok := parsedToken.Claims.(*util.InnerJWTClaims)
			Expect(ok).To(BeTrue())
			Expect(parsedClaims.App.AppCode).To(ContainSubstring("test-app"))
			Expect(parsedClaims.App.Verified).To(BeTrue())
			Expect(parsedClaims.User.Username).To(Equal("test-user"))
			Expect(parsedClaims.User.Verified).To(BeTrue())
			Expect(parsedClaims.Issuer).To(Equal("test-issuer"))
		})

		It("should fail with invalid private key", func() {
			claims := &util.JWTClaimsForLazySigning{
				AppCode:      "test-app",
				AppVerified:  true,
				Username:     "test-user",
				UserVerified: true,
				Issuer:       "test-issuer",
				Audience:     []string{"test-audience"},
			}

			invalidPrivateKey := []byte("invalid-private-key")

			_, err := util.SignInnerJWT(claims, invalidPrivateKey, 123)
			Expect(err).To(HaveOccurred())
		})

		It("should include mcp_server_id in app_code", func() {
			claims := &util.JWTClaimsForLazySigning{
				AppCode:      "my-app",
				AppVerified:  true,
				Username:     "user1",
				UserVerified: true,
				Issuer:       "issuer",
				Audience:     []string{"aud"},
			}

			tokenString, err := util.SignInnerJWT(claims, privateKeyPEM, 456)
			Expect(err).NotTo(HaveOccurred())

			parsedToken, err := jwt.ParseWithClaims(
				tokenString,
				&util.InnerJWTClaims{},
				func(token *jwt.Token) (interface{}, error) {
					return &privateKey.PublicKey, nil
				},
			)
			Expect(err).NotTo(HaveOccurred())

			parsedClaims := parsedToken.Claims.(*util.InnerJWTClaims)
			// app_code 格式应该包含 mcp_server_id
			Expect(parsedClaims.App.AppCode).To(ContainSubstring("456"))
			Expect(parsedClaims.App.AppCode).To(ContainSubstring("my-app"))
		})

		It("should set correct token header kid", func() {
			claims := &util.JWTClaimsForLazySigning{
				AppCode:      "test-app",
				AppVerified:  true,
				Username:     "test-user",
				UserVerified: true,
				Issuer:       "test-issuer",
				Audience:     []string{"test-audience"},
			}

			tokenString, err := util.SignInnerJWT(claims, privateKeyPEM, 123)
			Expect(err).NotTo(HaveOccurred())

			parsedToken, _ := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
				return &privateKey.PublicKey, nil
			})

			// 验证 header 中的 kid
			kid, ok := parsedToken.Header["kid"].(string)
			Expect(ok).To(BeTrue())
			Expect(kid).To(Equal(constant.OfficialGatewayName))
		})
	})

	Describe("SignInnerJWTFromContext", func() {
		It("should sign token from context successfully", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			// 设置 mcp_server_id
			util.SetMCPServerID(c, 789)

			// 设置 claims 和私钥到 context
			claims := &util.JWTClaimsForLazySigning{
				AppCode:      "context-app",
				AppVerified:  true,
				Username:     "context-user",
				UserVerified: true,
				Issuer:       "context-issuer",
				Audience:     []string{"context-audience"},
			}
			util.SetJWTClaimsForLazySigning(c, claims, privateKeyPEM)

			// 从 context 签发 JWT
			tokenString, err := util.SignInnerJWTFromContext(c.Request.Context())
			Expect(err).NotTo(HaveOccurred())
			Expect(tokenString).NotTo(BeEmpty())

			// 验证签发的 token
			parsedToken, err := jwt.ParseWithClaims(
				tokenString,
				&util.InnerJWTClaims{},
				func(token *jwt.Token) (interface{}, error) {
					return &privateKey.PublicKey, nil
				},
			)
			Expect(err).NotTo(HaveOccurred())

			parsedClaims := parsedToken.Claims.(*util.InnerJWTClaims)
			Expect(parsedClaims.App.AppCode).To(ContainSubstring("context-app"))
			Expect(parsedClaims.User.Username).To(Equal("context-user"))
		})

		It("should fail when claims not in context", func() {
			ctx := context.Background()

			_, err := util.SignInnerJWTFromContext(ctx)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("jwt claims not found"))
		})

		It("should fail when private key not in context", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			// 只设置 claims，不设置私钥
			claims := &util.JWTClaimsForLazySigning{
				AppCode:      "test-app",
				AppVerified:  true,
				Username:     "test-user",
				UserVerified: true,
				Issuer:       "test-issuer",
				Audience:     []string{"test-audience"},
			}
			ctx := context.WithValue(c.Request.Context(), constant.BkGatewayJWTClaims, claims)
			c.Request = c.Request.WithContext(ctx)

			_, err := util.SignInnerJWTFromContext(c.Request.Context())
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("private key not found"))
		})
	})

	Describe("InnerJWTClaims", func() {
		It("should have correct structure", func() {
			claims := util.InnerJWTClaims{
				App: util.InnerAppInfo{
					AppCode:  "app-code",
					Verified: true,
				},
				User: util.InnerUserInfo{
					Username: "username",
					Verified: true,
				},
				RegisteredClaims: jwt.RegisteredClaims{
					Issuer:    "issuer",
					Audience:  jwt.ClaimStrings{"aud1", "aud2"},
					ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
				},
			}

			Expect(claims.App.AppCode).To(Equal("app-code"))
			Expect(claims.App.Verified).To(BeTrue())
			Expect(claims.User.Username).To(Equal("username"))
			Expect(claims.User.Verified).To(BeTrue())
			Expect(claims.Issuer).To(Equal("issuer"))
			Expect(claims.Audience).To(HaveLen(2))
		})
	})

	Describe("InnerAppInfo", func() {
		It("should have correct fields", func() {
			appInfo := util.InnerAppInfo{AppCode: "my-app", Verified: true}
			Expect(appInfo.AppCode).To(Equal("my-app"))
			Expect(appInfo.Verified).To(BeTrue())
		})

		It("should handle unverified app", func() {
			appInfo := util.InnerAppInfo{AppCode: "unverified-app", Verified: false}
			Expect(appInfo.AppCode).To(Equal("unverified-app"))
			Expect(appInfo.Verified).To(BeFalse())
		})
	})

	Describe("InnerUserInfo", func() {
		It("should have correct fields", func() {
			userInfo := util.InnerUserInfo{Username: "admin", Verified: true}
			Expect(userInfo.Username).To(Equal("admin"))
			Expect(userInfo.Verified).To(BeTrue())
		})

		It("should handle unverified user", func() {
			userInfo := util.InnerUserInfo{Username: "guest", Verified: false}
			Expect(userInfo.Username).To(Equal("guest"))
			Expect(userInfo.Verified).To(BeFalse())
		})
	})
})
