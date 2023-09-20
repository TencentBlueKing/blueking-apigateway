/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
	"sync"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	"go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.10.0"
	tc "go.opentelemetry.io/otel/trace"

	"core/pkg/config"
)

const (
	sampleTypeAlwaysOn           = "always_on"
	sampleTypeAlwaysOff          = "always_off"
	sampleTypeParentBaseAlwaysOn = "parent_based_always_on"
	sampleTypeTraceIdRatio       = "trace_id_ratio"
)

type Trace struct {
	tc.Tracer
	config config.Tracing
}

// Tracer global tracer
var globalTracer *Trace

var traceOnce sync.Once

// InitTrace init
func InitTrace(config config.Tracing) error {
	var err error
	// init global tracer
	traceOnce.Do(func() {
		// init exporter
		client, clientErr := getExporterClient(config.Type, config.Endpoint)
		if clientErr != nil {
			err = clientErr
			return
		}
		exporter, exporterErr := otlptrace.New(context.Background(), client)
		if exporterErr != nil {
			err = exporterErr
			return
		}
		traceOptions := []trace.TracerProviderOption{
			trace.WithBatcher(exporter),
			trace.WithResource(resource.NewWithAttributes(
				semconv.SchemaURL,
				semconv.ServiceNameKey.String(config.ServiceName),
				attribute.Key("bk.data.token").String(config.Token),
			)),
		}
		// get sampler
		traceOptions = append(traceOptions, getTraceSampler(config.Sampler, config.SamplerRatio))
		// init provider
		tp := trace.NewTracerProvider(traceOptions...)
		// set  global provider
		otel.SetTracerProvider(tp)
		globalTracer = &Trace{
			Tracer: tp.Tracer(config.ServiceName),
			config: config,
		}
	})
	if err != nil {
		return err
	}
	return nil
}

// getExporterClient Get exporter client
func getExporterClient(protocolType string, endpoint string) (otlptrace.Client, error) {
	switch protocolType {
	case "http":
		return otlptracehttp.NewClient(
			otlptracehttp.WithEndpoint(endpoint),
			otlptracehttp.WithInsecure(),
		), nil
	case "grpc":
		return otlptracegrpc.NewClient(
			otlptracegrpc.WithEndpoint(endpoint),
			otlptracegrpc.WithInsecure(),
		), nil
	default:
		return nil, fmt.Errorf("unsupported protocol type:%s", protocolType)
	}
}

// StartTrace  start span from global tracer
func StartTrace(ctx context.Context, name string) (context.Context, tc.Span) {
	if globalTracer != nil && globalTracer.config.Enable {
		return globalTracer.Tracer.Start(ctx, name)
	} else {
		return ctx, nil
	}
}

// getTraceSampler get the sampler strategy
func getTraceSampler(samplerStrategy string, ratio float64) trace.TracerProviderOption {
	switch samplerStrategy {
	case sampleTypeAlwaysOn:
		return trace.WithSampler(trace.AlwaysSample())
	case sampleTypeAlwaysOff:
		return trace.WithSampler(trace.NeverSample())
	case sampleTypeParentBaseAlwaysOn:
		return trace.WithSampler(trace.ParentBased(trace.AlwaysSample()))
	default:
		// TraceIDRatioBased samples
		return trace.WithSampler(trace.TraceIDRatioBased(ratio))
	}
}
