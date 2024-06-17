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
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/go-sql-driver/mysql"
	"github.com/jmoiron/sqlx"

	"core/pkg/database"
)

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

type PublishEvent struct {
	ID          int64     `db:"id"`
	GatewayID   int64     `db:"gateway_id"`
	PublishID   int64     `db:"publish_id"`
	StageID     int64     `db:"stage_id"`
	Name        string    `db:"name"`
	Step        int       `db:"step"`
	Status      string    `db:"status"`
	Detail      Detail    `db:"detail"`
	CreatedTime time.Time `db:"created_time"`
	UpdatedTime time.Time `db:"updated_time"`
}

type Detail map[string]interface{}

// Scan Implement the sql.Scanner interface, Scan scans the value to Detail
func (d *Detail) Scan(value interface{}) error {
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New(fmt.Sprint("Failed to unmarshal Detail value:", value))
	}
	resultMap := make(Detail)
	err := json.Unmarshal(bytes, &resultMap)
	*d = resultMap
	return err
}

// Value Implement driver.Valuer interface, Value returns Detail value
func (d Detail) Value() (driver.Value, error) {
	if len(d) == 0 {
		return nil, nil
	}
	return json.Marshal(d)
}

type PublishEventManger interface {
	Create(ctx context.Context, publishEvent PublishEvent) (int64, error)
}

type publishEventManager struct {
	DB *sqlx.DB
}

// NewPublishEventManger
func NewPublishEventManger() PublishEventManger {
	return &publishEventManager{
		DB: database.GetDefaultDBClient().DB,
	}
}

var _ PublishEventManger = publishEventManager{}

// Create  publish event
func (p publishEventManager) Create(ctx context.Context, publishEvent PublishEvent) (int64, error) {
	insertSql := `INSERT INTO core_publish_event (
        gateway_id, 
        publish_id, 
        stage_id,
        name,
        step, 
        status, 
        detail,
        created_time,
	updated_time                       
        )VALUES (:gateway_id, :publish_id, :stage_id, :name, :step, :status, :detail,:created_time,:updated_time)`
	query, args, err := sqlx.Named(insertSql, publishEvent)
	if err != nil {
		return 0, err
	}
	result, err := database.SqxExec(ctx, p.DB, query, args...)
	if err != nil {
		// make sure err is a mysql.MySQLError.
		if errMySQL, ok := err.(*mysql.MySQLError); ok {
			if errMySQL.Number == database.DuplicateErrCode {
				return 0, fmt.Errorf("insert event duplicated err: %w", err)
			}
		}
		return 0, fmt.Errorf("failed to insert publish event: %w", err)
	}
	return result.LastInsertId()
}
