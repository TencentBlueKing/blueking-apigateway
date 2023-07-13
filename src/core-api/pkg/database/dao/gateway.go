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

	"github.com/jmoiron/sqlx"

	"core/pkg/database"
)

// TODO: split into thinx and x, for better performance

// Gateway ...
type Gateway struct {
	ID   int64  `db:"id"`
	Name string `db:"name"`
}

// GatewayManager ...
type GatewayManager interface {
	GetByName(ctx context.Context, name string) (Gateway, error)
}

type gatewayManager struct {
	DB *sqlx.DB
}

// NewGatewayManager ...
func NewGatewayManager() GatewayManager {
	return &gatewayManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

// GetByName ...
func (m gatewayManager) GetByName(ctx context.Context, name string) (Gateway, error) {
	gateway := Gateway{}
	query := `SELECT
		id,
		name
		FROM core_api
		WHERE name = ?`
	err := database.SqlxGet(ctx, m.DB, &gateway, query, name)
	return gateway, err
}
