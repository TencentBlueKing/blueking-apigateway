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

// Package server ...
package server

import (
	"context"
	"net"
	"net/http"

	"github.com/go-logr/zapr"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.uber.org/zap"
	ctrl "sigs.k8s.io/controller-runtime"
)

// MustServeHTTP ...
func MustServeHTTP(ctx context.Context, addr, network string, handler http.Handler) {
	logger := ctrl.LoggerFrom(ctx).GetSink().(zapr.Underlier).GetUnderlying() //nolint:forcetypeassert
	lc := net.ListenConfig{}
	l, err := lc.Listen(ctx, network, addr)
	if err != nil {
		logger.Panic(
			"Listen address failed",
			zap.Error(err),
			zap.String("address", addr),
			zap.String("network", network),
		)
	}
	err = http.Serve(l, otelhttp.NewHandler(handler, "server")) //nolint:gosec
	if ctx.Err() == nil {
		logger.Panic(
			"Server exited with error",
			zap.Error(err),
			zap.String("address", addr),
			zap.String("network", network),
		)
	} else {
		logger.Error("Server exited with context canceled",
			zap.Error(ctx.Err()), zap.String("address", addr), zap.String("network", network))
	}
}
