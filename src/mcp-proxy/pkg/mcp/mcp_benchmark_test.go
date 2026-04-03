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

package mcp_test

import (
	"context"
	"fmt"
	"testing"

	"github.com/getkin/kin-openapi/openapi3"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/infra/proxy"
	mcppkg "mcp_proxy/pkg/mcp"
)

// ---------- helpers ----------

func init() {
	// Ensure logger + global config are initialized for benchmarks
	// (when running `go test -bench` directly without Ginkgo suite)
	if config.G == nil {
		// Use "fatal" level to suppress log output in benchmarks, avoiding I/O noise
		cfg := &config.Config{}
		cfg.Logger.Default.Level = "fatal"
		cfg.Logger.API.Level = "fatal"
		cfg.Logger.Audit.Level = "fatal"
		logging.InitLogger(cfg)
		config.G = cfg
		config.G.McpServer.MaxConcurrentPrefetch = 20
	}
}

// buildOpenAPISpec creates a minimal OpenAPI 3.0 spec with the given number of operations.
func buildOpenAPISpec(numOps int) *openapi3.T {
	spec := &openapi3.T{
		OpenAPI: "3.0.0",
		Info:    &openapi3.Info{Title: "Bench API", Version: "1.0.0"},
		Servers: []*openapi3.Server{{URL: "https://api.bench.local"}},
		Paths:   &openapi3.Paths{},
	}
	for i := 0; i < numOps; i++ {
		pathItem := &openapi3.PathItem{
			Get: &openapi3.Operation{
				OperationID: fmt.Sprintf("op_%d", i),
				Summary:     fmt.Sprintf("Operation %d", i),
				Responses:   &openapi3.Responses{},
			},
		}
		spec.Paths.Set(fmt.Sprintf("/resource_%d", i), pathItem)
	}
	return spec
}

// operationIDs returns a slice of operation IDs: ["op_0", "op_1", ..., "op_{n-1}"]
func operationIDs(n int) []string {
	ids := make([]string, n)
	for i := 0; i < n; i++ {
		ids[i] = fmt.Sprintf("op_%d", i)
	}
	return ids
}

// setupProxyWithServers pre-populates an MCPProxy with `count` MCP servers,
// each having `toolsPerServer` tools and the given resource version.
func setupProxyWithServers(count, toolsPerServer, resourceVersion int) *proxy.MCPProxy {
	p := proxy.NewMCPProxy("", "")
	spec := buildOpenAPISpec(toolsPerServer)
	ops := operationIDs(toolsPerServer)
	for i := 0; i < count; i++ {
		name := fmt.Sprintf("server_%d", i)
		_ = p.AddMCPServerFromOpenAPISpec(name, resourceVersion, spec, ops, nil, constant.MCPServerProtocolTypeSSE)
	}
	return p
}

// ---------- Benchmark: checkNeedLoad ----------

// BenchmarkCheckNeedLoad_NoChange benchmarks checkNeedLoad when version & tools are unchanged (fast path).
func BenchmarkCheckNeedLoad_NoChange(b *testing.B) {
	for _, numTools := range []int{5, 20, 50, 100} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			p := setupProxyWithServers(1, numTools, 1)
			toolNames := make(model.ArrayString, numTools)
			for i := 0; i < numTools; i++ {
				toolNames[i] = fmt.Sprintf("op_%d", i)
			}
			server := &model.MCPServer{
				Name:          "server_0",
				ResourceNames: toolNames,
				ProtocolType:  constant.MCPServerProtocolTypeSSE,
			}
			release := &model.Release{ResourceVersionID: 1}

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				mcppkg.CheckNeedLoadForTest(p, server, release)
			}
		})
	}
}

// BenchmarkCheckNeedLoad_VersionChanged benchmarks checkNeedLoad when the resource version differs.
func BenchmarkCheckNeedLoad_VersionChanged(b *testing.B) {
	for _, numTools := range []int{5, 20, 50, 100} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			p := setupProxyWithServers(1, numTools, 1)
			server := &model.MCPServer{
				Name:         "server_0",
				ProtocolType: constant.MCPServerProtocolTypeSSE,
			}
			release := &model.Release{ResourceVersionID: 999} // different version

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				mcppkg.CheckNeedLoadForTest(p, server, release)
			}
		})
	}
}

