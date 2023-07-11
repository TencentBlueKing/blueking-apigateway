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
	"fmt"
	"net/url"
	"time"

	"core/pkg/config"
	"core/pkg/logging"

	"github.com/jmoiron/sqlx"
	"github.com/uptrace/opentelemetry-go-extra/otelsql"
	"github.com/uptrace/opentelemetry-go-extra/otelsqlx"
	semconv "go.opentelemetry.io/otel/semconv/v1.10.0"
)

// ! set the default https://making.pusher.com/production-ready-connection-pooling-in-go/
// https://www.alexedwards.net/blog/configuring-sqldb
// SetMaxOpenConns
// SetMaxIdleConns
// SetConnMaxLifetime
const (
	// maxOpenConns >= maxIdleConns

	defaultMaxOpenConns    = 100
	defaultMaxIdleConns    = 25
	defaultConnMaxLifetime = 10 * time.Minute
)

const (
	// sql errCode
	DuplicateErrCode uint16 = 1062
)

// DBClient MySQL DB Instance
type DBClient struct {
	name string

	DB *sqlx.DB

	dataSource string

	maxOpenConns    int
	maxIdleConns    int
	connMaxLifetime time.Duration
	traceEnabled    bool
}

// TestConnection ...
func (db *DBClient) TestConnection() (err error) {
	conn, err := sqlx.Connect("mysql", db.dataSource)
	if err != nil {
		return
	}

	conn.Close()
	return nil
}

// Connect connect to db, and update some settings
func (db *DBClient) Connect() error {
	var err error
	if db.traceEnabled {
		db.DB, err = otelsqlx.Open("mysql", db.dataSource,
			otelsql.WithAttributes(semconv.DBSystemMySQL),
			otelsql.WithDBName(db.name),
		)
	} else {
		db.DB, err = sqlx.Connect("mysql", db.dataSource)
	}
	if err != nil {
		return err
	}
	db.DB.SetMaxOpenConns(db.maxOpenConns)
	db.DB.SetMaxIdleConns(db.maxIdleConns)
	db.DB.SetConnMaxLifetime(db.connMaxLifetime)

	_, err = db.DB.Exec(`SET time_zone = "+00:00";`) // set session time zon to utc
	if err != nil {
		return err
	}

	logging.GetLogger().Infof("connect to database: %s[maxOpenConns=%d, maxIdleConns=%d, connMaxLifetime=%s]",
		db.name, db.maxOpenConns, db.maxIdleConns, db.connMaxLifetime)

	return nil
}

// SetTraceEnabled Set db trace
func (db *DBClient) SetTraceEnabled(enabled bool) {
	db.traceEnabled = enabled
}

// Close close db connection
func (db *DBClient) Close() {
	if db.DB != nil {
		db.DB.Close()
	}
}

// NewDBClient :
func NewDBClient(cfg *config.Database) *DBClient {
	dataSource := fmt.Sprintf("%s:%s@(%s:%d)/%s?charset=%s&parseTime=True&interpolateParams=true&loc=%s&time_zone=%s",
		cfg.User,
		cfg.Password,
		cfg.Host,
		cfg.Port,
		cfg.Name,
		"utf8",
		"UTC",
		url.QueryEscape("'+00:00'"),
	)

	maxOpenConns := defaultMaxOpenConns
	if cfg.MaxOpenConns > 0 {
		maxOpenConns = cfg.MaxOpenConns
	}

	maxIdleConns := defaultMaxIdleConns
	if cfg.MaxIdleConns > 0 {
		maxIdleConns = cfg.MaxIdleConns
	}

	if maxOpenConns < maxIdleConns {
		logging.GetLogger().
			Errorf("error config for database %s, maxOpenConns should greater or equals to maxIdleConns, will"+
				"use the default [defaultMaxOpenConns=%d, defaultMaxIdleConns=%d]",
				cfg.Name, defaultMaxOpenConns, defaultMaxIdleConns)
		maxOpenConns = defaultMaxOpenConns
		maxIdleConns = defaultMaxIdleConns
	}

	connMaxLifetime := defaultConnMaxLifetime
	if cfg.ConnMaxLifetimeSecond > 0 {
		if cfg.ConnMaxLifetimeSecond >= 60 {
			connMaxLifetime = time.Duration(cfg.ConnMaxLifetimeSecond) * time.Second
		} else {
			logging.GetLogger().Errorf("error config for database %s, connMaxLifetimeSeconds should be greater than 60 seconds"+
				"use the default [defaultConnMaxLifetime=%s]",
				cfg.Name, defaultConnMaxLifetime)
		}
	}

	return &DBClient{
		name:            cfg.Name,
		dataSource:      dataSource,
		maxOpenConns:    maxOpenConns,
		maxIdleConns:    maxIdleConns,
		connMaxLifetime: connMaxLifetime,
	}
}
