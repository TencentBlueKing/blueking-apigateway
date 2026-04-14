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

// Package metric ...
package metric

import (
	"github.com/prometheus/client_golang/prometheus"
)

const (
	serviceName = "apigateway-mcp-proxy"
)

// Metric collectors – initialized in InitMetrics() with the configured prefix.
var (
	// RequestCount api状态计数 + server_ip的请求数量和状态
	RequestCount *prometheus.CounterVec

	// RequestDuration api响应时间分布
	RequestDuration *prometheus.HistogramVec

	// --- MCP 协议级指标 ---

	// MCPRequestTotal MCP 方法调用计数
	MCPRequestTotal *prometheus.CounterVec

	// MCPRequestDuration MCP 方法调用耗时分布
	MCPRequestDuration *prometheus.HistogramVec

	// MCPToolCallTotal MCP tools/call 调用计数（按工具名细分）
	MCPToolCallTotal *prometheus.CounterVec

	// MCPSessionTotal 当前活跃 MCP 会话数（Gauge）
	MCPSessionTotal *prometheus.GaugeVec

	// MCPErrorTotal MCP 错误计数（按错误码分类）
	MCPErrorTotal *prometheus.CounterVec

	// MCPRequestBodySize MCP 请求体大小分布（字节）
	MCPRequestBodySize *prometheus.HistogramVec

	// MCPResponseBodySize MCP 响应体大小分布（字节）
	MCPResponseBodySize *prometheus.HistogramVec
)

// InitMetrics creates and registers all metric collectors.
// metricNamePrefix comes from config (McpServer.MetricNamePrefix), aligned with
// the dashboard's PROMETHEUS_METRIC_NAME_PREFIX so that PromQL queries match.
func InitMetrics(metricNamePrefix string) {
	RequestCount = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        metricNamePrefix + "mcp_proxy_requests_total",
			Help:        "How many HTTP requests processed, partitioned by status code, method and HTTP path.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"method", "path", "status", "mcp_server_name"},
	)

	RequestDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:        metricNamePrefix + "mcp_proxy_request_duration_milliseconds",
		Help:        "How long it took to process the request, partitioned by status code, method and HTTP path.",
		ConstLabels: prometheus.Labels{"service": serviceName},
		Buckets:     []float64{500, 1000, 2000, 5000, 10000, 30000, 60000},
	},
		[]string{"method", "path", "status", "mcp_server_name"},
	)

	MCPRequestTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_requests_total",
			Help:        "Total number of MCP method calls, partitioned by gateway, server, method, app_code, error_code and error.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "method", "app_code", "error_code", "error"},
	)

	MCPRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_request_duration_milliseconds",
			Help:        "Duration of MCP method calls in milliseconds.",
			ConstLabels: prometheus.Labels{"service": serviceName},
			Buckets:     []float64{50, 100, 200, 500, 1000, 2000, 5000, 10000, 30000, 60000},
		},
		[]string{"gateway_name", "mcp_server_name", "method", "app_code"},
	)

	MCPToolCallTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_tool_calls_total",
			Help:        "Total number of MCP tools/call invocations, partitioned by gateway, server, tool, app_code and error.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "tool_name", "app_code", "error_code", "error"},
	)

	MCPSessionTotal = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_sessions_active",
			Help:        "Number of currently active MCP sessions.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "app_code"},
	)

	// MCPErrorTotal MCP 错误计数（按错误码分类）
	// NOTE: 与 MCPRequestTotal{error="1"} 有信息重叠，保留此指标是为了方便在不同 dashboard 中
	// 直接查询错误分布，无需通过 MCPRequestTotal 的 error label 二次过滤。
	MCPErrorTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_errors_total",
			Help:        "Total number of MCP errors, partitioned by gateway, server, method, app_code and error code.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "method", "app_code", "error_code"},
	)

	// MCPRequestBodySize MCP 请求体大小分布（字节）
	MCPRequestBodySize = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_request_body_size_bytes",
			Help:        "MCP request body size distribution in bytes.",
			ConstLabels: prometheus.Labels{"service": serviceName},
			Buckets:     []float64{100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000},
		},
		[]string{"gateway_name", "mcp_server_name", "method"},
	)

	// MCPResponseBodySize MCP 响应体大小分布（字节）
	MCPResponseBodySize = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:        metricNamePrefix + "mcp_proxy_mcp_response_body_size_bytes",
			Help:        "MCP response body size distribution in bytes.",
			ConstLabels: prometheus.Labels{"service": serviceName},
			Buckets:     []float64{100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000},
		},
		[]string{"gateway_name", "mcp_server_name", "method"},
	)

	// Register all collectors
	prometheus.MustRegister(RequestCount)
	prometheus.MustRegister(RequestDuration)
	prometheus.MustRegister(MCPRequestTotal)
	prometheus.MustRegister(MCPRequestDuration)
	prometheus.MustRegister(MCPToolCallTotal)
	prometheus.MustRegister(MCPSessionTotal)
	prometheus.MustRegister(MCPErrorTotal)
	prometheus.MustRegister(MCPRequestBodySize)
	prometheus.MustRegister(MCPResponseBodySize)
}
