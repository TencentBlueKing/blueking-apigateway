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

package mcp_test

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
	sdkmcp "github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/prometheus/client_golang/prometheus"
	dto "github.com/prometheus/client_model/go"

	"mcp_proxy/pkg/constant"
	mcppkg "mcp_proxy/pkg/mcp"
	"mcp_proxy/pkg/metric"
)

// getCounterValue extracts the float64 value from a CounterVec for the given labels
func getCounterValue(cv *prometheus.CounterVec, labels ...string) float64 {
	m := &dto.Metric{}
	if err := cv.WithLabelValues(labels...).Write(m); err != nil {
		return 0
	}
	return m.GetCounter().GetValue()
}

// getGaugeValue extracts the float64 value from a GaugeVec for the given labels
func getGaugeValue(gv *prometheus.GaugeVec, labels ...string) float64 {
	m := &dto.Metric{}
	if err := gv.WithLabelValues(labels...).Write(m); err != nil {
		return 0
	}
	return m.GetGauge().GetValue()
}

// getHistogramCount extracts the sample count from a HistogramVec for the given labels
func getHistogramCount(hv *prometheus.HistogramVec, labels ...string) uint64 {
	m := &dto.Metric{}
	observer, err := hv.GetMetricWithLabelValues(labels...)
	if err != nil {
		return 0
	}
	if ph, ok := observer.(prometheus.Metric); ok {
		if err := ph.Write(m); err != nil {
			return 0
		}
	}
	return m.GetHistogram().GetSampleCount()
}

