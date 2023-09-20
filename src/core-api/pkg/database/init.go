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
	"sync"

	"github.com/dlmiddlecote/sqlstats"
	"github.com/jmoiron/sqlx"
	"github.com/prometheus/client_golang/prometheus"

	"core/pkg/config"
)

// NOTE: 独立/原子/单一

// DefaultDBClient ...
var (
	// DefaultDBClient 默认DB实例
	DefaultDBClient *DBClient
)

var defaultDBClientOnce sync.Once

// InitDBClients ...
func InitDBClients(defaultDBConfig *config.Database, tracerConfig config.Tracing) {
	if DefaultDBClient == nil {
		defaultDBClientOnce.Do(func() {
			DefaultDBClient = NewDBClient(defaultDBConfig)
			// set db trace
			DefaultDBClient.SetTraceEnabled(tracerConfig.DBAPIEnabled())
			if err := DefaultDBClient.Connect(); err != nil {
				panic(err)
			}

			// https://github.com/dlmiddlecote/sqlstats
			// Create a new collector, the name will be used as a label on the metrics
			collector := sqlstats.NewStatsCollector(defaultDBConfig.Name, DefaultDBClient.DB)
			// Register it with Prometheus
			prometheus.MustRegister(collector)
		})
	}
}

// GetDefaultDBClient 获取默认的DB实例
func GetDefaultDBClient() *DBClient {
	return DefaultDBClient
}

// GenerateDefaultDBTx ...
func GenerateDefaultDBTx() (*sqlx.Tx, error) {
	return GetDefaultDBClient().DB.Beginx()
}
