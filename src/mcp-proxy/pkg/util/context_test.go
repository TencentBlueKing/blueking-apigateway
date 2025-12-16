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
	"net/http"
	"net/http/httptest"
	"time"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

var _ = Describe("Context", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("BkUsername", func() {
		It("should set and get username", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetBkUsername(c, "test-user")

			username, exists := c.Get(string(constant.BkUsername))
			Expect(exists).To(BeTrue())
			Expect(username).To(Equal("test-user"))

			usernameFromCtx := c.Request.Context().Value(constant.BkUsername)
			Expect(usernameFromCtx).To(Equal("test-user"))
		})
	})

	Describe("BkAppCode", func() {
		It("should set and get app code", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetBkAppCode(c, "test-app")

			appCode := util.GetBkAppCode(c)
			Expect(appCode).To(Equal("test-app"))

			appCodeFromCtx := c.Request.Context().Value(constant.BkAppCode)
			Expect(appCodeFromCtx).To(Equal("test-app"))
		})

		It("should return empty when not set", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			appCode := util.GetBkAppCode(c)
			Expect(appCode).To(BeEmpty())
		})
	})

	Describe("InnerJWTToken", func() {
		It("should set and get inner JWT token", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetInnerJWTToken(c, "test-jwt-token")

			token, exists := c.Get(string(constant.BkGatewayInnerJWT))
			Expect(exists).To(BeTrue())
			Expect(token).To(Equal("test-jwt-token"))

			tokenFromCtx := util.GetInnerJWTTokenFromContext(c.Request.Context())
			Expect(tokenFromCtx).To(Equal("test-jwt-token"))
		})

		It("should return empty when not set", func() {
			ctx := context.Background()
			token := util.GetInnerJWTTokenFromContext(ctx)
			Expect(token).To(BeEmpty())
		})
	})

	Describe("MCPServerID", func() {
		It("should set and get MCP server ID", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetMCPServerID(c, 123)

			serverID := util.GetMCPServerID(c)
			Expect(serverID).To(Equal(123))

			serverIDFromCtx := c.Request.Context().Value(constant.MCPServerID)
			Expect(serverIDFromCtx).To(Equal(123))
		})

		It("should return 0 when not set", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			serverID := util.GetMCPServerID(c)
			Expect(serverID).To(Equal(0))
		})
	})

	Describe("MCPServerName", func() {
		It("should set and get MCP server name", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetMCPServerName(c, "test-server")

			serverName := util.GetMCPServerName(c)
			Expect(serverName).To(Equal("test-server"))

			serverNameFromCtx := c.Request.Context().Value(constant.MCPServerName)
			Expect(serverNameFromCtx).To(Equal("test-server"))
		})

		It("should return empty when not set", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			serverName := util.GetMCPServerName(c)
			Expect(serverName).To(BeEmpty())
		})
	})

	Describe("GatewayID", func() {
		It("should set and get gateway ID", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetGatewayID(c, 456)

			gatewayID := util.GetGatewayID(c)
			Expect(gatewayID).To(Equal(456))

			gatewayIDFromCtx := c.Request.Context().Value(constant.GatewayID)
			Expect(gatewayIDFromCtx).To(Equal(456))
		})

		It("should return 0 when not set", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			gatewayID := util.GetGatewayID(c)
			Expect(gatewayID).To(Equal(0))
		})
	})

	Describe("BkApiTimeout", func() {
		It("should set and get timeout", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetBkApiTimeout(c, 30)

			timeout := util.GetBkApiTimeout(c.Request.Context())
			Expect(timeout).To(Equal(30 * time.Second))
		})

		It("should return default timeout when not set", func() {
			ctx := context.Background()
			timeout := util.GetBkApiTimeout(ctx)
			Expect(timeout).To(Equal(5 * time.Minute))
		})

		It("should return default timeout when zero", func() {
			ctx := context.WithValue(context.Background(), constant.BkApiTimeout, 0)
			timeout := util.GetBkApiTimeout(ctx)
			Expect(timeout).To(Equal(5 * time.Minute))
		})
	})

	Describe("BkApiAllowedHeaders", func() {
		It("should set and get allowed headers", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			c.Request.Header.Set("X-Custom-Header", "custom-value")
			c.Request.Header.Set("X-Another-Header", "another-value")

			util.SetMCPServerID(c, 1)
			util.SetMCPServerName(c, "test-server")

			util.SetBkApiAllowedHeaders(c, "X-Custom-Header,X-Another-Header")

			headers := util.GetBkApiAllowedHeaders(c.Request.Context())
			Expect(headers).NotTo(BeNil())
			Expect(headers["X-Custom-Header"]).To(Equal("custom-value"))
			Expect(headers["X-Another-Header"]).To(Equal("another-value"))
			Expect(headers[constant.BkApiMCPServerIDKey]).To(Equal("1"))
			Expect(headers[constant.BkApiMCPServerNameKey]).To(Equal("test-server"))
		})

		It("should handle empty string", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetMCPServerID(c, 1)
			util.SetMCPServerName(c, "test-server")

			util.SetBkApiAllowedHeaders(c, "")

			headers := util.GetBkApiAllowedHeaders(c.Request.Context())
			Expect(headers).NotTo(BeNil())
			Expect(headers[constant.BkApiMCPServerIDKey]).To(Equal("1"))
			Expect(headers[constant.BkApiMCPServerNameKey]).To(Equal("test-server"))
		})

		It("should return empty map when not set", func() {
			ctx := context.Background()
			headers := util.GetBkApiAllowedHeaders(ctx)
			Expect(headers).NotTo(BeNil())
			Expect(headers).To(BeEmpty())
		})

		It("should handle headers with spaces", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			c.Request.Header.Set("X-Header-1", "value1")
			c.Request.Header.Set("X-Header-2", "value2")

			util.SetMCPServerID(c, 1)
			util.SetMCPServerName(c, "test-server")

			util.SetBkApiAllowedHeaders(c, " X-Header-1 , X-Header-2 ")

			headers := util.GetBkApiAllowedHeaders(c.Request.Context())
			Expect(headers).NotTo(BeNil())
			Expect(headers["X-Header-1"]).To(Equal("value1"))
			Expect(headers["X-Header-2"]).To(Equal("value2"))
		})
	})
})
