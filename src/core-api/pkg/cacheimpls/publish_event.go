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
	"fmt"
)

// PublishEventKey is the key of publish event
type PublishEventKey struct {
	GatewayID int64
	StageID   int64
	PublishID int64
	Step      int
	Status    string
}

// Key return the key string of publish event
func (k PublishEventKey) Key() string {
	return fmt.Sprintf("%d:%d:%d:%d:%s", k.GatewayID, k.StageID, k.PublishID, k.Step, k.Status)
}

// PublishEventExists will heck if event exists
func PublishEventExists(ctx context.Context, key PublishEventKey) bool {
	k := key.Key()
	_, ok := publishEventCache.Get(k)
	return ok
}

// PublishEventSet will set event in cache
func PublishEventSet(ctx context.Context, key PublishEventKey) {
	publishEventCache.Set(key.Key(), struct{}{}, 0)
}
