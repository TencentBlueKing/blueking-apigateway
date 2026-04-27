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
	"sync"

	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

// ResetForTest resets all global state so that Init can be called again in tests.
// NOTE: This function is exported for cross-package test usage (e.g., middleware_test).
// It is only intended for use in test code; production callers should never invoke it.
func ResetForTest() {
	globalProvider = nil
	globalTracer = nil
	propagator = nil
	once = sync.Once{}
}

// SetTestProvider injects a test TracerProvider and propagator directly.
// NOTE: This function is exported for cross-package test usage only.
func SetTestProvider(tp *sdktrace.TracerProvider, p propagation.TextMapPropagator) {
	globalProvider = tp
	globalTracer = tp.Tracer("test")
	propagator = p
}