// BenchmarkCheckNeedLoad_NewTool benchmarks checkNeedLoad when a new tool is added (same version).
func BenchmarkCheckNeedLoad_NewTool(b *testing.B) {
	for _, numTools := range []int{5, 20, 50, 100} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			p := setupProxyWithServers(1, numTools, 1)
			// Existing tools + one new tool
			toolNames := make(model.ArrayString, numTools+1)
			for i := 0; i < numTools; i++ {
				toolNames[i] = fmt.Sprintf("op_%d", i)
			}
			toolNames[numTools] = "new_tool"
			server := &model.MCPServer{
				Name:          "server_0",
				ResourceNames: toolNames,
				ProtocolType:  constant.MCPServerProtocolTypeSSE,
			}
			release := &model.Release{ResourceVersionID: 1}

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				mcppkg.CheckNeedLoadForTest(p, server, release)
			}
		})
	}
}

// BenchmarkCheckNeedLoad_NewServer benchmarks checkNeedLoad for a new server (doesn't exist yet).
func BenchmarkCheckNeedLoad_NewServer(b *testing.B) {
	p := proxy.NewMCPProxy("", "")
	server := &model.MCPServer{Name: "nonexistent"}
	release := &model.Release{ResourceVersionID: 1}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		mcppkg.CheckNeedLoadForTest(p, server, release)
	}
}

// ---------- Benchmark: AddMCPServerFromOpenAPISpec ----------

// BenchmarkAddMCPServerFromOpenAPISpec benchmarks adding a single server with varying tool counts.
func BenchmarkAddMCPServerFromOpenAPISpec(b *testing.B) {
	for _, numTools := range []int{1, 5, 10, 20, 50} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			spec := buildOpenAPISpec(numTools)
			ops := operationIDs(numTools)

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := proxy.NewMCPProxy("", "")
				_ = p.AddMCPServerFromOpenAPISpec(
					"bench-server", 1, spec, ops, nil, constant.MCPServerProtocolTypeSSE,
				)
			}
		})
	}
}

// BenchmarkAddMCPServerFromOpenAPISpec_StreamableHTTP benchmarks adding a Streamable HTTP server.
func BenchmarkAddMCPServerFromOpenAPISpec_StreamableHTTP(b *testing.B) {
	for _, numTools := range []int{1, 10, 50} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			spec := buildOpenAPISpec(numTools)
			ops := operationIDs(numTools)

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := proxy.NewMCPProxy("", "")
				_ = p.AddMCPServerFromOpenAPISpec(
					"bench-server", 1, spec, ops, nil, constant.MCPServerProtocolTypeStreamableHTTP,
				)
			}
		})
	}
}

// ---------- Benchmark: UpdateMCPServerFromOpenApiSpec ----------

// BenchmarkUpdateMCPServerFromOpenApiSpec benchmarks updating an existing server with a new spec.
func BenchmarkUpdateMCPServerFromOpenApiSpec(b *testing.B) {
	for _, numTools := range []int{5, 20, 50} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			p := setupProxyWithServers(1, numTools, 1)
			newSpec := buildOpenAPISpec(numTools + 5)
			newOps := operationIDs(numTools + 5)
			server := p.GetMCPServer("server_0")

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				_ = p.UpdateMCPServerFromOpenApiSpec(
					server, "server_0", i+2, newSpec, newOps, nil,
				)
			}
		})
	}
}

// ---------- Benchmark: applyServerChanges ----------

// BenchmarkApplyServerChanges_AllError benchmarks applying changes when all results have errors.
func BenchmarkApplyServerChanges_AllError(b *testing.B) {
	for _, numServers := range []int{5, 20, 50, 100} {
		b.Run(fmt.Sprintf("servers=%d", numServers), func(b *testing.B) {
			ctx := context.Background()
			results := make([]*mcppkg.ServerLoadResult, numServers)
			for i := 0; i < numServers; i++ {
				results[i] = mcppkg.NewServerLoadResult(
					&model.MCPServer{Name: fmt.Sprintf("err-server-%d", i)},
					nil, nil,
					fmt.Errorf("simulated error %d", i),
					false, false, false,
				)
			}

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := proxy.NewMCPProxy("", "")
				mcppkg.ApplyServerChangesForTest(ctx, p, results)
			}
		})
	}
}

