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

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"

	"github.com/jmoiron/sqlx"

	"core/pkg/database"
)

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

type ReleaseHistory struct {
	ID                int64     `db:"id"`
	GatewayID         int64     `db:"api_id"`
	StageID           int       `db:"stage_id"`
	ResourceVersionID int       `db:"resource_version_id"`
	CreatedTime       time.Time `db:"created_time"`
	UpdatedTime       time.Time `db:"updated_time"`
}

type ReleaseHistoryManger interface {
	Get(ctx context.Context, publishID int64) (ReleaseHistory, error)
}

// NewReleaseHistoryManger
func NewReleaseHistoryManger() ReleaseHistoryManger {
	return &releaseHistoryManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

type releaseHistoryManager struct {
	DB *sqlx.DB
}

var _ ReleaseHistoryManger = releaseHistoryManager{}

// Get release history by id
func (p releaseHistoryManager) Get(ctx context.Context, publishID int64) (ReleaseHistory, error) {
	query := `SELECT 
		stage_id,
		api_id,
		created_time,
		updated_time 
		FROM core_release_history 
		WHERE id = ?`
	var releaseHistory ReleaseHistory
	err := database.SqlxGet(ctx, p.DB, &releaseHistory, query, publishID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return releaseHistory, nil
		}
		return releaseHistory, fmt.Errorf("get release history err: %w", err)
	}
	return releaseHistory, nil
}
