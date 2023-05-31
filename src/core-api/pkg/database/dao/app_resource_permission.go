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
	"time"

	"core/pkg/database"

	"github.com/jmoiron/sqlx"
)

// TODO: split into thinx and x, for better performance

// AppResourcePermission ...
type AppResourcePermission struct {
	ID        int64  `db:"id"`
	BkAppCode string `db:"bk_app_code"`
	// NOTE: here map the api_id to gateway_id
	GatewayID  int64     `db:"api_id"`
	ResourceID int64     `db:"resource_id"`
	Expires    time.Time `db:"expires"`
}

// AppResourcePermissionManager ...
type AppResourcePermissionManager interface {
	Get(bkAppCode string, gatewayID int64, resourceID int64) (AppResourcePermission, error)
}

// NewAppResourcePermissionManager ...
func NewAppResourcePermissionManager() AppResourcePermissionManager {
	return &appResourcePermissionManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

type appResourcePermissionManager struct {
	DB *sqlx.DB
}

// Get ...
func (m appResourcePermissionManager) Get(
	bkAppCode string,
	gatewayID int64,
	resourceID int64,
) (AppResourcePermission, error) {
	perm := AppResourcePermission{}
	query := `SELECT
		id,
		bk_app_code,
		api_id,
		resource_id,
		expires
		FROM permission_app_resource
		WHERE bk_app_code = ?
		AND api_id = ?
		AND resource_id = ?`
	err := database.SqlxGet(m.DB, &perm, query, bkAppCode, gatewayID, resourceID)
	return perm, err
}
