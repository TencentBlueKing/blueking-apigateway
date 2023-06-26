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
	"strconv"

	"core/pkg/database/dao"

	"github.com/TencentBlueKing/gopkg/cache"
)

// ReleaseKey is the key of release
type ReleaseKey struct {
	GatewayID int64
	StageID   int64
}

// Key return the key string of release
func (k ReleaseKey) Key() string {
	return strconv.FormatInt(k.GatewayID, 10) + ":" + strconv.FormatInt(k.StageID, 10)
}

func retrieveStageByGatewayIDStageID(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(ReleaseKey)

	manager := dao.NewReleaseManager()
	return manager.Get(ctx, key.GatewayID, key.StageID)
}

// GetRelease will get the release from cache by gatewayID and stageID
func GetRelease(ctx context.Context, gatewayID, stageID int64) (release dao.Release, err error) {
	key := ReleaseKey{
		GatewayID: gatewayID,
		StageID:   stageID,
	}
	var value interface{}
	value, err = cacheGet(ctx, releaseCache, key)
	if err != nil {
		return
	}

	var ok bool
	release, ok = value.(dao.Release)
	if !ok {
		err = errors.New("not dao.Release in cache")
		return
	}
	return
}
