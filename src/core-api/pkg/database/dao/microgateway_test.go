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
	"testing"

	"core/pkg/database"

	sqlmock "github.com/DATA-DOG/go-sqlmock"
	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/assert"
)

func Test_microGatewayManager_Get(t *testing.T) {
	database.RunWithMock(t, func(db *sqlx.DB, mock sqlmock.Sqlmock, t *testing.T) {
		mockQuery := `^SELECT id, api_id, is_shared, is_managed, config FROM core_micro_gateway`

		instanceID := "instanceID"

		record := MicroGateway{
			ID:        "uuid",
			GatewayID: 1,
			IsShared:  true,
			IsManaged: true,
			Config:    "{}",
		}

		mockData := []interface{}{
			record,
		}
		mockRows := database.NewMockRows(mock, mockData...)

		mock.ExpectQuery(mockQuery).WithArgs(instanceID).WillReturnRows(mockRows)

		manager := &microGatewayManager{DB: db}
		p, err := manager.Get(instanceID)

		assert.NoError(t, err, "query from db fail.")
		assert.Equal(t, record, p)
	})
}
