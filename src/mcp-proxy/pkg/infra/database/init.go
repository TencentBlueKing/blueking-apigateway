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
	"context"
	"database/sql"
	"log"
	"sync"
	"time"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
	"gorm.io/plugin/opentelemetry/tracing"

	"mcp_proxy/pkg/config"
)

var db *gorm.DB

var initOnce sync.Once

const (
	// string 类型字段的默认长度
	defaultStringSize = 256
	// 默认批量创建数量
	defaultBatchSize = 100
	// 默认最大空闲连接
	defaultMaxIdleConns = 20
	// 默认最大连接数
	defaultMaxOpenConns = 100
)

// Client 获取数据库客户端
func Client() *gorm.DB {
	if db == nil {
		log.Fatalf("database client not init")
	}
	return db
}

// SetClient 设置数据库客户端(only for test)
func SetClient(client *gorm.DB) {
	db = client
}

// InitDBClient 初始化数据库客户端
func InitDBClient(cfg *config.Database) {
	if db != nil {
		return
	}
	if cfg == nil {
		log.Fatalf("mysql config is required when init database client")
	}
	initOnce.Do(func() {
		var err error
		if db, err = newClient(cfg); err != nil {
			log.Fatalf("failed to connect database %s: %s", cfg.DSN(), err)
		} else {
			log.Printf("database: %s connected\n", cfg.DSN())
		}
	})
}

// 初始化 DB Client
func newClient(cfg *config.Database) (*gorm.DB, error) {
	sqlDB, err := sql.Open("mysql", cfg.DSN())
	if err != nil {
		return nil, err
	}
	sqlDB.SetMaxIdleConns(defaultMaxIdleConns)
	sqlDB.SetMaxOpenConns(defaultMaxOpenConns)
	sqlDB.SetConnMaxLifetime(time.Hour)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 检查 DB 是否可用
	if err = sqlDB.PingContext(ctx); err != nil {
		return nil, err
	}

	mysqlCfg := mysql.Config{
		DSN:                       cfg.DSN(),
		DefaultStringSize:         defaultStringSize,
		SkipInitializeWithVersion: false,
	}
	gormCfg := &gorm.Config{
		ConnPool: sqlDB,
		// 禁用默认事务（需要手动管理）
		SkipDefaultTransaction: true,
		// 缓存预编译语句
		PrepareStmt: true,
		// Mysql 本身即不支持嵌套事务
		DisableNestedTransaction: true,
		// 批量操作数量
		CreateBatchSize: defaultBatchSize,
		// 数据库迁移时，忽略外键约束
		DisableForeignKeyConstraintWhenMigrating: true,
	}
	client, err := gorm.Open(mysql.New(mysqlCfg), gormCfg)
	if err != nil {
		return nil, err
	}

	if config.G.Tracing.DBAPIEnabled() {
		err = client.Use(tracing.NewPlugin())
		if err != nil {
			return client, err
		}
	}

	return client, nil
}
