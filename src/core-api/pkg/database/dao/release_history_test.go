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
	"testing"
	"time"

	sqlmock "github.com/DATA-DOG/go-sqlmock"
	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/assert"

	"core/pkg/database"
)

func Test_releaseHistoryManager_Get(t *testing.T) {
	database.RunWithMock(t, func(db *sqlx.DB, mock sqlmock.Sqlmock, t *testing.T) {
		mockQuery := `^SELECT 
				         stage_id,
                         api_id,
                         created_time,
				         updated_time 
			         FROM core_release_history 
			         WHERE id = ?`
		publishID := 16
		record := ReleaseHistory{
			ID:                16,
			CreatedTime:       time.Time{},
			UpdatedTime:       time.Time{},
			GatewayID:         23,
			ResourceVersionID: 23,
			StageID:           23,
		}
		mockData := []interface{}{
			record,
		}
		mockRows := database.NewMockRows(mock, mockData...)
		mock.ExpectQuery(mockQuery).WithArgs(publishID).WillReturnRows(mockRows)

		manager := &releaseHistoryManager{DB: db}
		p, err := manager.Get(context.Background(), int64(publishID))
		assert.NoError(t, err, "query from db fail.")
		assert.Equal(t, record.ID, p.ID)
	})
}
