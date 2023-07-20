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

package dao

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

import (
	"context"
	"time"

	"github.com/jmoiron/sqlx"

	"core/pkg/database"
)

// TODO: split into thinx and x, for better performance

// AppGatewayPermission ...
type AppGatewayPermission struct {
	ID        int64  `db:"id"`
	BkAppCode string `db:"bk_app_code"`
	// NOTE: here map the api_id to gateway_id
	GatewayID int64     `db:"api_id"`
	Expires   time.Time `db:"expires"`
}

// AppGatewayPermissionManager ...
type AppGatewayPermissionManager interface {
	Get(ctx context.Context, bkAppCode string, gatewayID int64) (AppGatewayPermission, error)
}

type appGatewayPermissionManager struct {
	DB *sqlx.DB
}

// NewAppGatewayPermissionManager ...
func NewAppGatewayPermissionManager() AppGatewayPermissionManager {
	return &appGatewayPermissionManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

// Get ...
func (m appGatewayPermissionManager) Get(
	ctx context.Context,
	bkAppCode string,
	gatewayID int64,
) (AppGatewayPermission, error) {
	perm := AppGatewayPermission{}
	query := `SELECT
		id,
		bk_app_code,
		api_id,
		expires
		FROM permission_app_api
		WHERE bk_app_code = ?
		AND api_id = ?`
	err := database.SqlxGet(ctx, m.DB, &perm, query, bkAppCode, gatewayID)
	return perm, err
}
