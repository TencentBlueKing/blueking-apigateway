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

package bkaidevtrace

import (
	"context"
	"net/http"
	"testing"

	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"

	"mcp_proxy/pkg/config"
)

func setupTestProvider(t *testing.T) (*sdktrace.TracerProvider, *tracetest.InMemoryExporter) {
	t.Helper()
	exporter := tracetest.NewInMemoryExporter()
	tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
	return tp, exporter
}

func TestInit(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	err := Init(config.BkAIDevTrace{
		Enable:      true,
		Endpoint:    "localhost:4318",
		ServiceName: "test-service",
		Token:       "test-token",
	})
	if err != nil {
		t.Fatalf("Init failed: %v", err)
	}

	if !Enabled() {
		t.Error("expected Enabled() to be true after Init")
	}

	if globalProvider == nil {
		t.Error("expected globalProvider to be set")
	}

	if globalTracer == nil {
		t.Error("expected globalTracer to be set")
	}

	if propagator == nil {
		t.Error("expected propagator to be set")
	}
}

func TestEnabled(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	if Enabled() {
		t.Error("expected Enabled() to be false before Init")
	}

	tp, _ := setupTestProvider(t)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	SetTestProvider(tp, propagation.TraceContext{})

	if !Enabled() {
		t.Error("expected Enabled() to be true after setting test provider")
	}
}

func TestStartSpan(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	tp, exporter := setupTestProvider(t)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	SetTestProvider(tp, propagation.TraceContext{})

	ctx, span := StartSpan(context.Background(), "test-span")
	if span == nil {
		t.Fatal("expected non-nil span")
	}
	span.End()

	spans := exporter.GetSpans()
	if len(spans) != 1 {
		t.Fatalf("expected 1 span, got %d", len(spans))
	}
	if spans[0].Name != "test-span" {
		t.Errorf("expected span name 'test-span', got %q", spans[0].Name)
	}

	if ctx == nil {
		t.Error("expected non-nil context")
	}
}

func TestStartSpanNotInitialized(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	ctx, span := StartSpan(context.Background(), "test-span")
	if span != nil {
		t.Error("expected nil span when not initialized")
	}
	if ctx == nil {
		t.Error("expected non-nil context")
	}
}

func TestGetTraceIDFromContext(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	tp, _ := setupTestProvider(t)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	SetTestProvider(tp, propagation.TraceContext{})

	t.Run("returns empty when no span", func(t *testing.T) {
		traceID := GetTraceIDFromContext(context.Background())
		if traceID != "" {
			t.Errorf("expected empty trace ID, got %q", traceID)
		}
	})

	t.Run("returns valid trace ID from active span", func(t *testing.T) {
		ctx, span := StartSpan(context.Background(), "test-span")
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

func TestGetSpanIDFromContext(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	tp, _ := setupTestProvider(t)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	SetTestProvider(tp, propagation.TraceContext{})

	t.Run("returns empty when no span", func(t *testing.T) {
		spanID := GetSpanIDFromContext(context.Background())
		if spanID != "" {
			t.Errorf("expected empty span ID, got %q", spanID)
		}
	})

	t.Run("returns valid span ID from active span", func(t *testing.T) {
		ctx, span := StartSpan(context.Background(), "test-span")
		defer span.End()

		spanID := GetSpanIDFromContext(ctx)
		if spanID == "" {
			t.Error("expected non-empty span ID")
		}
		if len(spanID) != 16 {
			t.Errorf("expected 16-char span ID, got %d chars: %s", len(spanID), spanID)
		}
	})
}

func TestExtract(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	tp, _ := setupTestProvider(t)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	SetTestProvider(tp, propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	// Create a span and inject into headers
	ctx, span := StartSpan(context.Background(), "parent-span")
	defer span.End()

	parentTraceID := GetTraceIDFromContext(ctx)

	headers := http.Header{}
	Inject(ctx, propagation.HeaderCarrier(headers))

	traceparent := headers.Get("Traceparent")
	if traceparent == "" {
		t.Fatal("expected traceparent header to be injected")
	}

	// Extract into a new context and start a child span
	newCtx := Extract(context.Background(), propagation.HeaderCarrier(headers))
	childCtx, childSpan := StartSpan(newCtx, "child-span")
	defer childSpan.End()

	childTraceID := GetTraceIDFromContext(childCtx)
	if childTraceID != parentTraceID {
		t.Errorf("expected trace IDs to match: parent=%s, child=%s", parentTraceID, childTraceID)
	}
}

func TestExtractNoPropagator(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	// No propagator set
	ctx := Extract(context.Background(), propagation.HeaderCarrier(http.Header{}))
	if ctx == nil {
		t.Error("expected non-nil context")
	}
}

func TestNewSpanContext(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	spanCtx := NewSpanContext()

	if !spanCtx.IsValid() {
		t.Error("expected valid span context")
	}
	if !spanCtx.HasTraceID() {
		t.Error("expected span context to have trace ID")
	}
	if !spanCtx.HasSpanID() {
		t.Error("expected span context to have span ID")
	}
	if !spanCtx.IsSampled() {
		t.Error("expected span context to be sampled")
	}

	traceIDStr := spanCtx.TraceID().String()
	if len(traceIDStr) != 32 {
		t.Errorf("expected 32-char trace ID, got %d chars: %s", len(traceIDStr), traceIDStr)
	}

	spanIDStr := spanCtx.SpanID().String()
	if len(spanIDStr) != 16 {
		t.Errorf("expected 16-char span ID, got %d chars: %s", len(spanIDStr), spanIDStr)
	}

	// Ensure two calls produce different IDs
	spanCtx2 := NewSpanContext()
	if spanCtx.TraceID() == spanCtx2.TraceID() {
		t.Error("expected different trace IDs for two calls")
	}
	if spanCtx.SpanID() == spanCtx2.SpanID() {
		t.Error("expected different span IDs for two calls")
	}
}

func TestShutdown(t *testing.T) {
	ResetForTest()
	defer ResetForTest()

	tp, _ := setupTestProvider(t)
	SetTestProvider(tp, nil)

	if err := Shutdown(context.Background()); err != nil {
		t.Errorf("unexpected shutdown error: %v", err)
	}

	// Shutdown with nil provider should not panic
	ResetForTest()
	if err := Shutdown(context.Background()); err != nil {
		t.Errorf("unexpected shutdown error with nil provider: %v", err)
	}
}
