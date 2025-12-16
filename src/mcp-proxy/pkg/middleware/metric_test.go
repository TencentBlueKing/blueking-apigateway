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

	"mcp_proxy/pkg/middleware"
	"mcp_proxy/pkg/util"
)

var _ = Describe("Metric", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("Metrics Middleware", func() {
		It("should handle requests successfully", func() {
			r := gin.Default()
			r.Use(middleware.Metrics())
			util.NewTestRouter(r)

			req, _ := http.NewRequest("GET", "/ping", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(200))
		})

		It("should track POST requests", func() {
			r := gin.Default()
			r.Use(middleware.Metrics())
			r.POST("/api/test", func(c *gin.Context) {
				c.String(http.StatusCreated, "created")
			})

			req, _ := http.NewRequest("POST", "/api/test", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusCreated))
		})

		It("should track requests with path parameters", func() {
			r := gin.Default()
			r.Use(middleware.Metrics())
			r.GET("/mcp/:name/sse", func(c *gin.Context) {
				c.String(http.StatusOK, "ok")
			})

			req, _ := http.NewRequest("GET", "/mcp/test-server/sse", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusOK))
		})

		It("should track error responses", func() {
			r := gin.Default()
			r.Use(middleware.Metrics())
			r.GET("/error", func(c *gin.Context) {
				c.String(http.StatusInternalServerError, "error")
			})

			req, _ := http.NewRequest("GET", "/error", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusInternalServerError))
		})

		It("should track 404 responses", func() {
			r := gin.Default()
			r.Use(middleware.Metrics())

			req, _ := http.NewRequest("GET", "/not-found", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusNotFound))
		})
	})
})
