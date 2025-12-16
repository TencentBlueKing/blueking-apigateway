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

var _ = Describe("RequestID", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("RequestID Middleware", func() {
		It("should use existing request ID from header", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			existingRequestID := "existing-request-id-12345"
			c.Request.Header.Set(constant.BkGatewayRequestIDKey, existingRequestID)

			mw := middleware.RequestID()
			mw(c)

			requestID := util.GetRequestIDFromContext(c.Request.Context())
			Expect(requestID).To(Equal(existingRequestID))
		})

		It("should generate new request ID when not provided", func() {
			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

			mw := middleware.RequestID()
			mw(c)

			requestID := util.GetRequestIDFromContext(c.Request.Context())
			Expect(requestID).NotTo(BeEmpty())
			// UUID4 hex format check (32 hex characters without dashes)
			Expect(requestID).To(HaveLen(32))
		})

		It("should generate unique request IDs for multiple requests", func() {
			requestIDs := make(map[string]bool)

			for i := 0; i < 10; i++ {
				w := httptest.NewRecorder()
				c, _ := gin.CreateTestContext(w)
				c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

				mw := middleware.RequestID()
				mw(c)

				requestID := util.GetRequestIDFromContext(c.Request.Context())
				Expect(requestID).NotTo(BeEmpty())
				Expect(requestIDs).NotTo(HaveKey(requestID), "Request ID should be unique")
				requestIDs[requestID] = true
			}
		})
	})
})
