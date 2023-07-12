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

	"github.com/TencentBlueKing/gopkg/cache"

	"core/pkg/database/dao"
)

// ReleaseHistoryCacheKey is the key of jwt public key
type ReleaseHistoryCacheKey struct {
	ReleaseID int64
}

// Key return the key string of release history
func (k ReleaseHistoryCacheKey) Key() string {
	return strconv.FormatInt(k.ReleaseID, 10)
}

func retrieveReleaseHistory(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(ReleaseHistoryCacheKey)

	manager := dao.NewReleaseHistoryManger()

	releaseHistory, err := manager.Get(ctx, key.ReleaseID)
	if err != nil {
		return "", err
	}

	return releaseHistory, nil
}

// GetReleaseHistory will get the jwt public key from cache by ReleaseID
func GetReleaseHistory(ctx context.Context, releaseID int64) (releaseHistory dao.ReleaseHistory, err error) {
	key := ReleaseHistoryCacheKey{
		ReleaseID: releaseID,
	}
	var value interface{}
	value, err = cacheGet(ctx, releaseHistoryCache, key)
	if err != nil {
		return
	}

	var ok bool
	releaseHistory, ok = value.(dao.ReleaseHistory)
	if !ok {
		err = errors.New("not ReleaseHistory in cache")
		return
	}
	return
}
