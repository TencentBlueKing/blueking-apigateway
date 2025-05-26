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
	"errors"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/spf13/cast"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// StageKey is the key of stage
type StageKey struct {
	ID int
}

// Key return the key string of stage
func (k StageKey) Key() string {
	return cast.ToString(k.ID)
}

func retrieveStageByID(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(StageKey)
	r := repo.Stage
	return repo.Stage.WithContext(ctx).Where(r.ID.Eq(key.ID)).Take()
}

// GetStageByID will get the stage from cache by gatewayID and stageName
func GetStageByID(ctx context.Context, id int) (stage *model.Stage, err error) {
	key := StageKey{
		ID: id,
	}
	var value interface{}
	value, err = cacheGet(ctx, stageCache, key)
	if err != nil {
		return
	}

	var ok bool
	stage, ok = value.(*model.Stage)
	if !ok {
		err = errors.New("not model.Stage in cache")
		return
	}
	return
}
