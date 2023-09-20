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
	"strings"

	"github.com/jmoiron/sqlx"

	"core/pkg/database"
)

// TODO: split into thinx and x, for better performance

// MicroGateway ...
type MicroGateway struct {
	// it's a uuid
	ID        string `db:"id"`
	GatewayID int64  `db:"api_id"`

	IsShared  bool `db:"is_shared"`
	IsManaged bool `db:"is_managed"`

	Config string `db:"config"`
}

// MicroGatewayManager ...
type MicroGatewayManager interface {
	Get(ctx context.Context, instanceID string) (MicroGateway, error)
}

type microGatewayManager struct {
	DB *sqlx.DB
}

// NewMicroGatewayManager ...
func NewMicroGatewayManager() MicroGatewayManager {
	return &microGatewayManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

// Get ...
func (m microGatewayManager) Get(ctx context.Context, instanceID string) (MicroGateway, error) {
	// the id in database is uuid(32), the django handled the 36 to 32 by default
	// but here we need to do it ourselves
	instanceID = strings.ReplaceAll(instanceID, "-", "")

	perm := MicroGateway{}
	query := `SELECT
		id,
		api_id,
		is_shared,
		is_managed,
		config
		FROM core_micro_gateway
		WHERE id = ?`
	err := database.SqlxGet(ctx, m.DB, &perm, query, instanceID)
	return perm, err
}
