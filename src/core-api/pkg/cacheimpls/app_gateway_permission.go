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
	"database/sql"
	"errors"
	"strconv"

	"github.com/TencentBlueKing/gopkg/cache"

	"core/pkg/database/dao"
	"core/pkg/logging"
)

// AppGatewayPermissionKey is the key of app-gateway permission
type AppGatewayPermissionKey struct {
	AppCode   string
	GatewayID int64
}

// Key return the key string of app-gateway permission
func (k AppGatewayPermissionKey) Key() string {
	return k.AppCode + ":" + strconv.FormatInt(k.GatewayID, 10)
}

func retrieveAppGatewayPermission(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(AppGatewayPermissionKey)

	manager := dao.NewAppGatewayPermissionManager()

	perm, err := manager.Get(ctx, key.AppCode, key.GatewayID)
	// if not permission records, cache `nil`
	if errors.Is(err, sql.ErrNoRows) {
		logging.GetLogger().Debugw("retrieveAppGatewayPermission",
			"appCode", key.AppCode, "gatewayID", key.GatewayID, "perm", perm, "err", err)

		return nil, nil
	}

	return perm, err
}

// GetAppGatewayPermissionExpiredAt get the expired time of the app-gateway permission
func GetAppGatewayPermissionExpiredAt(
	ctx context.Context,
	appCode string,
	gatewayID int64,
) (int64, error) {
	key := AppGatewayPermissionKey{
		AppCode:   appCode,
		GatewayID: gatewayID,
	}
	value, err := cacheGet(ctx, appGatewayPermissionCache, key)
	if err != nil {
		return 0, err
	}

	// if cached value is nil, means no records
	if value == nil {
		return 0, nil
	}

	// var ok bool
	appGatewayPermission, ok := value.(dao.AppGatewayPermission)
	if !ok {
		err = errors.New("not dao.AppGatewayPermission in cache")
		return 0, err
	}

	return appGatewayPermission.Expires.Unix(), nil
}
