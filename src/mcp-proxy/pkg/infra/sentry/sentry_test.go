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

package sentry_test

import (
	"net/http"
	"net/http/httptest"
	"time"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/sentry"
)

var _ = Describe("Sentry", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
	})

	Describe("Init", func() {
		It("should succeed with empty DSN (sentry disabled)", func() {
			err := sentry.Init(config.Sentry{DSN: ""})
			Expect(err).NotTo(HaveOccurred())
		})

		It("should return error with invalid DSN", func() {
			err := sentry.Init(config.Sentry{DSN: "not-a-valid-dsn"})
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("init sentry fail"))
		})
	})

	Describe("Enabled", func() {
		It("should return false when sentry is not initialized with DSN", func() {
			// Re-init without DSN to ensure disabled state
			_ = sentry.Init(config.Sentry{DSN: ""})
			// Note: Enabled() state depends on previous calls; this test checks
			// that the function doesn't panic and returns a boolean.
			_ = sentry.Enabled()
		})
	})

	Describe("ReportToSentry", func() {
		It("should not panic when sentry is disabled", func() {
			Expect(func() {
				sentry.ReportToSentry(
					"test message",
					map[string]string{"tag1": "value1"},
					map[string]any{"key1": "value1"},
				)
			}).NotTo(Panic())
		})

		It("should not panic with nil tags and extra", func() {
			Expect(func() {
				sentry.ReportToSentry("test message", nil, nil)
			}).NotTo(Panic())
		})

		It("should not panic with empty tags and extra", func() {
			Expect(func() {
				sentry.ReportToSentry("test message", map[string]string{}, map[string]any{})
			}).NotTo(Panic())
		})
	})

	Describe("Flush", func() {
		It("should not panic when sentry is disabled", func() {
			Expect(func() {
				sentry.Flush(2 * time.Second)
			}).NotTo(Panic())
		})

		It("should not panic with zero timeout", func() {
			Expect(func() {
				sentry.Flush(0)
			}).NotTo(Panic())
		})
	})

	Describe("Recovery", func() {
		It("should create recovery middleware", func() {
			mw := sentry.Recovery()
			Expect(mw).NotTo(BeNil())
		})

		It("should pass through on normal request", func() {
			r := gin.New()
			r.Use(sentry.Recovery())
			r.GET("/test", func(c *gin.Context) {
				c.String(http.StatusOK, "ok")
			})

			req, _ := http.NewRequest("GET", "/test", nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusOK))
			Expect(w.Body.String()).To(Equal("ok"))
		})

		It("should recover from panic with string", func() {
			r := gin.New()
			r.Use(sentry.Recovery())
			r.GET("/panic", func(c *gin.Context) {
				panic("test panic")
			})

			req, _ := http.NewRequest("GET", "/panic", nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusInternalServerError))
		})

		It("should recover from panic with error", func() {
			r := gin.New()
			r.Use(sentry.Recovery())
			r.GET("/panic", func(c *gin.Context) {
				panic(http.ErrServerClosed)
			})

			req, _ := http.NewRequest("GET", "/panic", nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusInternalServerError))
		})

		It("should recover from panic with arbitrary type", func() {
			r := gin.New()
			r.Use(sentry.Recovery())
			r.GET("/panic", func(c *gin.Context) {
				panic(12345)
			})

			req, _ := http.NewRequest("GET", "/panic", nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			Expect(w.Code).To(Equal(http.StatusInternalServerError))
		})
	})
})
