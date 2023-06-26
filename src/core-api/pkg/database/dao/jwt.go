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
	"core/pkg/database"

	"github.com/jmoiron/sqlx"
)

// JWT ...
type JWT struct {
	PublicKey string `db:"public_key"`
}

// JWTManager ...
type JWTManager interface {
	Get(ctx context.Context, gatewayID int64) (JWT, error)
}

// NewJWTManager ...
func NewJWTManager() JWTManager {
	return &jwtManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

type jwtManager struct {
	DB *sqlx.DB
}

// Get ...
func (m jwtManager) Get(ctx context.Context, gatewayID int64) (JWT, error) {
	JWT := JWT{}
	query := `SELECT
		public_key
		FROM core_jwt
		WHERE api_id = ?`
	err := database.SqlxGet(ctx, m.DB, &JWT, query, gatewayID)
	return JWT, err
}
