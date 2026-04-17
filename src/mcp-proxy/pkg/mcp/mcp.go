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
	"sync"
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
	initStart := time.Now()
	logging.GetLogger().Info("mcp server init start")

	// 查询当前所有配置的mcp server
	err := LoadMCPServer(ctx, mcpProxy)
	if err != nil {
		return nil, err
	}

	logging.GetLogger().Infof("mcp server init complete, duration=%s", time.Since(initStart))
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
				reloadStart := time.Now()
				logging.GetLogger().Info("reload mcp server start")
				err := LoadMCPServer(ctx, m.proxy)
				if err != nil {
					logging.GetLogger().Errorf("reload mcp server error: %v, duration=%s",
						err, time.Since(reloadStart))
					continue
				}
				logging.GetLogger().Infof("reload mcp server success, duration=%s", time.Since(reloadStart))
			case <-ctx.Done():
				logging.GetLogger().Info("mcp server reload goroutine stopped due to context cancellation")
				return // ✅ 响应 context 取消，正确退出
			}
		}
	})
	return m.proxy
}

// serverLoadResult 保存并发加载单个 server 的配置结果
type serverLoadResult struct {
	server   *model.MCPServer
	release  *model.Release
	conf     *Config
	err      error
	skipped  bool // 标记版本未变化、无需重新加载的 server
	isNew    bool // 标记是否为新增的 server
	needLoad bool // 标记是否需要加载 openapi spec
}

// loadStats 记录 LoadMCPServer 各阶段的统计数据
type loadStats struct {
	addedCount   int
	updatedCount int
	skippedCount int
	errorCount   int
}

// LoadMCPServer ...
func LoadMCPServer(ctx context.Context, mcpProxy *proxy.MCPProxy) error {
	loadStart := time.Now()

	dbStart := time.Now()
	servers, err := biz.GetAllActiveMCPServers(ctx)
	if err != nil {
		return err
	}
	logging.GetLogger().Infof("loaded %d active mcp servers from db, duration=%s",
		len(servers), time.Since(dbStart))

	if len(servers) == 0 {
		cleanupAllMCPServers(ctx, mcpProxy)
		mcpProxy.Run(ctx)
		logging.GetLogger().Infof("no active mcp servers, cleanup complete, duration=%s", time.Since(loadStart))
		return nil
	}

	// Phase 1: 并发预取 release + openapi spec（IO 密集型，适合并发）
	results := prefetchServerConfigs(ctx, mcpProxy, servers)
	logging.GetLogger().Infof("mcp server concurrent prefetch complete, duration=%s", time.Since(dbStart))

	// Phase 2: 串行应用变更（涉及 mcpProxy 的写操作，需要保证线程安全）
	stats, activeMcpServer := applyServerChanges(ctx, mcpProxy, results)

	// 删除已经不存在的mcp server
	deletedCount := cleanupStaleMCPServers(ctx, mcpProxy, activeMcpServer)
	mcpProxy.Run(ctx)

	logging.GetLogger().Infof(
		"load mcp server complete: total=%d, added=%d, updated=%d, skipped=%d, deleted=%d, error=%d, duration=%s",
		len(servers), stats.addedCount, stats.updatedCount, stats.skippedCount,
		deletedCount, stats.errorCount, time.Since(loadStart))
	return nil
}

// cleanupAllMCPServers 清理所有已有的 mcp server
func cleanupAllMCPServers(ctx context.Context, mcpProxy *proxy.MCPProxy) {
	names := mcpProxy.CleanupAll()
	for _, name := range names {
		if err := cacheimpls.DeleteMCPServerCache(ctx, name); err != nil {
			logging.GetLogger().Warnf("delete mcp server[%s] cache error: %v", name, err)
		}
	}
}

// prefetchServerConfigs 并发预取所有 server 的 release 和 openapi spec。
// 使用 config.G.McpServer.MaxConcurrentPrefetch 限制并发数（默认 20），
// 避免在 server 数量较多时导致数据库连接池耗尽。
func prefetchServerConfigs(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	servers []*model.MCPServer,
) []*serverLoadResult {
	results := make([]*serverLoadResult, len(servers))
	var wg sync.WaitGroup

	// 使用 buffered channel 作为 semaphore 限制并发数
	maxConcurrent := config.G.McpServer.MaxConcurrentPrefetch
	sem := make(chan struct{}, maxConcurrent)

	for i, svr := range servers {
		results[i] = &serverLoadResult{server: svr}
		wg.Add(1)
		idx, s := i, svr
		util.GoroutineWithRecovery(ctx, func() {
			defer wg.Done()
			sem <- struct{}{}        // acquire
			defer func() { <-sem }() // release
			prefetchSingleServer(ctx, mcpProxy, results[idx], s)
		})
	}
	wg.Wait()
	return results
}

