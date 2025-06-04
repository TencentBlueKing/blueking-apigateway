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

// Package cmd is the package for cmd
package cmd

import (
	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"mcp_proxy/pkg/entity/model"
)

// NewGenCmd ...
func NewGenCmd() *cobra.Command {
	migrateCmd := cobra.Command{
		Use:   "gen",
		Short: "gen dao code",
		Run: func(cmd *cobra.Command, args []string) {
			if cfgFile != "" {
				viper.SetConfigFile(cfgFile)
			}
			initConfig()
			initDatabase()
			// 生成模型的crud代码
			model.RunGenDao()
		},
	}

	// 配置文件路径，如果未指定，会从环境变量读取各项配置
	// 注意：目前平台未默认提供配置文件，需通过 `模块配置 - 挂载卷` 添加
	migrateCmd.Flags().StringVarP(&cfgFile, "config", "c", "", "config file (default is config.yml;required)")
	return &migrateCmd
}

func init() {
	rootCmd.AddCommand(NewGenCmd())
}
