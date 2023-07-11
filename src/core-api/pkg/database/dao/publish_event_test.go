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

	"core/pkg/constant"
	"core/pkg/database"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/jmoiron/sqlx"
	"github.com/stretchr/testify/assert"
)

func Test_publishEventManager_Create(t *testing.T) {
	database.RunWithMock(t, func(db *sqlx.DB, mock sqlmock.Sqlmock, t *testing.T) {
		mockQuery := `^INSERT INTO core_publish_event`
		record := PublishEvent{
			GatewayID: 67,
			PublishID: 89,
			StageID:   12,
			Name:      constant.EventNameApplyConfiguration,
			Step:      1,
			Status:    constant.EventStatusSuccess,
			Detail:    map[string]interface{}{"err_msg": "success"},
		}
		mock.ExpectExec(mockQuery).WillReturnResult(
			sqlmock.NewResult(1, 1))

		manager := &publishEventManager{DB: db}
		result, err := manager.Create(context.Background(), record)
		assert.NoError(t, err, "insert db fail.")
		assert.Equal(t, result, int64(1))
	})
}