// prefetchSingleServer 预取单个 server 的 release 和 openapi spec
func prefetchSingleServer(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	result *serverLoadResult,
	s *model.MCPServer,
) {
	// 获取 release
	releaseStart := time.Now()
	release, releaseErr := biz.GetRelease(ctx, s.GatewayID, s.StageID)
	if releaseErr != nil {
		result.err = fmt.Errorf("get release error: %w", releaseErr)
		logging.GetLogger().Errorf("mcp server[%s] prefetch failed: %v", s.Name, result.err)
		return
	}
	result.release = release
	logging.GetLogger().Debugf("mcp server[%s] get release duration=%s",
		s.Name, time.Since(releaseStart))

	result.isNew = !mcpProxy.IsMCPServerExist(s.Name)
	result.needLoad = checkNeedLoad(mcpProxy, s, release)

	if !result.needLoad {
		result.skipped = true
		return
	}

	// 加载 openapi spec
	specStart := time.Now()
	conf, confErr := GetMCPServerConfigWithRelease(ctx, s, release)
	if confErr != nil {
		result.err = fmt.Errorf("get openapi spec error: %w", confErr)
		logging.GetLogger().Errorf("mcp server[%s] prefetch failed: %v", s.Name, result.err)
		return
	}
	result.conf = conf
	logging.GetLogger().Debugf("mcp server[%s] load openapi spec duration=%s",
		s.Name, time.Since(specStart))
}

// checkNeedLoad 检查是否需要重新加载 openapi spec
func checkNeedLoad(mcpProxy *proxy.MCPProxy, s *model.MCPServer, release *model.Release) bool {
	if !mcpProxy.IsMCPServerExist(s.Name) {
		return true
	}

	mcpServer := mcpProxy.GetMCPServer(s.Name)
	// 协议类型变化，需要重建
	if mcpServer.GetProtocolType() != s.GetProtocolType() {
		logging.GetLogger().Infof(
			"mcp server[%s] protocol type changed from %s to %s, will recreate",
			s.Name, mcpServer.GetProtocolType(), s.GetProtocolType())
		return true
	}

	// 资源版本变化，需要重新加载
	if mcpServer.GetResourceVersionID() != release.ResourceVersionID {
		return true
	}

	// 版本未变化，检查是否有新增工具（使用 map 进行 O(1) 查找）
	currentToolSet := make(map[string]struct{}, len(mcpServer.GetTools()))
	for _, t := range mcpServer.GetTools() {
		currentToolSet[t] = struct{}{}
	}
	for _, toolName := range s.GetToolNames() {
		if _, exists := currentToolSet[toolName]; !exists {
			logging.GetLogger().Infof(
				"mcp server[%s] resource_names changed, will reload openapi spec", s.Name)
			return true
		}
	}

	logging.GetLogger().Debugf("mcp server[%s] version unchanged, skip reload", s.Name)
	return false
}

// applyServerChanges 串行应用所有 server 的变更
func applyServerChanges(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	results []*serverLoadResult,
) (*loadStats, map[string]struct{}) {
	activeMcpServer := make(map[string]struct{})
	stats := &loadStats{}

	for _, result := range results {
		svr := result.server
		activeMcpServer[svr.Name] = struct{}{}

		if result.err != nil {
			logging.GetLogger().Errorf("mcp server[%s] load failed: %v", svr.Name, result.err)
			stats.errorCount++
			continue
		}

		// 处理协议类型变化（需要在主线程中执行 delete）
		if mcpProxy.IsMCPServerExist(svr.Name) {
			existingServer := mcpProxy.GetMCPServer(svr.Name)
			if existingServer.GetProtocolType() != svr.GetProtocolType() {
				mcpProxy.DeleteMCPServer(svr.Name)
			}
		}

		// 如果不需要重新加载 openapi spec（版本未变化）
		if result.skipped {
			prompts := loadMCPServerPrompts(ctx, svr.ID)
			mcpProxy.UpdateMCPServerPrompts(svr.Name, prompts)
			stats.skippedCount++
			continue
		}

		// 如果mcp server不存在，添加mcp server
		if !mcpProxy.IsMCPServerExist(svr.Name) && result.conf != nil {
			if addMCPServer(ctx, mcpProxy, svr, result.conf) {
				stats.addedCount++
			} else {
				stats.errorCount++
			}
			continue
		}

		// 如果mcp server已经存在，更新mcp server
		if updateMCPServer(ctx, mcpProxy, svr, result.conf) {
			stats.updatedCount++
		} else {
			stats.skippedCount++
		}
	}

	return stats, activeMcpServer
}

