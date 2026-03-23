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

package mcp

import (
	"context"

	sdkmcp "github.com/modelcontextprotocol/go-sdk/mcp"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/infra/proxy"
)

// ExtractToolNameForTest exposes extractToolName for testing.
func ExtractToolNameForTest(req sdkmcp.Request) string {
	return extractToolName(req)
}

// MatchErrorCodeNameForTest exposes matchErrorCodeName for testing.
func MatchErrorCodeNameForTest(code int64) string {
	return matchErrorCodeName(code)
}

// ShouldReportToSentryForTest exposes shouldReportToSentry for testing.
func ShouldReportToSentryForTest(err error) bool {
	return shouldReportToSentry(err)
}

// CheckNeedLoadForTest exposes checkNeedLoad for testing.
func CheckNeedLoadForTest(mcpProxy *proxy.MCPProxy, s *model.MCPServer, release *model.Release) bool {
	return checkNeedLoad(mcpProxy, s, release)
}

// CleanupAllMCPServersForTest exposes cleanupAllMCPServers for testing.
func CleanupAllMCPServersForTest(ctx context.Context, mcpProxy *proxy.MCPProxy) {
	cleanupAllMCPServers(ctx, mcpProxy)
}

// CleanupStaleMCPServersForTest exposes cleanupStaleMCPServers for testing.
func CleanupStaleMCPServersForTest(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	activeMcpServer map[string]struct{},
) int {
	return cleanupStaleMCPServers(ctx, mcpProxy, activeMcpServer)
}

// ServerLoadResult is an alias for serverLoadResult for testing.
type ServerLoadResult = serverLoadResult

// LoadStats is an alias for loadStats for testing.
type LoadStats = loadStats

// ApplyServerChangesForTest exposes applyServerChanges for testing.
func ApplyServerChangesForTest(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	results []*ServerLoadResult,
) (*loadStats, map[string]struct{}) {
	return applyServerChanges(ctx, mcpProxy, results)
}

// NewServerLoadResult creates a serverLoadResult for testing.
func NewServerLoadResult(
	server *model.MCPServer,
	release *model.Release,
	conf *Config,
	err error,
	skipped bool,
	isNew bool,
	needLoad bool,
) *ServerLoadResult {
	return &ServerLoadResult{
		server:   server,
		release:  release,
		conf:     conf,
		err:      err,
		skipped:  skipped,
		isNew:    isNew,
		needLoad: needLoad,
	}
}

// NewConfig creates a Config for testing.
func NewConfig(resourceVersion int) *Config {
	return &Config{
		resourceVersion: resourceVersion,
	}
}

// GetLoadStatsValues returns stats values for testing.
func GetLoadStatsValues(stats *loadStats) (added, updated, skipped, errorCount int) {
	return stats.addedCount, stats.updatedCount, stats.skippedCount, stats.errorCount
}

// PrefetchServerConfigsForTest exposes prefetchServerConfigs for benchmark testing.
func PrefetchServerConfigsForTest(
	ctx context.Context,
	mcpProxy *proxy.MCPProxy,
	servers []*model.MCPServer,
) []*ServerLoadResult {
	return prefetchServerConfigs(ctx, mcpProxy, servers)
}
