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

package trace

import (
	"context"
	"fmt"
	"net/http"
	"testing"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
)

func TestGetTraceIDFromContext(t *testing.T) {
	t.Run("returns empty string when no span in context", func(t *testing.T) {
		ctx := context.Background()
		traceID := GetTraceIDFromContext(ctx)
		if traceID != "" {
			t.Errorf("expected empty trace ID, got %q", traceID)
		}
	})

	t.Run("returns stored trace ID from context value", func(t *testing.T) {
		ctx := context.WithValue(context.Background(), constant.TraceID, "feedfacefeedfacefeedfacefeedface")
		traceID := GetTraceIDFromContext(ctx)
		if traceID != "feedfacefeedfacefeedfacefeedface" {
			t.Errorf("expected stored trace ID, got %q", traceID)
		}
	})

	t.Run("returns valid trace ID from active span", func(t *testing.T) {
		exporter := tracetest.NewInMemoryExporter()
		tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
		defer func() { _ = tp.Shutdown(context.Background()) }()

		ctx, span := tp.Tracer("test").Start(context.Background(), "test-span")
		defer span.End()

		traceID := GetTraceIDFromContext(ctx)
		if traceID == "" {
			t.Error("expected non-empty trace ID")
		}
		if len(traceID) != 32 {
			t.Errorf("expected 32-char trace ID, got %d chars: %s", len(traceID), traceID)
		}
	})
}

func TestExtractTraceIDFromTraceparent(t *testing.T) {
	t.Run("extracts trace ID from valid header", func(t *testing.T) {
		traceparent := "00-11223344556677889900aabbccddeeff-aabbccddeeff0011-01"
		traceID := ExtractTraceIDFromTraceparent(traceparent)
		if traceID != "11223344556677889900aabbccddeeff" {
			t.Errorf("expected extracted trace ID, got %q", traceID)
		}
	})

	t.Run("returns empty for invalid header", func(t *testing.T) {
		traceID := ExtractTraceIDFromTraceparent("invalid-traceparent")
		if traceID != "" {
			t.Errorf("expected empty trace ID, got %q", traceID)
		}
	})
}

func TestWrapErrorWithTraceID(t *testing.T) {
	t.Run("returns nil for nil error", func(t *testing.T) {
		ctx := context.Background()
		err := WrapErrorWithTraceID(ctx, nil)
		if err != nil {
			t.Errorf("expected nil, got %v", err)
		}
	})

	t.Run("returns original error when no trace context", func(t *testing.T) {
		ctx := context.Background()
		original := fmt.Errorf("test error")
		err := WrapErrorWithTraceID(ctx, original)
		if err.Error() != "test error" {
			t.Errorf("expected 'test error', got %q", err.Error())
		}
	})

	t.Run("wraps error with trace_id when span exists", func(t *testing.T) {
		exporter := tracetest.NewInMemoryExporter()
		tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
		defer func() { _ = tp.Shutdown(context.Background()) }()

		ctx, span := tp.Tracer("test").Start(context.Background(), "test-span")
		defer span.End()

		original := fmt.Errorf("something went wrong")
		err := WrapErrorWithTraceID(ctx, original)
		if err == nil {
			t.Fatal("expected error, got nil")
		}

		traceID := GetTraceIDFromContext(ctx)
		expected := fmt.Sprintf("something went wrong (trace_id=%s)", traceID)
		if err.Error() != expected {
			t.Errorf("expected %q, got %q", expected, err.Error())
		}
	})
}

func TestStartTrace(t *testing.T) {
	t.Run("returns nil span when global tracer is not initialized", func(t *testing.T) {
		// Reset global tracer
		originalTracer := globalTracer
		globalTracer = nil
		defer func() { globalTracer = originalTracer }()

		ctx, span := StartTrace(context.Background(), "test")
		if span != nil {
			t.Error("expected nil span")
		}
		if ctx == nil {
			t.Error("expected non-nil context")
		}
	})

	t.Run("returns nil span when tracing is disabled", func(t *testing.T) {
		originalTracer := globalTracer
		globalTracer = &Trace{
			config: config.Tracing{Enable: false},
		}
		defer func() { globalTracer = originalTracer }()

		ctx, span := StartTrace(context.Background(), "test")
		if span != nil {
			t.Error("expected nil span when tracing is disabled")
		}
		if ctx == nil {
			t.Error("expected non-nil context")
		}
	})
}

