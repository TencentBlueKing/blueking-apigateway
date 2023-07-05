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

func Test_appGatewayPermissionManager_Get(t *testing.T) {
	database.RunWithMock(t, func(db *sqlx.DB, mock sqlmock.Sqlmock, t *testing.T) {
		mockQuery := `^SELECT id, bk_app_code, api_id, expires FROM permission_app_api`
		bkAppCode := "bk_app_code"
		gatewayID := int64(1)

		permission := AppGatewayPermission{
			ID:        1,
			BkAppCode: bkAppCode,
			GatewayID: gatewayID,
			Expires:   time.Now(),
		}

		mockData := []interface{}{
			permission,
		}
		mockRows := database.NewMockRows(mock, mockData...)

		mock.ExpectQuery(mockQuery).WithArgs(bkAppCode, gatewayID).WillReturnRows(mockRows)

		manager := &appGatewayPermissionManager{DB: db}
		p, err := manager.Get(context.Background(), bkAppCode, gatewayID)

		assert.NoError(t, err, "query from db fail.")
		assert.Equal(t, permission, p)
	})
}
