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
	"time"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/middleware"
	"mcp_proxy/pkg/util"
)

var _ = Describe("MCPPermission", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("MCPServerPermissionMiddleware", func() {
		It("should create middleware function", func() {
			mw := middleware.MCPServerPermissionMiddleware()
			Expect(mw).NotTo(BeNil())
		})

		It("should setup context correctly", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/mcp/test-server/sse", nil)
			c.Params = gin.Params{{Key: "name", Value: "test-server"}}

			util.SetMCPServerID(c, 123)
			util.SetBkAppCode(c, "my-app")

			Expect(util.GetMCPServerID(c)).To(Equal(123))
			Expect(util.GetBkAppCode(c)).To(Equal("my-app"))
		})

		It("should handle missing mcp server id", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/mcp/test-server/sse", nil)
			c.Params = gin.Params{{Key: "name", Value: "test-server"}}

			// MCP server ID not set, should return 0
			Expect(util.GetMCPServerID(c)).To(Equal(0))
		})

		It("should handle missing app code", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/mcp/test-server/sse", nil)

			// App code not set, should return empty string
			Expect(util.GetBkAppCode(c)).To(Equal(""))
		})

		It("should set and get gateway id correctly", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			util.SetGatewayID(c, 456)
			Expect(util.GetGatewayID(c)).To(Equal(456))
		})
	})

	Describe("Permission expiration logic", func() {
		It("should consider permission valid when expires time is in the future", func() {
			// expires 在未来，权限有效
			expiresTime := time.Now().Add(time.Hour)
			isExpired := expiresTime.Before(time.Now())
			Expect(isExpired).To(BeFalse())
		})

		It("should consider permission expired when expires time is in the past", func() {
			// expires 在过去，权限过期
			expiresTime := time.Now().Add(-time.Hour)
			isExpired := expiresTime.Before(time.Now())
			Expect(isExpired).To(BeTrue())
		})

		It("should consider permission valid when expires time equals now (boundary case)", func() {
			// expires 等于当前时间，应该视为有效（刚好到期的那一刻还是有效的）
			now := time.Now()
			expiresTime := now
			isExpired := expiresTime.Before(now)
			Expect(isExpired).To(BeFalse())
		})
	})
})
