/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

// Package cmd ...
package cmd

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/getsentry/sentry-go"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"go.uber.org/zap"

	"operator/pkg/client"
	"operator/pkg/config"
	"operator/pkg/core/agent"
	"operator/pkg/core/synchronizer"
	"operator/pkg/eventreporter"
	"operator/pkg/logging"
	"operator/pkg/trace"
)

var (
	rootCtx, cancel = context.WithCancel(context.Background())
	logger          *zap.SugaredLogger
)

var (
	cfgFile      string
	globalConfig *config.Config
)

// initConfig init config from args or config file
func initConfig() {
	// 0. init config
	if cfgFile != "" {
		// Use config file from the flag.
		viper.SetConfigFile(cfgFile)
	} else {
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

func initSentry() {
	if len(globalConfig.Sentry.Dsn) != 0 {
		err := sentry.Init(sentry.ClientOptions{
			Dsn: globalConfig.Sentry.Dsn,
		})
		if err != nil {
			logging.GetLogger().Errorf("init Sentry fail: %s", err)
			return
		}
		logging.GetLogger().Info("init Sentry success")
	} else {
		logging.GetLogger().Info("Sentry is not enabled, will not init it")
	}
}

// initLog init logger must after initConfig
func initLog() {
	logging.Init(globalConfig)
	logger = logging.GetLogger().Named("setup")
}

func initTracing() {
	if err := trace.InitTrace(globalConfig.Tracing, config.InstanceName); err != nil {
		logger.Errorw("failed to init tracing", "err", err)
	}
}

func gracefulShutdown(shutdownHookFuncOptions ...func()) {
	c := make(chan os.Signal, 2)
	signal.Notify(c, syscall.SIGTERM, syscall.SIGINT)
	go func() {
		select {
		case sig := <-c:
			logger.Infow("Got signal. Aborting...", "sig", sig)
			cancel() // Gracefully shut down before listening to the context signal
			for _, shutdown := range shutdownHookFuncOptions {
				shutdown() // Suitable for those who need to process the data before closing
			}
			time.Sleep(time.Second * 3)
			os.Exit(1)
		case <-rootCtx.Done():
			logger.Info("root context canceled")
			time.Sleep(time.Second * 3)
			os.Exit(1)
		}
	}()
}

func preRun(cmd *cobra.Command, args []string) {
	_ = cmd.ParseFlags(args)
	initConfig()
	initSentry()
	initLog()
	initClient()
	// init publish reporter
	eventreporter.InitReporter(globalConfig)
}

func initClient() {
	client.InitResourceClient(globalConfig)
	client.InitCoreAPIClient(globalConfig)
	client.InitApisixClient(globalConfig)
}

func initOperator() {
	synchronizer.Init(globalConfig)
	agent.Init(globalConfig)
}
