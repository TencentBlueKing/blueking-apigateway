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

package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"
	tc "go.opentelemetry.io/otel/trace"

	"mcp_proxy/pkg/infra/bkaidevtrace"
)

// BkAIDevTraceContextMiddleware extracts traceparent from the incoming HTTP request
// and injects the trace context into the request context using BKAIDev's isolated
// trace propagator (separate from the project's global OTEL tracing). If no
// traceparent is present, a new trace context is created so that downstream MCP
// spans always have a valid trace ID.
func BkAIDevTraceContextMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx := c.Request.Context()
		traceparent := c.GetHeader("traceparent")

		if traceparent != "" {
			// Extract existing trace context from headers
			carrier := headerCarrier(c.Request.Header)
			ctx = bkaidevtrace.Extract(ctx, &carrier)
		} else {
			// No traceparent provided: create a span context with random trace/span IDs
			// without creating an actual span, so that downstream MCP spans have a valid parent.
			spanCtx := bkaidevtrace.NewSpanContext()
			ctx = tc.ContextWithSpanContext(ctx, spanCtx)
		}

		c.Request = c.Request.WithContext(ctx)
		c.Next()
	}
}

type headerCarrier http.Header

// Get returns the value associated with the passed key.
func (h headerCarrier) Get(key string) string {
	return http.Header(h).Get(key)
}

// Set stores the key-value pair.
func (h headerCarrier) Set(key string, value string) {
	http.Header(h).Set(key, value)
}

// Keys lists the keys stored in this carrier.
func (h headerCarrier) Keys() []string {
	keys := make([]string, 0, len(h))
	for k := range h {
		keys = append(keys, k)
	}
	return keys
}
