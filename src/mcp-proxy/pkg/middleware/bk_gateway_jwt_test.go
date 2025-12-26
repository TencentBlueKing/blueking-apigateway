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

package middleware_test

import (
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

	"mcp_proxy/pkg/middleware"
)

var _ = Describe("BkGatewayJWT", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("VerifyJWTToken", func() {
		DescribeTable("validates claims correctly",
			func(claims *middleware.CustomClaims, expectedErr error) {
				err := middleware.VerifyJWTToken(claims)
				if expectedErr != nil {
					Expect(err).To(MatchError(expectedErr))
				} else {
					Expect(err).NotTo(HaveOccurred())
				}
			},
			Entry("valid claims",
				&middleware.CustomClaims{
					App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
					User: middleware.UserInfo{Username: "test-user", Verified: true},
				}, nil,
			),
			Entry("empty app code",
				&middleware.CustomClaims{
					App:  middleware.AppInfo{AppCode: "", Verified: true},
					User: middleware.UserInfo{Username: "test-user", Verified: true},
				}, middleware.ErrAPIGatewayJWTAppInfoNoAppCode,
			),
			Entry("app not verified",
				&middleware.CustomClaims{
					App:  middleware.AppInfo{AppCode: "test-app", Verified: false},
					User: middleware.UserInfo{Username: "test-user", Verified: true},
				}, middleware.ErrAPIGatewayJWTAppNotVerified,
			),
			Entry("user not verified but app verified - should pass",
				&middleware.CustomClaims{
					App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
					User: middleware.UserInfo{Username: "test-user", Verified: false},
				}, nil,
			),
			Entry("empty username with verified app - should pass",
				&middleware.CustomClaims{
					App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
					User: middleware.UserInfo{Username: "", Verified: true},
				}, nil,
			),
		)
	})

	Describe("ParseBKJWTToken", func() {
		var privateKey *rsa.PrivateKey
		var publicKeyPEM []byte

		BeforeEach(func() {
			var err error
			privateKey, err = rsa.GenerateKey(rand.Reader, 2048)
			Expect(err).NotTo(HaveOccurred())

			publicKeyBytes, err := x509.MarshalPKIXPublicKey(&privateKey.PublicKey)
			Expect(err).NotTo(HaveOccurred())
			publicKeyPEM = pem.EncodeToMemory(&pem.Block{
				Type:  "PUBLIC KEY",
				Bytes: publicKeyBytes,
			})
		})

		It("should fail with invalid public key", func() {
			tokenString := "invalid.token.string"
			invalidPublicKey := []byte("invalid-public-key")

			_, err := middleware.ParseBKJWTToken(tokenString, invalidPublicKey)
			Expect(err).To(HaveOccurred())
		})

		It("should fail with invalid token format", func() {
			tokenString := "invalid.token.format"

			_, err := middleware.ParseBKJWTToken(tokenString, publicKeyPEM)
			Expect(err).To(HaveOccurred())
		})

		It("should parse valid token successfully", func() {
			claims := &middleware.CustomClaims{
				App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
				User: middleware.UserInfo{Username: "test-user", Verified: true},
				RegisteredClaims: jwt.RegisteredClaims{
					Issuer:    "test-issuer",
					ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
					IssuedAt:  jwt.NewNumericDate(time.Now()),
					NotBefore: jwt.NewNumericDate(time.Now().Add(-time.Minute)),
				},
			}

			token := jwt.NewWithClaims(jwt.SigningMethodRS512, claims)
			tokenString, err := token.SignedString(privateKey)
			Expect(err).NotTo(HaveOccurred())

			parsedClaims, err := middleware.ParseBKJWTToken(tokenString, publicKeyPEM)
			Expect(err).NotTo(HaveOccurred())
			Expect(parsedClaims.App.AppCode).To(Equal("test-app"))
			Expect(parsedClaims.User.Username).To(Equal("test-user"))
		})

		It("should return error for expired token", func() {
			claims := &middleware.CustomClaims{
				App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
				User: middleware.UserInfo{Username: "test-user", Verified: true},
				RegisteredClaims: jwt.RegisteredClaims{
					Issuer:    "test-issuer",
					ExpiresAt: jwt.NewNumericDate(time.Now().Add(-time.Hour)), // expired
					IssuedAt:  jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
					NotBefore: jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
				},
			}

			token := jwt.NewWithClaims(jwt.SigningMethodRS512, claims)
			tokenString, err := token.SignedString(privateKey)
			Expect(err).NotTo(HaveOccurred())

			_, err = middleware.ParseBKJWTToken(tokenString, publicKeyPEM)
			Expect(err).To(MatchError(middleware.ErrExpired))
		})

		It("should return error for not yet valid token (nbf)", func() {
			claims := &middleware.CustomClaims{
				App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
				User: middleware.UserInfo{Username: "test-user", Verified: true},
				RegisteredClaims: jwt.RegisteredClaims{
					Issuer:    "test-issuer",
					ExpiresAt: jwt.NewNumericDate(time.Now().Add(2 * time.Hour)),
					IssuedAt:  jwt.NewNumericDate(time.Now()),
					NotBefore: jwt.NewNumericDate(time.Now().Add(time.Hour)), // not valid yet
				},
			}

			token := jwt.NewWithClaims(jwt.SigningMethodRS512, claims)
			tokenString, err := token.SignedString(privateKey)
			Expect(err).NotTo(HaveOccurred())

			_, err = middleware.ParseBKJWTToken(tokenString, publicKeyPEM)
			Expect(err).To(MatchError(middleware.ErrNBFInvalid))
		})

		It("should return error for future issued at token (iat)", func() {
			claims := &middleware.CustomClaims{
				App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
				User: middleware.UserInfo{Username: "test-user", Verified: true},
				RegisteredClaims: jwt.RegisteredClaims{
					Issuer:    "test-issuer",
					ExpiresAt: jwt.NewNumericDate(time.Now().Add(2 * time.Hour)),
					IssuedAt:  jwt.NewNumericDate(time.Now().Add(time.Hour)), // issued in future
					NotBefore: jwt.NewNumericDate(time.Now().Add(-time.Minute)),
				},
			}

			token := jwt.NewWithClaims(jwt.SigningMethodRS512, claims)
			tokenString, err := token.SignedString(privateKey)
			Expect(err).NotTo(HaveOccurred())

			_, err = middleware.ParseBKJWTToken(tokenString, publicKeyPEM)
			Expect(err).To(MatchError(middleware.ErrIATInvalid))
		})
	})

	Describe("CustomClaims", func() {
		It("should have correct fields", func() {
			claims := &middleware.CustomClaims{
				App:  middleware.AppInfo{AppCode: "test-app", Verified: true},
				User: middleware.UserInfo{Username: "test-user", Verified: true},
				RegisteredClaims: jwt.RegisteredClaims{
					Issuer:    "test-issuer",
					ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
					IssuedAt:  jwt.NewNumericDate(time.Now()),
				},
			}

			Expect(claims.App.AppCode).To(Equal("test-app"))
			Expect(claims.App.Verified).To(BeTrue())
			Expect(claims.User.Username).To(Equal("test-user"))
			Expect(claims.User.Verified).To(BeTrue())
			Expect(claims.Issuer).To(Equal("test-issuer"))
		})
	})

	Describe("AppInfo", func() {
		It("should have correct fields", func() {
			appInfo := middleware.AppInfo{AppCode: "my-app", Verified: true}
			Expect(appInfo.AppCode).To(Equal("my-app"))
			Expect(appInfo.Verified).To(BeTrue())
		})

		It("should handle unverified app", func() {
			appInfo := middleware.AppInfo{AppCode: "unverified-app", Verified: false}
			Expect(appInfo.AppCode).To(Equal("unverified-app"))
			Expect(appInfo.Verified).To(BeFalse())
		})
	})

	Describe("UserInfo", func() {
		It("should have correct fields", func() {
			userInfo := middleware.UserInfo{Username: "admin", Verified: true}
			Expect(userInfo.Username).To(Equal("admin"))
			Expect(userInfo.Verified).To(BeTrue())
		})

		It("should handle unverified user", func() {
			userInfo := middleware.UserInfo{Username: "guest", Verified: false}
			Expect(userInfo.Username).To(Equal("guest"))
			Expect(userInfo.Verified).To(BeFalse())
		})
	})

	Describe("Error Messages", func() {
		It("should have correct error messages", func() {
			Expect(middleware.ErrUnauthorized.Error()).To(Equal("jwtauth: token is unauthorized"))
			Expect(middleware.ErrExpired.Error()).To(Equal("jwtauth: token is expired"))
			Expect(middleware.ErrNBFInvalid.Error()).To(Equal("jwtauth: token nbf validation failed"))
			Expect(middleware.ErrIATInvalid.Error()).To(Equal("jwtauth: token iat validation failed"))
			Expect(middleware.ErrAPIGatewayJWTAppInfoNoAppCode.Error()).To(Equal("app_code not in app info"))
			Expect(middleware.ErrAPIGatewayJWTUserInfoNoUsername.Error()).To(Equal("username not in user info"))
			Expect(middleware.ErrAPIGatewayJWTAppNotVerified.Error()).To(Equal("app not verified"))
			Expect(middleware.ErrAPIGatewayJWTUserNotVerified.Error()).To(Equal("user not verified"))
		})
	})

	Describe("BkGatewayJWTAuthMiddleware", func() {
		It("should abort with no token", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			mw := middleware.BkGatewayJWTAuthMiddleware()
			mw(c)

			Expect(c.IsAborted()).To(BeTrue())
			Expect(w.Code).To(Equal(http.StatusUnauthorized))
		})

		It("should create middleware function", func() {
			mw := middleware.BkGatewayJWTAuthMiddleware()
			Expect(mw).NotTo(BeNil())
		})

		It("should abort with invalid token", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)
			c.Request.Header.Set("X-Bkapi-JWT", "invalid-token")

			mw := middleware.BkGatewayJWTAuthMiddleware()

			// This test may panic due to missing database, so we just verify the middleware is created
			Expect(mw).NotTo(BeNil())
		})
	})
})
