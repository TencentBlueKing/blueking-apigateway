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
	"errors"

	"github.com/getkin/kin-openapi/openapi3"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/infra/proxy"
	mcppkg "mcp_proxy/pkg/mcp"
)

var _ = Describe("MCP Load Functions", func() {
	var (
		mcpProxy    *proxy.MCPProxy
		ctx         context.Context
		openapiSpec *openapi3.T
	)

	BeforeEach(func() {
		mcpProxy = proxy.NewMCPProxy("", "")
		ctx = context.Background()
		openapiSpec = &openapi3.T{
			OpenAPI: "3.0.0",
			Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
			Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
			Paths:   &openapi3.Paths{},
		}
		pathItem := &openapi3.PathItem{
			Get: &openapi3.Operation{
				OperationID: "getUsers",
				Summary:     "Get users",
				Responses:   &openapi3.Responses{},
			},
			Post: &openapi3.Operation{
				OperationID: "createUser",
				Summary:     "Create user",
				Responses:   &openapi3.Responses{},
			},
		}
		openapiSpec.Paths.Set("/users", pathItem)
	})

	Describe("checkNeedLoad", func() {
		It("should return true when server does not exist in proxy", func() {
			server := &model.MCPServer{Name: "new-server"}
			release := &model.Release{ResourceVersionID: 1}

			needLoad := mcppkg.CheckNeedLoadForTest(mcpProxy, server, release)
			Expect(needLoad).To(BeTrue())
		})

		It("should return true when resource version changed", func() {
			// Add an existing server with version 1
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"test-server", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())

			server := &model.MCPServer{
				Name:         "test-server",
				ProtocolType: constant.MCPServerProtocolTypeSSE,
			}
			release := &model.Release{ResourceVersionID: 2} // Different version

			needLoad := mcppkg.CheckNeedLoadForTest(mcpProxy, server, release)
			Expect(needLoad).To(BeTrue())
		})

		It("should return false when version unchanged and all tools present", func() {
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"test-server", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())

			server := &model.MCPServer{
				Name:          "test-server",
				ResourceNames: model.ArrayString{"getUsers"},
				ProtocolType:  constant.MCPServerProtocolTypeSSE,
			}
			release := &model.Release{ResourceVersionID: 1} // Same version

			needLoad := mcppkg.CheckNeedLoadForTest(mcpProxy, server, release)
			Expect(needLoad).To(BeFalse())
		})

		It("should return true when new tool is added (resource_names changed)", func() {
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"test-server", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())

			server := &model.MCPServer{
				Name:          "test-server",
				ResourceNames: model.ArrayString{"getUsers", "createUser"}, // New tool added
				ProtocolType:  constant.MCPServerProtocolTypeSSE,
			}
			release := &model.Release{ResourceVersionID: 1} // Same version

			needLoad := mcppkg.CheckNeedLoadForTest(mcpProxy, server, release)
			Expect(needLoad).To(BeTrue())
		})

		It("should return true when protocol type changed", func() {
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"test-server", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())

			server := &model.MCPServer{
				Name:         "test-server",
				ProtocolType: constant.MCPServerProtocolTypeStreamableHTTP, // Changed protocol
			}
			release := &model.Release{ResourceVersionID: 1}

			needLoad := mcppkg.CheckNeedLoadForTest(mcpProxy, server, release)
			Expect(needLoad).To(BeTrue())
		})

		It("should return true when raw_response_enabled changed", func() {
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"test-server", 1, openapiSpec, []string{"getUsers"}, nil,
				constant.MCPServerProtocolTypeSSE, false,
			)
			Expect(err).NotTo(HaveOccurred())

			server := &model.MCPServer{
				Name:                "test-server",
				ProtocolType:        constant.MCPServerProtocolTypeSSE,
				RawResponseEnabled:  true, // Changed raw_response_enabled
			}
			release := &model.Release{ResourceVersionID: 1}

			needLoad := mcppkg.CheckNeedLoadForTest(mcpProxy, server, release)
			Expect(needLoad).To(BeTrue())
		})
	})

	Describe("cleanupAllMCPServers", func() {
		It("should remove all MCP servers from proxy", func() {
			// Add two servers
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"server-1", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())
			err = mcpProxy.AddMCPServerFromOpenAPISpec(
				"server-2", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())
			mcpProxy.Run(ctx)

			Expect(mcpProxy.GetActiveMCPServerNames()).To(HaveLen(2))

			mcppkg.CleanupAllMCPServersForTest(ctx, mcpProxy)

			Expect(mcpProxy.IsMCPServerExist("server-1")).To(BeFalse())
			Expect(mcpProxy.IsMCPServerExist("server-2")).To(BeFalse())
		})

		It("should not panic when no servers exist", func() {
			Expect(func() {
				mcppkg.CleanupAllMCPServersForTest(ctx, mcpProxy)
			}).NotTo(Panic())
		})
	})

	Describe("cleanupStaleMCPServers", func() {
		It("should delete servers not in active set", func() {
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"server-1", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())
			err = mcpProxy.AddMCPServerFromOpenAPISpec(
				"server-2", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())
			mcpProxy.Run(ctx)

			// Only server-1 is active
			activeServers := map[string]struct{}{
				"server-1": {},
			}

			deletedCount := mcppkg.CleanupStaleMCPServersForTest(ctx, mcpProxy, activeServers)

			Expect(deletedCount).To(Equal(1))
			Expect(mcpProxy.IsMCPServerExist("server-1")).To(BeTrue())
			Expect(mcpProxy.IsMCPServerExist("server-2")).To(BeFalse())
		})

		It("should return 0 when all servers are active", func() {
			err := mcpProxy.AddMCPServerFromOpenAPISpec(
				"server-1", 1, openapiSpec, []string{"getUsers"}, nil, constant.MCPServerProtocolTypeSSE,
				false,
			)
			Expect(err).NotTo(HaveOccurred())
			mcpProxy.Run(ctx)

			activeServers := map[string]struct{}{
				"server-1": {},
			}

			deletedCount := mcppkg.CleanupStaleMCPServersForTest(ctx, mcpProxy, activeServers)
			Expect(deletedCount).To(Equal(0))
		})

		It("should return 0 when no servers exist", func() {
			activeServers := map[string]struct{}{}
			deletedCount := mcppkg.CleanupStaleMCPServersForTest(ctx, mcpProxy, activeServers)
			Expect(deletedCount).To(Equal(0))
		})
	})

	Describe("applyServerChanges", func() {
		It("should count errors for failed results", func() {
			r := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "fail-server"},
				nil,
				nil,
				errors.New("load failed"),
				false,
				false,
				false,
			)
			results := []*mcppkg.ServerLoadResult{r}

			stats, activeServers := mcppkg.ApplyServerChangesForTest(ctx, mcpProxy, results)
			added, updated, skipped, errCount := mcppkg.GetLoadStatsValues(stats)

			Expect(errCount).To(Equal(1))
			Expect(added).To(Equal(0))
			Expect(updated).To(Equal(0))
			Expect(skipped).To(Equal(0))
			Expect(activeServers).To(HaveKey("fail-server"))
		})

		It("should track all servers as active even with errors", func() {
			r1 := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "server-a"},
				nil, nil,
				errors.New("error"),
				false, false, false,
			)
			r2 := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "server-b"},
				nil, nil,
				errors.New("error"),
				false, false, false,
			)
			results := []*mcppkg.ServerLoadResult{r1, r2}

			_, activeServers := mcppkg.ApplyServerChangesForTest(ctx, mcpProxy, results)

			Expect(activeServers).To(HaveLen(2))
			Expect(activeServers).To(HaveKey("server-a"))
			Expect(activeServers).To(HaveKey("server-b"))
		})

		It("should count multiple errors correctly", func() {
			r1 := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "fail-1"},
				nil, nil,
				errors.New("error 1"),
				false, false, false,
			)
			r2 := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "fail-2"},
				nil, nil,
				errors.New("error 2"),
				false, false, false,
			)
			r3 := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "fail-3"},
				nil, nil,
				errors.New("error 3"),
				false, false, false,
			)
			results := []*mcppkg.ServerLoadResult{r1, r2, r3}

			stats, _ := mcppkg.ApplyServerChangesForTest(ctx, mcpProxy, results)
			_, _, _, errCount := mcppkg.GetLoadStatsValues(stats)

			Expect(errCount).To(Equal(3))
		})
	})

	Describe("loadStats", func() {
		It("should correctly return stat values", func() {
			// Simulate the scenario: 1 error, 0 added, 0 updated, 0 skipped
			r := mcppkg.NewServerLoadResult(
				&model.MCPServer{Name: "err-server"},
				nil, nil,
				errors.New("test"),
				false, false, false,
			)
			results := []*mcppkg.ServerLoadResult{r}

			stats, _ := mcppkg.ApplyServerChangesForTest(ctx, mcpProxy, results)
			added, updated, skipped, errCount := mcppkg.GetLoadStatsValues(stats)

			Expect(added).To(Equal(0))
			Expect(updated).To(Equal(0))
			Expect(skipped).To(Equal(0))
			Expect(errCount).To(Equal(1))
		})
	})
})
