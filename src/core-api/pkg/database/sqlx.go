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

package database

import (
	"time"

	"github.com/jmoiron/sqlx"
)

type queryFunc func(db *sqlx.DB, dest interface{}, query string, args ...interface{}) error

func queryTimer(f queryFunc) queryFunc {
	return func(db *sqlx.DB, dest interface{}, query string, args ...interface{}) error {
		start := time.Now()
		defer logSlowSQL(start, query, args)
		// NOTE: must be args...
		return f(db, dest, query, args...)
	}
}

func sqlxSelectFunc(db *sqlx.DB, dest interface{}, query string, args ...interface{}) error {
	query, args, err := sqlx.In(query, args...)
	if err != nil {
		return err
	}
	err = db.Select(dest, query, args...)
	return err
}

func sqlxGetFunc(db *sqlx.DB, dest interface{}, query string, args ...interface{}) error {
	query, args, err := sqlx.In(query, args...)
	if err != nil {
		return err
	}
	err = db.Get(dest, query, args...)

	if err == nil {
		return nil
	}

	return err
}

// note: if you want to add more functions, please take a look at
//       https://github.com/TencentBlueKing/bk-iam/blob/master/pkg/database/sqlx.go

// SqlxSelect ...
var (
	SqlxSelect = queryTimer(sqlxSelectFunc)
	SqlxGet    = queryTimer(sqlxGetFunc)
)