// NOTE: BenchmarkApplyServerChanges_AllSkipped is not included because the "skipped"
// code path calls loadMCPServerPrompts() which requires database/cache initialization.
// This path is better benchmarked via integration tests.

// ---------- Benchmark: cleanupStaleMCPServers ----------

// BenchmarkCleanupStaleMCPServers benchmarks cleanup of stale servers.
// NOTE: setup (create proxy + servers) is included in measurement because separating it
// with StopTimer/StartTimer causes b.N to grow excessively, leading to timeouts.
func BenchmarkCleanupStaleMCPServers(b *testing.B) {
	for _, total := range []int{5, 10, 20} {
		staleCount := total / 2
		b.Run(fmt.Sprintf("total=%d/stale=%d", total, staleCount), func(b *testing.B) {
			ctx := context.Background()

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := setupProxyWithServers(total, 3, 1)
				p.Run(ctx)
				activeSet := make(map[string]struct{})
				for j := 0; j < total-staleCount; j++ {
					activeSet[fmt.Sprintf("server_%d", j)] = struct{}{}
				}
				mcppkg.CleanupStaleMCPServersForTest(ctx, p, activeSet)
			}
		})
	}
}

// ---------- Benchmark: cleanupAllMCPServers ----------

// BenchmarkCleanupAllMCPServers benchmarks full cleanup of all servers.
func BenchmarkCleanupAllMCPServers(b *testing.B) {
	for _, numServers := range []int{5, 10, 20} {
		b.Run(fmt.Sprintf("servers=%d", numServers), func(b *testing.B) {
			ctx := context.Background()

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := setupProxyWithServers(numServers, 3, 1)
				p.Run(ctx)
				mcppkg.CleanupAllMCPServersForTest(ctx, p)
			}
		})
	}
}

// ---------- Benchmark: Full Load Cycle (add + update + cleanup) ----------

// BenchmarkFullLoadCycle simulates a complete load cycle:
// 1. Create MCPProxy with existing servers
// 2. Build server load results (mix of add/update/skip/error)
// 3. Apply changes
// 4. Cleanup stale servers
func BenchmarkFullLoadCycle(b *testing.B) {
	for _, totalServers := range []int{10, 20} {
		b.Run(fmt.Sprintf("total=%d", totalServers), func(b *testing.B) {
			ctx := context.Background()

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				// Setup: create proxy with half the servers already loaded
				existingCount := totalServers / 2
				p := setupProxyWithServers(existingCount, 5, 1)
				p.Run(ctx)

				// Build results simulating:
				// - first half: new servers to add (won't hit prompts because conf has no openapiFileData)
				// - second half: errors
				results := make([]*mcppkg.ServerLoadResult, totalServers)
				half := totalServers / 2

				for j := 0; j < totalServers; j++ {
					name := fmt.Sprintf("server_%d", j)
					switch {
					case j < half:
						// Error results (fast path, no DB needed)
						results[j] = mcppkg.NewServerLoadResult(
							&model.MCPServer{ID: j, Name: name},
							nil, nil,
							fmt.Errorf("simulated error %d", j),
							false, false, false,
						)
					default:
						// Error results
						results[j] = mcppkg.NewServerLoadResult(
							&model.MCPServer{ID: j, Name: name},
							nil, nil,
							fmt.Errorf("simulated error %d", j),
							false, false, false,
						)
					}
				}

				// Build active set (everything except stale servers)
				activeSet := make(map[string]struct{})
				for j := 0; j < totalServers; j++ {
					activeSet[fmt.Sprintf("server_%d", j)] = struct{}{}
				}

				// Phase 2: apply changes
				mcppkg.ApplyServerChangesForTest(ctx, p, results)

				// Phase 3: cleanup stale
				mcppkg.CleanupStaleMCPServersForTest(ctx, p, activeSet)
			}
		})
	}
}

