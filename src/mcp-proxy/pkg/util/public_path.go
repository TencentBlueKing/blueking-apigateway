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

package util

import (
	"net/http"
	"strings"
)

// RequestWithPublicPathPrefix returns a shallow clone of r whose URL.Path is prefixed when needed.
// Used so handlers (e.g. MCP SSE) that advertise req.URL in responses match the client-facing path
// behind a reverse proxy that strips a path prefix.
//
// prefix should be like "/api/bk-apigateway/prod/..." without a trailing slash. If r.URL.Path
// already has prefix on a path-segment boundary, r is returned unchanged.
func RequestWithPublicPathPrefix(r *http.Request, prefix string) *http.Request {
	prefix = normalizePublicPathPrefix(prefix)
	if prefix == "" || r == nil || r.URL == nil {
		return r
	}
	if hasPathPrefix(r.URL.Path, prefix) {
		return r
	}
	r2 := r.Clone(r.Context())
	u := *r.URL
	r2.URL = &u
	r2.URL.Path = prefix + r.URL.Path
	return r2
}

// hasPathPrefix reports whether path starts with prefix at a path segment boundary.
func hasPathPrefix(path, prefix string) bool {
	if !strings.HasPrefix(path, prefix) {
		return false
	}
	return len(path) == len(prefix) || path[len(prefix)] == '/'
}

func normalizePublicPathPrefix(prefix string) string {
	prefix = strings.TrimSpace(prefix)
	prefix = strings.Trim(prefix, `"'`)
	for strings.HasSuffix(prefix, "/") && prefix != "" {
		prefix = strings.TrimSuffix(prefix, "/")
	}
	if prefix == "" {
		return ""
	}
	if !strings.HasPrefix(prefix, "/") {
		prefix = "/" + prefix
	}
	return prefix
}
