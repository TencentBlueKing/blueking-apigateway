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

// Package bkaidevtrace provides an independent OpenTelemetry trace pipeline
// for BKAIDev Agent trace reporting. It is fully isolated from the project's
// own global tracing to avoid interference.
package bkaidevtrace

import (
	"context"
	"crypto/rand"
	"encoding/binary"
	"fmt"
	mrand "math/rand"
	"sync"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.10.0"
	tc "go.opentelemetry.io/otel/trace"

	"mcp_proxy/pkg/config"
)

var (
	globalProvider *sdktrace.TracerProvider
	globalTracer   tc.Tracer
	propagator     propagation.TextMapPropagator
	once           sync.Once
)

// Init initializes the independent BKAIDev trace pipeline.
func Init(cfg config.BkAIDevTrace) error {
	var initErr error
	once.Do(func() {
		// WithInsecure uses HTTP instead of HTTPS for the OTLP exporter.
		// This is intentional: the BKAIDev trace collector runs in the same
		// internal network, so TLS is not required. The bk.data.token in the
		// resource attributes provides authentication.
		client := otlptracehttp.NewClient(
			otlptracehttp.WithEndpoint(cfg.Endpoint),
			otlptracehttp.WithInsecure(),
		)
		exporter, err := otlptrace.New(context.Background(), client)
		if err != nil {
			initErr = fmt.Errorf("create bkaidevtrace exporter: %w", err)
			return
		}

		tp := sdktrace.NewTracerProvider(
			sdktrace.WithBatcher(exporter),
			sdktrace.WithResource(resource.NewWithAttributes(
				semconv.SchemaURL,
				semconv.ServiceNameKey.String(cfg.ServiceName),
				attribute.Key("bk.data.token").String(cfg.Token),
			)),
			sdktrace.WithSampler(sdktrace.AlwaysSample()),
		)

		globalProvider = tp
		globalTracer = tp.Tracer(cfg.ServiceName)
		propagator = propagation.NewCompositeTextMapPropagator(
			propagation.TraceContext{},
			propagation.Baggage{},
		)
	})
	return initErr
}

// Enabled returns whether the BKAIDev trace pipeline is initialized.
func Enabled() bool {
	return globalTracer != nil
}

// StartSpan starts a new span using the independent tracer.
func StartSpan(ctx context.Context, name string, opts ...tc.SpanStartOption) (context.Context, tc.Span) {
	if globalTracer == nil {
		return ctx, nil
	}
	return globalTracer.Start(ctx, name, opts...)
}

// Extract extracts trace context from carrier using the independent propagator.
func Extract(ctx context.Context, carrier propagation.TextMapCarrier) context.Context {
	if propagator == nil {
		return ctx
	}
	return propagator.Extract(ctx, carrier)
}

// Inject injects trace context into carrier using the independent propagator.
func Inject(ctx context.Context, carrier propagation.TextMapCarrier) {
	if propagator == nil {
		return
	}
	propagator.Inject(ctx, carrier)
}

// GetTraceIDFromContext extracts the trace ID from the active span in context.
func GetTraceIDFromContext(ctx context.Context) string {
	span := tc.SpanFromContext(ctx)
	if span == nil {
		return ""
	}
	sc := span.SpanContext()
	if !sc.TraceID().IsValid() {
		return ""
	}
	return sc.TraceID().String()
}

// GetSpanIDFromContext extracts the span ID from the active span in context.
func GetSpanIDFromContext(ctx context.Context) string {
	span := tc.SpanFromContext(ctx)
	if span == nil {
		return ""
	}
	sc := span.SpanContext()
	if !sc.SpanID().IsValid() {
		return ""
	}
	return sc.SpanID().String()
}

// NewSpanContext creates a span context with a randomly-generated trace ID and span ID.
// This is used to carry a valid trace context without creating an actual span.
func NewSpanContext() tc.SpanContext {
	var traceID tc.TraceID
	var spanID tc.SpanID

	// Try crypto/rand first for both traceID and spanID.
	// If crypto/rand fails (extremely rare), fallback to a single math/rand instance
	// to avoid seed collision when two separate instances are created with the same
	// time-based seed under high concurrency.
	traceOK := true
	if _, err := rand.Read(traceID[:]); err != nil {
		traceOK = false
	}
	if _, err := rand.Read(spanID[:]); err != nil {
		if traceOK {
			// Only traceID succeeded via crypto/rand; generate spanID with math/rand
			r := mrand.New(mrand.NewSource(time.Now().UnixNano()))
			binary.BigEndian.PutUint64(spanID[:], uint64(r.Int63()))
		}
	}
	if !traceOK {
		// crypto/rand failed for traceID; use a single math/rand instance for both
		r := mrand.New(mrand.NewSource(time.Now().UnixNano()))
		binary.BigEndian.PutUint64(traceID[:8], uint64(r.Int63()))
		binary.BigEndian.PutUint64(traceID[8:], uint64(r.Int63()))
		binary.BigEndian.PutUint64(spanID[:], uint64(r.Int63()))
	}

	return tc.NewSpanContext(tc.SpanContextConfig{
		TraceID:    traceID,
		SpanID:     spanID,
		TraceFlags: tc.FlagsSampled,
	})
}

// Shutdown flushes and shuts down the tracer provider.
func Shutdown(ctx context.Context) error {
	if globalProvider == nil {
		return nil
	}
	return globalProvider.Shutdown(ctx)
}
