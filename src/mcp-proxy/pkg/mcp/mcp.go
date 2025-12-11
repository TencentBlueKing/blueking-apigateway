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

// Package mcp is the package for mcp server
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
		defer ticker.Stop() // 确保 ticker 被正确停止
		for {
			select {
			case <-ticker.C:
				logging.GetLogger().Infof("reload mcp server start")
				err := LoadMCPServer(ctx, m.proxy)
				if err != nil {
					logging.GetLogger().Errorf("reload mcp server error: %v", err)
					continue
				}
				logging.GetLogger().Infof("reload mcp server success")
			case <-ctx.Done():
				logging.GetLogger().Info("mcp server reload goroutine stopped due to context cancellation")
				return // ✅ 响应 context 取消，正确退出
			}
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
		// 查看每个mcp server当前生效的资源版本
		release, err := biz.GetRelease(ctx, server.GatewayID, server.StageID)
		if err != nil {
			logging.GetLogger().Errorf("get mcp server[%s] release error: %v", server.Name, err)
			continue
		}
		wouldReloadOpenapiSpec := true
		// 判断mcp server是否已经存在
		if mcpProxy.IsMCPServerExist(server.Name) {
			mcpServer := mcpProxy.GetMCPServer(server.Name)
			// 判断资源版本是否变化
			if mcpServer.GetResourceVersionID() == release.ResourceVersionID {
				logging.GetLogger().Debugf("mcp server[%s] version unchanged, skip reload yaml", server.Name)
				wouldReloadOpenapiSpec = false
			}
		}

		var conf *Config

		if wouldReloadOpenapiSpec {
			// 传入 release 避免重复查询
			conf, err = GetMCPServerConfigWithRelease(ctx, server, release)
			if err != nil {
				logging.GetLogger().Errorf("get mcp server[name:%s] openapi file error: %v", server.Name, err)
				continue
			}
		}

		// 如果mcp server不存在，添加mcp server
		if !mcpProxy.IsMCPServerExist(server.Name) && conf != nil {
			err = mcpProxy.AddMCPServerFromOpenAPISpec(server.Name,
				conf.resourceVersion, conf.openapiFileData, server.ResourceNames)
			if err != nil {
				logging.GetLogger().Errorf("add mcp server[name:%s] error: %v", server.Name, err)
				continue
			}
			logging.GetLogger().Infof("add  mcp server[%s] success", server.Name)
			continue
		}

		// 如果mcp server已经存在，判断mcp server的工具是否变化
		mcpServer := mcpProxy.GetMCPServer(server.Name)
		if mcpServer == nil {
			logging.GetLogger().Warnf("mcp server[%s] does not exist, skip tool cleanup", server.Name)
			continue
		}
		for _, tool := range mcpServer.GetTools() {
			// 如果当前mcp server的工具不在当前生效的资源列表中，删除该工具
			if !arrutil.Contains(server.ResourceNames, tool) {
				mcpServer.UnregisterTool(tool)
				continue
			}
		}

		// 如果资源版本发生变化，更新mcp server
		if wouldReloadOpenapiSpec && conf != nil {
			// 更新mcp server
			err = mcpProxy.UpdateMCPServerFromOpenApiSpec(mcpServer, server.Name, conf.resourceVersion,
				conf.openapiFileData, server.ResourceNames)
			if err != nil {
				return err
			}
			logging.GetLogger().Infof("update mcp server[%s] success", server.Name)
		}
	}
	// 删除已经不存在的mcp server
	for _, server := range mcpProxy.GetActiveMCPServerNames() {
		if _, ok := activeMcpServer[server]; !ok {
			mcpProxy.DeleteMCPServer(server)
		}
	}
	mcpProxy.Run(ctx)
	return nil
}

// GetMCPServerConfigWithRelease 使用已有的 release 信息获取配置，避免重复查询
func GetMCPServerConfigWithRelease(
	ctx context.Context,
	server *model.MCPServer,
	release *model.Release,
) (*Config, error) {
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
