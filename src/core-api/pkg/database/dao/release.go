/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

// NOTE: relationship release - stage is one-to-one

// Release ...
type Release struct {
	ID int64 `db:"id"`

	GatewayID         int64 `db:"api_id"`
	StageID           int64 `db:"stage_id"`
	ResourceVersionID int64 `db:"resource_version_id"`
}

// ReleaseManager ...
type ReleaseManager interface {
	Get(ctx context.Context, gatewayID int64, stageID int64) (Release, error)
}

type releaseManager struct {
	DB *sqlx.DB
}

// NewReleaseManager ...
func NewReleaseManager() ReleaseManager {
	return &releaseManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

// Get ...
func (m releaseManager) Get(ctx context.Context, gatewayID int64, stageID int64) (Release, error) {
	Release := Release{}
	query := `SELECT
		id,
		api_id,
		stage_id,
		resource_version_id
		FROM core_release
		WHERE api_id = ?
		AND stage_id = ?`
	err := database.SqlxGet(ctx, m.DB, &Release, query, gatewayID, stageID)
	return Release, err
}
