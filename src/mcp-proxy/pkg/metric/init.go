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

// RequestCount ...
var (
	// RequestCount api状态计数 + server_ip的请求数量和状态
	RequestCount = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        "apigateway_mcp_proxy_requests_total",
			Help:        "How many HTTP requests processed, partitioned by status code, method and HTTP path.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"method", "path", "status", "mcp_server_name"},
	)

	// RequestDuration api响应时间分布
	RequestDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:        "apigateway_mcp_proxy_request_duration_milliseconds",
		Help:        "How long it took to process the request, partitioned by status code, method and HTTP path.",
		ConstLabels: prometheus.Labels{"service": serviceName},
		Buckets:     []float64{500, 1000, 2000, 5000, 10000, 30000, 60000},
	},
		[]string{"method", "path", "status", "mcp_server_name"},
	)

	// --- MCP 协议级指标 ---

	// MCPRequestTotal MCP 方法调用计数
	MCPRequestTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        "apigateway_mcp_proxy_mcp_requests_total",
			Help:        "Total number of MCP method calls, partitioned by gateway, server, method, error_code and error.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "method", "error_code", "error"},
	)

	// MCPRequestDuration MCP 方法调用耗时分布
	MCPRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:        "apigateway_mcp_proxy_mcp_request_duration_milliseconds",
			Help:        "Duration of MCP method calls in milliseconds.",
			ConstLabels: prometheus.Labels{"service": serviceName},
			Buckets:     []float64{50, 100, 200, 500, 1000, 2000, 5000, 10000, 30000, 60000},
		},
		[]string{"gateway_name", "mcp_server_name", "method"},
	)

	// MCPToolCallTotal MCP tools/call 调用计数（按工具名细分）
	MCPToolCallTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        "apigateway_mcp_proxy_mcp_tool_calls_total",
			Help:        "Total number of MCP tools/call invocations, partitioned by gateway, server, tool and error.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "tool_name", "error_code", "error"},
	)

	// MCPSessionTotal 当前活跃 MCP 会话数（Gauge）
	MCPSessionTotal = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name:        "apigateway_mcp_proxy_mcp_sessions_active",
			Help:        "Number of currently active MCP sessions.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name"},
	)

	// MCPErrorTotal MCP 错误计数（按错误码分类）
	// NOTE: 与 MCPRequestTotal{error="1"} 有信息重叠，保留此指标是为了方便在不同 dashboard 中
	// 直接查询错误分布，无需通过 MCPRequestTotal 的 error label 二次过滤。
	MCPErrorTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name:        "apigateway_mcp_proxy_mcp_errors_total",
			Help:        "Total number of MCP errors, partitioned by gateway, server, method and error code.",
			ConstLabels: prometheus.Labels{"service": serviceName},
		},
		[]string{"gateway_name", "mcp_server_name", "method", "error_code"},
	)
)

// InitMetrics will register the metrics
func InitMetrics() {
	// Register the summary and the histogram with Prometheus's default registry.
	prometheus.MustRegister(RequestCount)
	prometheus.MustRegister(RequestDuration)

	// MCP protocol-level metrics
	prometheus.MustRegister(MCPRequestTotal)
	prometheus.MustRegister(MCPRequestDuration)
	prometheus.MustRegister(MCPToolCallTotal)
	prometheus.MustRegister(MCPSessionTotal)
	prometheus.MustRegister(MCPErrorTotal)
}