var _ = Describe("Middleware", func() {
	var (
		gatewayName   string
		serverName    string
		ctx           context.Context
		successResult sdkmcp.Result
	)

	BeforeEach(func() {
		gatewayName = "test-gateway"
		serverName = "test-server"
		ctx = context.WithValue(context.Background(), constant.GatewayName, gatewayName)
		successResult = &sdkmcp.InitializeResult{}
	})

	Describe("LoggingMiddleware", func() {
		It("should not panic and return result", func() {
			middleware := mcppkg.LoggingMiddleware(serverName)

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return successResult, nil
			})

			result, err := handler(ctx, "initialize", nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
		})

		It("should enrich client_id from session's InitializeParams.ClientInfo", func() {
			// Create an MCP server with a tool and our LoggingMiddleware
			server := sdkmcp.NewServer(&sdkmcp.Implementation{Name: "test-server", Version: "1.0.0"}, nil)

			// Add a simple echo tool using the ToolHandler API
			server.AddTool(&sdkmcp.Tool{
				Name:        "echo",
				Description: "Echo tool",
				InputSchema: json.RawMessage(`{"type":"object"}`),
			}, func(ctx context.Context, req *sdkmcp.CallToolRequest) (*sdkmcp.CallToolResult, error) {
				return &sdkmcp.CallToolResult{
					Content: []sdkmcp.Content{&sdkmcp.TextContent{Text: "hello"}},
				}, nil
			})

			// Add LoggingMiddleware — it should pick up clientInfo.Name as client_id
			server.AddReceivingMiddleware(mcppkg.LoggingMiddleware(serverName))

			// Create in-memory transport pair
			serverTransport, clientTransport := sdkmcp.NewInMemoryTransports()

			testCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()

			// Server connect (must be before client)
			serverSession, err := server.Connect(testCtx, serverTransport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer serverSession.Close()

			// Client connect with specific ClientInfo
			client := sdkmcp.NewClient(&sdkmcp.Implementation{
				Name:    "cursor",
				Version: "2.0.0",
			}, nil)

			clientSession, err := client.Connect(testCtx, clientTransport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer clientSession.Close()

			// After initialize, the ServerSession should have InitializeParams.ClientInfo.Name == "cursor"
			initParams := serverSession.InitializeParams()
			Expect(initParams).NotTo(BeNil())
			Expect(initParams.ClientInfo).NotTo(BeNil())
			Expect(initParams.ClientInfo.Name).To(Equal("cursor"))

			// Call the echo tool — this will trigger LoggingMiddleware which should use "cursor" as client_id
			result, err := clientSession.CallTool(testCtx, &sdkmcp.CallToolParams{
				Name: "echo",
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("MetricMiddleware", func() {
		It("should record MCPRequestTotal on successful call", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getCounterValue(metric.MCPRequestTotal, gatewayName, serverName, "initialize", "0", "0")

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return successResult, nil
			})

			_, err := handler(ctx, "initialize", nil)
			Expect(err).NotTo(HaveOccurred())

			after := getCounterValue(metric.MCPRequestTotal, gatewayName, serverName, "initialize", "0", "0")
			Expect(after - before).To(Equal(float64(1)))
		})

		It("should record MCPRequestTotal with error status on failure", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getCounterValue(metric.MCPRequestTotal, gatewayName, serverName, "tools/call", "unknown", "1")

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, errors.New("test error")
			})

			_, _ = handler(ctx, "tools/call", nil)

			after := getCounterValue(metric.MCPRequestTotal, gatewayName, serverName, "tools/call", "unknown", "1")
			Expect(after - before).To(Equal(float64(1)))
		})

		It("should record MCPRequestDuration", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getHistogramCount(metric.MCPRequestDuration, gatewayName, serverName, "tools/list")

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return successResult, nil
			})

			_, err := handler(ctx, "tools/list", nil)
			Expect(err).NotTo(HaveOccurred())

			after := getHistogramCount(metric.MCPRequestDuration, gatewayName, serverName, "tools/list")
			Expect(after - before).To(Equal(uint64(1)))
		})

		It("should record MCPSessionTotal on successful initialize", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return successResult, nil
			})

			_, err := handler(ctx, "initialize", nil)
			Expect(err).NotTo(HaveOccurred())

			after := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)
			Expect(after - before).To(Equal(float64(1)))
		})

		It("should not increment MCPSessionTotal on failed initialize", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, errors.New("init failed")
			})

			_, _ = handler(ctx, "initialize", nil)

			after := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)
			Expect(after - before).To(Equal(float64(0)))
		})

		It("should record MCPErrorTotal with normalized jsonrpc error code", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getCounterValue(metric.MCPErrorTotal, gatewayName, serverName, "tools/call", "method_not_found")

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, &jsonrpc.Error{
					Code:    jsonrpc.CodeMethodNotFound,
					Message: "method not found",
				}
			})

			_, _ = handler(ctx, "tools/call", nil)

			after := getCounterValue(metric.MCPErrorTotal, gatewayName, serverName, "tools/call", "method_not_found")
			Expect(after - before).To(Equal(float64(1)))
		})

		It("should record MCPErrorTotal with unknown error code for non-jsonrpc error", func() {
			middleware := mcppkg.MetricMiddleware(serverName)

			before := getCounterValue(metric.MCPErrorTotal, gatewayName, serverName, "tools/call", "unknown")

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, errors.New("some error")
			})

			_, _ = handler(ctx, "tools/call", nil)

			after := getCounterValue(metric.MCPErrorTotal, gatewayName, serverName, "tools/call", "unknown")
			Expect(after - before).To(Equal(float64(1)))
		})
	})

	Describe("SessionMetricMiddleware", func() {
		It("should decrement MCPSessionTotal on notifications/cancelled", func() {
			// First, set an initial value
			metric.MCPSessionTotal.WithLabelValues(gatewayName, serverName).Inc()
			before := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)

			middleware := mcppkg.SessionMetricMiddleware(serverName)

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, nil
			})

			_, err := handler(ctx, "notifications/cancelled", nil)
			Expect(err).NotTo(HaveOccurred())

			after := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)
			Expect(before - after).To(Equal(float64(1)))
		})

		It("should not decrement MCPSessionTotal for other methods", func() {
			before := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)

			middleware := mcppkg.SessionMetricMiddleware(serverName)

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return successResult, nil
			})

			_, err := handler(ctx, "tools/list", nil)
			Expect(err).NotTo(HaveOccurred())

			after := getGaugeValue(metric.MCPSessionTotal, gatewayName, serverName)
			Expect(after).To(Equal(before))
		})
	})

	Describe("TracingMiddleware", func() {
		It("should not panic and return result when tracing is not initialized", func() {
			middleware := mcppkg.TracingMiddleware(serverName)

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return successResult, nil
			})

			result, err := handler(ctx, "tools/list", nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).To(Equal(successResult))
		})

		It("should propagate errors from next handler", func() {
			middleware := mcppkg.TracingMiddleware(serverName)
			expectedErr := errors.New("handler error")

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, expectedErr
			})

			result, err := handler(ctx, "tools/call", nil)
			Expect(err).To(MatchError(expectedErr))
			Expect(result).To(BeNil())
		})

		It("should propagate jsonrpc errors from next handler", func() {
			middleware := mcppkg.TracingMiddleware(serverName)
			expectedErr := &jsonrpc.Error{
				Code:    jsonrpc.CodeMethodNotFound,
				Message: "method not found",
			}

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				return nil, expectedErr
			})

			result, err := handler(ctx, "tools/call", nil)
			Expect(err).To(MatchError(expectedErr))
			Expect(result).To(BeNil())
		})

		It("should pass correct method to next handler", func() {
			middleware := mcppkg.TracingMiddleware(serverName)
			var receivedMethod string

			handler := middleware(func(ctx context.Context, method string, req sdkmcp.Request) (sdkmcp.Result, error) {
				receivedMethod = method
				return successResult, nil
			})

			_, err := handler(ctx, "initialize", nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(receivedMethod).To(Equal("initialize"))
		})
	})

	Describe("extractToolName", func() {
		It("should return empty string for nil request", func() {
			name := mcppkg.ExtractToolNameForTest(nil)
			Expect(name).To(Equal(""))
		})
	})

	Describe("matchErrorCodeName", func() {
		It("should return human-readable name for standard JSON-RPC codes", func() {
			Expect(mcppkg.MatchErrorCodeNameForTest(-32700)).To(Equal("parse_error"))
			Expect(mcppkg.MatchErrorCodeNameForTest(-32600)).To(Equal("invalid_request"))
			Expect(mcppkg.MatchErrorCodeNameForTest(-32601)).To(Equal("method_not_found"))
			Expect(mcppkg.MatchErrorCodeNameForTest(-32602)).To(Equal("invalid_params"))
			Expect(mcppkg.MatchErrorCodeNameForTest(-32603)).To(Equal("internal_error"))
		})

		It("should return string representation for unknown codes", func() {
			Expect(mcppkg.MatchErrorCodeNameForTest(-32000)).To(Equal("-32000"))
			Expect(mcppkg.MatchErrorCodeNameForTest(42)).To(Equal("42"))
		})
	})
})