func TestSetTextMapPropagator(t *testing.T) {
	t.Run("propagator injects traceparent into HTTP headers", func(t *testing.T) {
		// Set up trace provider and propagator (mirrors what InitTrace does)
		exporter := tracetest.NewInMemoryExporter()
		tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
		defer func() { _ = tp.Shutdown(context.Background()) }()

		otel.SetTracerProvider(tp)
		otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		))

		// Create a span
		ctx, span := tp.Tracer("test").Start(context.Background(), "test-span")
		defer span.End()

		// Inject into HTTP headers
		headers := http.Header{}
		otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(headers))

		traceparent := headers.Get("Traceparent")
		if traceparent == "" {
			t.Error("expected traceparent header to be injected")
		}

		// Verify W3C traceparent format: version-trace_id-span_id-flags
		if len(traceparent) < 55 {
			t.Errorf("traceparent header too short: %s", traceparent)
		}
	})

	t.Run("propagator extracts traceparent from HTTP headers", func(t *testing.T) {
		exporter := tracetest.NewInMemoryExporter()
		tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
		defer func() { _ = tp.Shutdown(context.Background()) }()

		otel.SetTracerProvider(tp)
		otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		))

		// Create a span and inject into headers
		ctx, span := tp.Tracer("test").Start(context.Background(), "original-span")
		headers := http.Header{}
		otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(headers))
		span.End()

		originalTraceID := GetTraceIDFromContext(ctx)

		// Extract from headers into a new context
		newCtx := otel.GetTextMapPropagator().Extract(context.Background(), propagation.HeaderCarrier(headers))

		// Start a child span in the new context
		newCtx, childSpan := tp.Tracer("test").Start(newCtx, "child-span")
		defer childSpan.End()

		// The child span should share the same trace ID
		childTraceID := GetTraceIDFromContext(newCtx)
		if childTraceID != originalTraceID {
			t.Errorf("expected trace IDs to match: original=%s, child=%s", originalTraceID, childTraceID)
		}
	})

	t.Run("noop propagator does not inject traceparent", func(t *testing.T) {
		exporter := tracetest.NewInMemoryExporter()
		tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
		defer func() { _ = tp.Shutdown(context.Background()) }()

		otel.SetTracerProvider(tp)
		// Reset to noop propagator (default when InitTrace is NOT called)
		otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator())

		ctx, span := tp.Tracer("test").Start(context.Background(), "test-span")
		defer span.End()

		headers := http.Header{}
		otel.GetTextMapPropagator().Inject(ctx, propagation.HeaderCarrier(headers))

		traceparent := headers.Get("Traceparent")
		if traceparent != "" {
			t.Errorf("expected no traceparent with noop propagator, got %s", traceparent)
		}
	})
}

func TestGetTraceSampler(t *testing.T) {
	tests := []struct {
		name    string
		sampler string
		ratio   float64
	}{
		{"always_on", sampleTypeAlwaysOn, 0},
		{"always_off", sampleTypeAlwaysOff, 0},
		{"parent_based_always_on", sampleTypeParentBaseAlwaysOn, 0},
		{"trace_id_ratio", sampleTypeTraceIdRatio, 0.5},
		{"default_ratio", "unknown", 0.1},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			option := getTraceSampler(tt.sampler, tt.ratio)
			if option == nil {
				t.Error("expected non-nil TracerProviderOption")
			}
		})
	}
}

func TestGetExporterClient(t *testing.T) {
	t.Run("returns error for unsupported protocol", func(t *testing.T) {
		_, err := getExporterClient("unsupported", "localhost:4317")
		if err == nil {
			t.Error("expected error for unsupported protocol")
		}
	})

	t.Run("returns http client", func(t *testing.T) {
		client, err := getExporterClient("http", "localhost:4318")
		if err != nil {
			t.Errorf("unexpected error: %v", err)
		}
		if client == nil {
			t.Error("expected non-nil client")
		}
	})

	t.Run("returns grpc client", func(t *testing.T) {
		client, err := getExporterClient("grpc", "localhost:4317")
		if err != nil {
			t.Errorf("unexpected error: %v", err)
		}
		if client == nil {
			t.Error("expected non-nil client")
		}
	})
}
