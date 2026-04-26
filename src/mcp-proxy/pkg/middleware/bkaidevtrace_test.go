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
	"context"
	"net/http"
	"net/http/httptest"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	tc "go.opentelemetry.io/otel/trace"

	"mcp_proxy/pkg/infra/bkaidevtrace"
	"mcp_proxy/pkg/middleware"
)

var _ = Describe("BkAIDevTraceContextMiddleware", func() {
	BeforeEach(func() {
		gin.SetMode(gin.TestMode)
		bkaidevtrace.ResetForTest()
	})

	AfterEach(func() {
		bkaidevtrace.ResetForTest()
	})

	It("should extract trace context from traceparent header", func() {
		// Set up test provider
		exporter := sdktrace.NewTracerProvider(sdktrace.WithSyncer(&testSpanExporter{}))
		defer func() { _ = exporter.Shutdown(context.Background()) }()
		bkaidevtrace.SetTestProvider(exporter, propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		))

		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)
		c.Request.Header.Set("traceparent", "00-11223344556677889900aabbccddeeff-aabbccddeeff0011-01")

		called := false
		middleware.BkAIDevTraceContextMiddleware()(c)
		called = true

		Expect(called).To(BeTrue())
		spanCtx := tc.SpanFromContext(c.Request.Context()).SpanContext()
		Expect(spanCtx.IsValid()).To(BeTrue())
		Expect(spanCtx.TraceID().String()).To(Equal("11223344556677889900aabbccddeeff"))
	})

	It("should create new span context when no traceparent header", func() {
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

		middleware.BkAIDevTraceContextMiddleware()(c)

		spanCtx := tc.SpanFromContext(c.Request.Context()).SpanContext()
		Expect(spanCtx.IsValid()).To(BeTrue())
		Expect(spanCtx.TraceID().String()).NotTo(BeEmpty())
		Expect(spanCtx.SpanID().String()).NotTo(BeEmpty())
	})

	It("should pass through Next handler", func() {
		w := httptest.NewRecorder()
		c, _ := gin.CreateTestContext(w)
		c.Request = httptest.NewRequest(http.MethodGet, "/test", nil)

		mw := middleware.BkAIDevTraceContextMiddleware()
		mw(c)

		Expect(c.Request.Context()).NotTo(BeNil())
	})
})

type testSpanExporter struct{}

func (t *testSpanExporter) ExportSpans(ctx context.Context, spans []sdktrace.ReadOnlySpan) error {
	return nil
}

func (t *testSpanExporter) Shutdown(ctx context.Context) error {
	return nil
}
