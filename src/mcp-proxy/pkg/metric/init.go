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
)

// InitMetrics will register the metrics
func InitMetrics() {
	// Register the summary and the histogram with Prometheus's default registry.
	prometheus.MustRegister(RequestCount)
	prometheus.MustRegister(RequestDuration)
}
