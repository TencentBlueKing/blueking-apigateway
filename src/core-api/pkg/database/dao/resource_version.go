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

// ResourceVersion ...
type ResourceVersion struct {
	ID int64 `db:"id"`

	Data string `db:"data"`
}

// ResourceVersionManager ...
type ResourceVersionManager interface {
	Get(ctx context.Context, id int64) (ResourceVersion, error)
}

// NewResourceVersionManager ...
func NewResourceVersionManager() ResourceVersionManager {
	return &resourceVersionManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

type resourceVersionManager struct {
	DB *sqlx.DB
}

// Get ...
func (m resourceVersionManager) Get(ctx context.Context, id int64) (ResourceVersion, error) {
	ResourceVersion := ResourceVersion{}
	query := `SELECT
		id,
		data
		FROM core_resource_version
		WHERE id = ?`
	err := database.SqlxGet(ctx, m.DB, &ResourceVersion, query, id)
	return ResourceVersion, err
}
