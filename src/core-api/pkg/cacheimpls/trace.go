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

package cacheimpls

import (
	"context"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/TencentBlueKing/gopkg/cache/memory"
	"go.opentelemetry.io/otel/attribute"

	"core/pkg/trace"
)

// tracedFuncWrapper
func tracedFuncWrapper(name string, fn memory.RetrieveFunc) memory.RetrieveFunc {
	return func(ctx context.Context, key cache.Key) (interface{}, error) {
		startTrace, span := trace.StartTrace(ctx, "cache_load")
		if span != nil {
			span.SetAttributes(attribute.String("cache_name", name))
			defer span.End()
		}
		return fn(startTrace, key)
	}
}

// cacheGet
func cacheGet(ctx context.Context, cache memory.Cache, key cache.Key) (interface{}, error) {
	startCtx, span := trace.StartTrace(ctx, "cache_get")
	if span != nil {
		span.SetAttributes(attribute.String("key", key.Key()))
		defer span.End()
	}
	return cache.Get(startCtx, key)
}

// cacheExists
func cacheExists(ctx context.Context, cache memory.Cache, key cache.Key) bool {
	startCtx, span := trace.StartTrace(ctx, "cache_exit")
	if span != nil {
		span.SetAttributes(attribute.String("key", key.Key()))
		defer span.End()
	}
	return cache.Exists(startCtx, key)
}

// cacheExists
func cacheSet(ctx context.Context, cache memory.Cache, key cache.Key, data interface{}) {
	startCtx, span := trace.StartTrace(ctx, "cache_set")
	if span != nil {
		span.SetAttributes(attribute.String("key", key.Key()))
		defer span.End()
	}
	cache.Set(startCtx, key, data)
}
