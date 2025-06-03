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

package mcp

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/gookit/goutil/arrutil"

	"mcp_proxy/pkg/biz"
	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/proxy"
	"mcp_proxy/pkg/util"
)

// Config ...
type Config struct {
	resourceVersion int
	openapiFileData *openapi3.T
}

// MCP ...
type MCP struct {
	proxy *proxy.MCPProxy
}

// Init ...
func Init(ctx context.Context, mcpProxy *proxy.MCPProxy) (*MCP, error) {
	// 查询当前所有配置的mcp server
	err := LoadMCPServer(ctx, mcpProxy)
	if err != nil {
		return nil, err
	}
	return &MCP{
		proxy: mcpProxy,
	}, nil
}

// Run ...
func (m *MCP) Run(ctx context.Context) *proxy.MCPProxy {
	ticker := time.NewTicker(config.G.McpServer.Interval)
	util.GoroutineWithRecovery(ctx, func() {
		for range ticker.C {
			logging.GetLogger().Infof("reload mcp server start")
			err := LoadMCPServer(ctx, m.proxy)
			if err != nil {
				logging.GetLogger().Errorf("reload mcp server error: %v", err)
				continue
			}
			logging.GetLogger().Infof("reload mcp server success")
		}
	})
	return m.proxy
}

// LoadMCPServer ...
func LoadMCPServer(ctx context.Context, mcpProxy *proxy.MCPProxy) error {
	servers, err := biz.GetAllActiveMCPServers(ctx)
	if err != nil {
		return err
	}

	activeMcpServer := make(map[string]struct{})
	for _, server := range servers {
		activeMcpServer[server.Name] = struct{}{}
		registeredToolMap := make(map[string]struct{})
		for _, tool := range server.ResourceNames {
			registeredToolMap[tool] = struct{}{}
		}
		conf, err := GetMCPServerConfig(ctx, server)
		if err != nil {
			logging.GetLogger().Errorf("get mcp server[name:%s] openapi file error: %v", server.Name, err)
			continue
		}
		if !mcpProxy.IsMCPServerExist(server.Name) {
			err = mcpProxy.AddMCPServerFromOpenApiSpec(server.Name, conf.openapiFileData, registeredToolMap)
			if err != nil {
				logging.GetLogger().Errorf("add mcp server[name:%s] error: %v", server.Name, err)
				continue
			}
			continue
		}
		mcpServer := mcpProxy.GetMCPServer(server.Name)
		for _, tool := range mcpServer.GetTools() {
			// 如果当前mcp server的工具不在当前生效的资源列表中，删除该工具
			if !arrutil.Contains(server.ResourceNames, tool) {
				mcpServer.UnregisterTool(tool)
				continue
			}
		}
		err = mcpProxy.AddMCPServerFromOpenApiSpec(server.Name, conf.openapiFileData, registeredToolMap)
		if err != nil {
			return err
		}
	}

	// 删除已经不存在的mcp server
	for _, server := range mcpProxy.GetActiveMCPServerNames() {
		if _, ok := activeMcpServer[server]; !ok {
			mcpProxy.DeleteMCPServer(server)
		}
	}
	// 启动所有的mcp server
	util.GoroutineWithRecovery(ctx, func() {
		mcpProxy.Run(ctx)
	})
	return nil
}

// GetMCPServerConfig ...
func GetMCPServerConfig(ctx context.Context, server *model.MCPServer) (*Config, error) {
	// 查看每个mcp server当前生效的资源版本
	release, err := biz.GetRelease(ctx, server.GatewayID, server.StageID)
	if err != nil {
		return nil, err
	}
	// 根据release查找当前生效的资源版本的openapi文件
	openapiFile, err := biz.GetOpenapiGatewayResourceVersionSpec(ctx, server.GatewayID, release.ResourceVersionID)
	if err != nil {
		return nil, err
	}
	// 根据openapi文件初始化mcp server的proxy
	openapiFileData, err := openapi3.NewLoader().LoadFromData([]byte(openapiFile.Schema))
	if err != nil {
		return nil, err
	}
	// 渲染openapi文件的server信息
	endpoint := fmt.Sprintf("%s/{stage}", strings.TrimSuffix(config.G.McpServer.BkApiUrlTmpl, "/"))
	gateway, err := cacheimpls.GetGatewayByID(ctx, server.GatewayID)
	if err != nil {
		logging.GetLogger().Errorf("get gateway[id:%d] error: %v", server.GatewayID, err)
		return nil, err
	}
	stage, err := cacheimpls.GetStageByID(ctx, server.StageID)
	if err != nil {
		logging.GetLogger().Errorf("get stage[id:%d] error: %v", server.StageID, err)
		return nil, err
	}
	openapiFileData.Servers = []*openapi3.Server{{
		URL: util.ReplacePlaceHolder(endpoint, map[string]string{
			"api_name": gateway.Name,
			"stage":    stage.Name,
		}),
	}}
	return &Config{
		resourceVersion: release.ResourceVersionID,
		openapiFileData: openapiFileData,
	}, nil
}
