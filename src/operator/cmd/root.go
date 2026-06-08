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
	"os"
	"time"

	sentry "github.com/getsentry/sentry-go"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"operator/pkg/core/runner"
	"operator/pkg/eventreporter"
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:    "bk-apigateway-operator",
	Short:  "bk-gateway operator for apisix",
	PreRun: preRun,
	Run:    rootRun,
}

func init() {
	rootCmd.Flags().StringVarP(&cfgFile, "config", "c", "", "config file (default is config.yml;required)")
	rootCmd.PersistentFlags().Bool("viper", true, "Use Viper for configuration")

	_ = rootCmd.MarkFlagRequired("config")
	viper.SetDefault("author", "blueking-paas")
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func rootRun(cmd *cobra.Command, args []string) {
	initOperator()
	gracefulShutdown(eventreporter.Shutdown)
	initTracing()

	// TODO sentry 相关的逻辑放到一起
	if len(globalConfig.Sentry.Dsn) != 0 {
		defer func() {
			sentry.Flush(2 * time.Second)
			sentry.Recover()
		}()
	}

	// start event reporter
	eventreporter.Start(rootCtx)

	// 只支持etcd模式，直接使用etcd运行器
	agentRunner := runner.NewEtcdAgentRunner(rootCtx, globalConfig)
	defer agentRunner.Close()
	agentRunner.Run(rootCtx)
}