// ---------- Benchmark: AddMCPServer at scale ----------

// BenchmarkAddMultipleServers benchmarks adding many servers sequentially.
func BenchmarkAddMultipleServers(b *testing.B) {
	for _, numServers := range []int{5, 10, 20} {
		b.Run(fmt.Sprintf("servers=%d", numServers), func(b *testing.B) {
			spec := buildOpenAPISpec(10)
			ops := operationIDs(10)

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := proxy.NewMCPProxy("", "")
				for j := 0; j < numServers; j++ {
					_ = p.AddMCPServerFromOpenAPISpec(
						fmt.Sprintf("server_%d", j), 1, spec, ops, nil, constant.MCPServerProtocolTypeSSE,
					)
				}
			}
		})
	}
}

// ---------- Benchmark: Tool name mapping ----------

// BenchmarkAddMCPServerWithToolNameMap benchmarks adding a server with tool name mapping.
func BenchmarkAddMCPServerWithToolNameMap(b *testing.B) {
	for _, numTools := range []int{5, 20, 50} {
		b.Run(fmt.Sprintf("tools=%d", numTools), func(b *testing.B) {
			spec := buildOpenAPISpec(numTools)
			ops := operationIDs(numTools)
			toolNameMap := make(map[string]string, numTools)
			for i := 0; i < numTools; i++ {
				toolNameMap[fmt.Sprintf("op_%d", i)] = fmt.Sprintf("custom_tool_%d", i)
			}

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := proxy.NewMCPProxy("", "")
				_ = p.AddMCPServerFromOpenAPISpec(
					"bench-server", 1, spec, ops, toolNameMap, constant.MCPServerProtocolTypeSSE,
				)
			}
		})
	}
}

// ---------- Benchmark: Prompts ----------

// BenchmarkRegisterPrompts benchmarks prompt registration to servers.
func BenchmarkRegisterPrompts(b *testing.B) {
	for _, numPrompts := range []int{1, 5, 20, 50} {
		b.Run(fmt.Sprintf("prompts=%d", numPrompts), func(b *testing.B) {
			prompts := make([]*proxy.PromptConfig, numPrompts)
			for i := 0; i < numPrompts; i++ {
				prompts[i] = &proxy.PromptConfig{
					Name:        fmt.Sprintf("prompt_%d", i),
					Description: fmt.Sprintf("Benchmark prompt %d", i),
					Content:     fmt.Sprintf("This is the content for prompt %d used in benchmarking", i),
				}
			}

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := setupProxyWithServers(1, 5, 1)
				p.RegisterPromptsToMCPServer("server_0", prompts)
			}
		})
	}
}

// BenchmarkUpdatePrompts benchmarks prompt update (add new + remove old) on servers.
func BenchmarkUpdatePrompts(b *testing.B) {
	for _, numPrompts := range []int{5, 20, 50} {
		b.Run(fmt.Sprintf("prompts=%d", numPrompts), func(b *testing.B) {
			// Initial prompts
			initPrompts := make([]*proxy.PromptConfig, numPrompts)
			for i := 0; i < numPrompts; i++ {
				initPrompts[i] = &proxy.PromptConfig{
					Name:        fmt.Sprintf("prompt_%d", i),
					Description: fmt.Sprintf("Initial prompt %d", i),
					Content:     fmt.Sprintf("Initial content %d", i),
				}
			}
			// Updated prompts: remove half, add half new
			half := numPrompts / 2
			newPrompts := make([]*proxy.PromptConfig, numPrompts)
			for i := 0; i < half; i++ {
				newPrompts[i] = initPrompts[i] // keep first half
			}
			for i := half; i < numPrompts; i++ {
				newPrompts[i] = &proxy.PromptConfig{
					Name:        fmt.Sprintf("new_prompt_%d", i),
					Description: fmt.Sprintf("New prompt %d", i),
					Content:     fmt.Sprintf("New content %d", i),
				}
			}

			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				p := setupProxyWithServers(1, 5, 1)
				p.RegisterPromptsToMCPServer("server_0", initPrompts)
				p.UpdateMCPServerPrompts("server_0", newPrompts)
			}
		})
	}
}
