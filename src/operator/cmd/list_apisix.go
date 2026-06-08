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
	"fmt"
	"reflect"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"operator/pkg/client"
)

type listApisixCommand struct {
	cmd *cobra.Command
}

var listApisixCmd = &listApisixCommand{}

func init() {
	listApisixCmd.Init()
}

// Init ...
func (l *listApisixCommand) Init() {
	cmd := &cobra.Command{
		Use:          "list-apisix",
		Short:        "list resources in apisix",
		SilenceUsage: true,
		PreRun:       preRun,
		RunE:         l.RunE,
	}

	cmd.Flags()
	cmd.Flags().String("gateway_name", "", "gateway name for list apisix command")
	cmd.Flags().String("stage_name", "", "stage name for list apisix command")
	cmd.Flags().Int64("resource_id", 0, "resource ID for list apisix command")
	cmd.Flags().String("resource_name", "", "resource name for list apisix command")
	cmd.Flags().StringP("write-out", "w", "json", "response write out format (simple, json, yaml)")
	cmd.Flags().Bool("count", false, "gateway resources count")
	cmd.Flags().Bool("current-version", false, "gateway stage version")
	_ = cmd.MarkFlagRequired("gateway_name")
	_ = cmd.MarkFlagRequired("stage_name")
	cmd.MarkFlagsMutuallyExclusive("resource_id", "resource_name")

	cmd.Flags().StringVarP(&cfgFile, "config", "c", "", "config file (default is config.yml;required)")
	cmd.PersistentFlags().Bool("viper", true, "Use Viper for configuration")

	_ = cmd.MarkFlagRequired("config")
	viper.SetDefault("author", "blueking-paas")

	rootCmd.AddCommand(cmd)
	l.cmd = cmd
}

// RunE ...
func (l *listApisixCommand) RunE(cmd *cobra.Command, args []string) error {
	initClient()

	cli, err := client.GetLeaderResourceClient(globalConfig.HttpServer.AuthPassword)
	if err != nil {
		logger.Infow("GetLeaderResourcesClient failed", "err", err)
		return err
	}
	if cli == nil {
		logger.Error(err, "GetLeaderResourcesClient failed")
		return err
	}

	gatewayName, _ := cmd.Flags().GetString("gateway_name")
	stageName, _ := cmd.Flags().GetString("stage_name")
	resourceName, _ := cmd.Flags().GetString("resource_name")
	resourceID, _ := cmd.Flags().GetInt64("resource_id")
	count, _ := cmd.Flags().GetBool("count")
	currentVersion, _ := cmd.Flags().GetBool("current-version")

	apisixListRequest := &client.ApisixListRequest{
		GatewayName: gatewayName,
		StageName:   stageName,
		Resource: &client.ResourceInfo{
			ID:   resourceID,
			Name: resourceName,
		},
	}
	// 查询指定环境下的资源数量
	if count {
		resp, err := cli.ApisixStageResourceCount(apisixListRequest)
		if err != nil {
			logger.Error(err, "apisix count request failed")
			return err
		}
		fmt.Printf("count: %d\n", resp.Count)
		return nil
	}
	// 查询指定环境下的发布版本信息
	if currentVersion {
		resp, err := cli.ApisixStageCurrentVersion(apisixListRequest)
		if err != nil {
			logger.Error(err, "apisix current-version request failed")
			return err
		}
		return printJson(resp)
	}
	// 查询指定环境下的资源列表
	resp, err := cli.ApisixList(apisixListRequest)
	if err != nil {
		logger.Error(err, "List apisix request failed")
		return err
	}
	format, _ := cmd.Flags().GetString("write-out")
	err = l.formatOutput(resp, format)
	if err != nil {
		logger.Error(err, "print resp failed")
		return err
	}
	return nil
}

func (l *listApisixCommand) formatOutput(apisixListInfo client.ApisixListInfo, format string) error {
	switch format {
	case "json":
		return printJson(apisixListInfo)
	case "yaml":
		return printYaml(apisixListInfo)
	case "simple":
		for stage, listResources := range apisixListInfo {
			fmt.Printf("Stage: %s\n", stage)
			l.printResource("Routes", listResources.Routes)
			l.printResource("Services", listResources.Services)
			l.printResource("PluginMetadatas", listResources.PluginMetadata)
			l.printResource("SSLs", listResources.SSLs)
		}
	}
	return nil
}

func (l *listApisixCommand) printResource(typeName string, fields any) {
	fmt.Printf("\t%s:\n", typeName)
	if fields == nil {
		return
	}

	// 使用反射来处理任意类型的 map[string]T
	rv := reflect.ValueOf(fields)
	if rv.Kind() != reflect.Map {
		return
	}

	// 遍历 map 的 keys
	for _, key := range rv.MapKeys() {
		fmt.Printf("\t\t%s\n", key.String())
	}
}
