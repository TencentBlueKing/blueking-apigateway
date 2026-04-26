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
	"net/http"
	"net/http/httptest"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/middleware"
	"mcp_proxy/pkg/util"
)

var _ = Describe("MCPHeader", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("MCPServerHeaderMiddleware", func() {
		DescribeTable("handles timeout header correctly",
			func(timeout string, allowedHeaders string, expectedTimeoutSeconds int) {
				w := httptest.NewRecorder()
				c, _ := gin.CreateTestContext(w)
				c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

				if timeout != "" {
					c.Request.Header.Set(constant.BkApiTimeoutHeaderKey, timeout)
				}
				if allowedHeaders != "" {
					c.Request.Header.Set(constant.BkApiAllowedHeadersKey, allowedHeaders)
				}

				mw := middleware.MCPServerHeaderMiddleware()
				mw(c)

				actualTimeout := util.GetBkApiTimeout(c.Request.Context())
				if expectedTimeoutSeconds == 0 {
					// Default timeout is 5 minutes
					Expect(int(actualTimeout.Seconds())).To(Equal(5 * 60))
				} else {
					Expect(int(actualTimeout.Seconds())).To(Equal(expectedTimeoutSeconds))
				}
			},
			Entry("with timeout header", "30", "", 30),
			Entry("without timeout header", "", "", 0),
			Entry("with allowed headers", "60", "X-Custom-Header,X-Another-Header", 60),
			Entry("invalid timeout value", "invalid", "", 0),
		)

		It("should extract allowed headers", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			c.Request.Header.Set(constant.BkApiAllowedHeadersKey, "X-Custom-Header,X-Another-Header")
			c.Request.Header.Set("X-Custom-Header", "custom-value")
			c.Request.Header.Set("X-Another-Header", "another-value")

			util.SetMCPServerID(c, 1)
			util.SetMCPServerName(c, "test-server")

			mw := middleware.MCPServerHeaderMiddleware()
			mw(c)

			headers := util.GetBkApiAllowedHeaders(c.Request.Context())
			Expect(headers).NotTo(BeNil())
			Expect(headers["X-Custom-Header"]).To(Equal("custom-value"))
			Expect(headers["X-Another-Header"]).To(Equal("another-value"))
		})

		It("should parse X-Bkapi-ItsmFlex header", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			itsmFlexJSON := `{"agent.info.code":"ai-test-appcode","agent.info.name":"AgentName","agent.session.caller_executor":"judge-caller","agent.session.executor":"judge-executor"}`
			c.Request.Header.Set(constant.BkApiItsmFlexKey, itsmFlexJSON)

			mw := middleware.MCPServerHeaderMiddleware()
			mw(c)

			data := util.GetBkApiItsmFlexData(c.Request.Context())
			Expect(data).NotTo(BeNil())
			Expect(data.AgentCode).To(Equal("ai-test-appcode"))
			Expect(data.AgentName).To(Equal("AgentName"))
			Expect(data.CallerExecutor).To(Equal("judge-caller"))
			Expect(data.Executor).To(Equal("judge-executor"))
		})

		It("should ignore invalid X-Bkapi-ItsmFlex header", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			c.Request.Header.Set(constant.BkApiItsmFlexKey, "not-json")

			mw := middleware.MCPServerHeaderMiddleware()
			mw(c)

			data := util.GetBkApiItsmFlexData(c.Request.Context())
			Expect(data).To(BeNil())
		})

		It("should handle missing X-Bkapi-ItsmFlex header", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			mw := middleware.MCPServerHeaderMiddleware()
			mw(c)

			data := util.GetBkApiItsmFlexData(c.Request.Context())
			Expect(data).To(BeNil())
		})
	})
})
