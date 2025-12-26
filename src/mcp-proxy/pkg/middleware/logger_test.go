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
	"bytes"
	"net/http"
	"net/http/httptest"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/middleware"
	"mcp_proxy/pkg/util"
)

var _ = Describe("Logger", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
		logging.InitLogger(&config.Config{})
	})

	Describe("APILogger", func() {
		It("should log GET requests", func() {
			r := gin.Default()
			r.Use(middleware.APILogger())
			util.NewTestRouter(r)

			req, _ := http.NewRequest("GET", "/ping", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(200))
		})

		It("should log POST requests with body", func() {
			r := gin.New()
			r.Use(middleware.APILogger())
			r.POST("/test", func(c *gin.Context) {
				c.String(http.StatusOK, "ok")
			})

			body := bytes.NewBufferString(`{"key": "value"}`)
			req, _ := http.NewRequest("POST", "/test", body)
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(200))
		})

		It("should log requests with query params", func() {
			r := gin.New()
			r.Use(middleware.APILogger())
			r.GET("/test", func(c *gin.Context) {
				c.String(http.StatusOK, "ok")
			})

			req, _ := http.NewRequest("GET", "/test?param1=value1&param2=value2", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(200))
		})

		It("should log requests with context values", func() {
			r := gin.New()
			r.Use(func(c *gin.Context) {
				util.SetGatewayID(c, 123)
				util.SetMCPServerID(c, 456)
				util.SetMCPServerName(c, "test-server")
				c.Next()
			})
			r.Use(middleware.APILogger())
			r.GET("/test", func(c *gin.Context) {
				c.String(http.StatusOK, "ok")
			})

			req, _ := http.NewRequest("GET", "/test", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(200))
		})

		It("should log error responses", func() {
			r := gin.New()
			r.Use(middleware.APILogger())
			r.GET("/error", func(c *gin.Context) {
				c.String(http.StatusInternalServerError, "error")
			})

			req, _ := http.NewRequest("GET", "/error", nil)
			w := httptest.NewRecorder()

			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(500))
		})

		It("should create middleware function", func() {
			mw := middleware.APILogger()
			Expect(mw).NotTo(BeNil())
		})
	})
})
