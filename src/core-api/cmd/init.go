/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

package cmd

import (
	"fmt"

	"github.com/spf13/viper"

	"core/pkg/config"
	"core/pkg/database"
	"core/pkg/logging"
	"core/pkg/metric"
	sty "core/pkg/sentry"
	"core/pkg/trace"
)

var globalConfig *config.Config

// initConfig reads in config file and ENV variables if set.
func initConfig() {
	if cfgFile == "" {
		panic("Config file missing")
	}
	// Use config file from the flag.
	// viper.SetConfigFile(cfgFile)
	// If a config file is found, read it in.
	if err := viper.ReadInConfig(); err != nil {
		panic(fmt.Sprintf("Using config file: %s, read fail: err=%v", viper.ConfigFileUsed(), err))
	}
	var err error
	globalConfig, err = config.Load(viper.GetViper())
	if err != nil {
		panic(fmt.Sprintf("Could not load configurations from file, error: %v", err))
	}
}

func initLogger() {
	logging.InitLogger(globalConfig)
}

func initDatabase() {
	defaultDBConfig, ok := globalConfig.DatabaseMap["apigateway"]
	if !ok {
		panic("database apigateway should be configured")
	}

	database.InitDBClients(&defaultDBConfig, globalConfig.Tracing)

	logging.GetLogger().Info("init Database success")
}

func initSentry() {
	err := sty.Init(globalConfig.Sentry)
	if err != nil {
		logging.GetLogger().Errorf("init Sentry fail: %s", err)
	} else {
		logging.GetLogger().Info("init Sentry success")
	}
}

func initMetrics() {
	metric.InitMetrics()
	logging.GetLogger().Info("init Metrics success")
}

func initTracing() {
	if !globalConfig.Tracing.Enable {
		logging.GetLogger().Info("tracing is not enabled, will not init it")
		return
	}
	logging.GetLogger().Info("enabling tracing")
	err := trace.InitTrace(globalConfig.Tracing)
	if err != nil {
		logging.GetLogger().Errorf("init tracing fail: %+v", err)
		return
	}
	logging.GetLogger().Info("init tracing success")
}