// addMCPServer 添加新的 mcp server，返回是否成功
func addMCPServer(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	svr *model.MCPServer,
	conf *Config,
) bool {
	addStart := time.Now()
	resourceNames := svr.GetResourceNames()

	err := mcpProxy.AddMCPServerFromOpenAPISpec(
		svr.Name, conf.resourceVersion, conf.openapiFileData,
		resourceNames, svr.GetToolNameMap(), svr.GetProtocolType(), svr.RawResponse,
	)
	if err != nil {
		logging.GetLogger().Errorf("add mcp server[name:%s] error: %v", svr.Name, err)
		return false
	}

	// Add logging, metric, and session metric middlewares
	mcpServer := mcpProxy.GetMCPServer(svr.Name)
	if mcpServer != nil {
		AddLoggingMiddleware(mcpServer.GetServer(), svr.Name)
		AddMetricMiddleware(mcpServer.GetServer(), svr.Name)
		AddSessionMetricMiddleware(mcpServer.GetServer(), svr.Name)
		// Add tracing middleware if MCP tracing is enabled
		if config.G.Tracing.McpAPIEnabled() {
			AddTracingMiddleware(mcpServer.GetServer(), svr.Name)
		}
	}

	// 加载并注册 Prompts
	prompts := loadMCPServerPrompts(ctx, svr.ID)
	if len(prompts) > 0 {
		mcpProxy.RegisterPromptsToMCPServer(svr.Name, prompts)
	}
	logging.GetLogger().Infof(
		"add mcp server[%s] protocol:%s, tool:%d, prompt:%d, duration=%s",
		svr.Name, svr.GetProtocolType(), len(resourceNames), len(prompts), time.Since(addStart))
	return true
}

// updateMCPServer 更新已存在的 mcp server，返回是否有实际变更
func updateMCPServer(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	svr *model.MCPServer,
	conf *Config,
) bool {
	mcpServer := mcpProxy.GetMCPServer(svr.Name)
	if mcpServer == nil {
		logging.GetLogger().Warnf("mcp server[%s] does not exist, skip tool cleanup", svr.Name)
		return false
	}

	toolNames := svr.GetToolNames()
	var toolUpdated bool
	for _, tool := range mcpServer.GetTools() {
		if !arrutil.Contains(toolNames, tool) {
			mcpServer.RemoveTool(tool)
			toolUpdated = true
		}
	}

	var resourceVersionUpdated bool
	if conf != nil {
		err := mcpProxy.UpdateMCPServerFromOpenApiSpec(mcpServer, svr.Name, conf.resourceVersion,
			conf.openapiFileData, svr.GetResourceNames(), svr.GetToolNameMap())
		if err != nil {
			logging.GetLogger().Errorf("update mcp server[%s] from openapi spec error: %v", svr.Name, err)
			return false
		}
		resourceVersionUpdated = true
	}

	// 更新 Prompts（每次都检查更新）
	prompts := loadMCPServerPrompts(ctx, svr.ID)
	mcpProxy.UpdateMCPServerPrompts(svr.Name, prompts)

	if toolUpdated || resourceVersionUpdated {
		logging.GetLogger().Infof(
			"updated prompts:%d, tools_changed:%v, resource_version_changed:%v for mcp server[%s]",
			len(prompts), toolUpdated, resourceVersionUpdated, svr.Name)
		return true
	}
	return false
}

// cleanupStaleMCPServers 删除已经不存在的 mcp server，返回删除数量
func cleanupStaleMCPServers(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	activeMcpServer map[string]struct{},
) int {
	names := mcpProxy.CleanupStale(activeMcpServer)
	for _, name := range names {
		if err := cacheimpls.DeleteMCPServerCache(ctx, name); err != nil {
			logging.GetLogger().Warnf("delete mcp server[%s] cache error: %v", name, err)
		}
	}
	return len(names)
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

// loadMCPServerPrompts 加载 MCP Server 的 Prompts 配置
func loadMCPServerPrompts(ctx context.Context, mcpServerID int) []*proxy.PromptConfig {
	prompts, err := biz.GetMCPServerPrompts(ctx, mcpServerID)
	if err != nil {
		logging.GetLogger().Errorf("get mcp server[id:%d] prompts error: %v", mcpServerID, err)
		return []*proxy.PromptConfig{}
	}
	if len(prompts) == 0 {
		return []*proxy.PromptConfig{}
	}

	result := make([]*proxy.PromptConfig, 0, len(prompts))
	for _, p := range prompts {
		result = append(result, &proxy.PromptConfig{
			Name:        p.Code,
			Description: p.Name,
			Content:     p.Content,
		})
	}
	return result
}
