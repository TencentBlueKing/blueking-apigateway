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
	"github.com/getkin/kin-openapi/openapi3"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/proxy"
)

var _ = Describe("MCP", func() {
	Describe("MCPProxy", func() {
		var mcpProxy *proxy.MCPProxy

		BeforeEach(func() {
			mcpProxy = proxy.NewMCPProxy()
		})

		Describe("Basic Operations", func() {
			It("should return false for non-existent server", func() {
				Expect(mcpProxy.IsMCPServerExist("non-existent")).To(BeFalse())
			})

			It("should return nil for non-existent server", func() {
				Expect(mcpProxy.GetMCPServer("non-existent")).To(BeNil())
			})

			It("should return empty names when no servers", func() {
				names := mcpProxy.GetActiveMCPServerNames()
				Expect(names).To(BeEmpty())
			})
		})

		Describe("AddMCPServerFromOpenAPISpec", func() {
			It("should add server from OpenAPI spec", func() {
				openapiSpec := &openapi3.T{
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
				}
				openapiSpec.Paths.Set("/users", pathItem)

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(mcpProxy.IsMCPServerExist("test-server")).To(BeTrue())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetResourceVersionID()).To(Equal(1))
			})
		})

		Describe("DeleteMCPServer", func() {
			It("should delete existing server", func() {
				openapiSpec := &openapi3.T{
					OpenAPI: "3.0.0",
					Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
					Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
					Paths:   &openapi3.Paths{},
				}

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(mcpProxy.IsMCPServerExist("test-server")).To(BeTrue())

				mcpProxy.DeleteMCPServer("test-server")
				Expect(mcpProxy.IsMCPServerExist("test-server")).To(BeFalse())
			})

			It("should not panic when deleting non-existent server", func() {
				Expect(func() {
					mcpProxy.DeleteMCPServer("non-existent")
				}).NotTo(Panic())
			})
		})

		Describe("UpdateMCPServerFromOpenApiSpec", func() {
			It("should update server with new version", func() {
				openapiSpec := &openapi3.T{
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
				}
				openapiSpec.Paths.Set("/users", pathItem)

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetResourceVersionID()).To(Equal(1))

				newOpenapiSpec := &openapi3.T{
					OpenAPI: "3.0.0",
					Info:    &openapi3.Info{Title: "Test API Updated", Version: "2.0.0"},
					Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
					Paths:   &openapi3.Paths{},
				}

				newPathItem := &openapi3.PathItem{
					Get: &openapi3.Operation{
						OperationID: "getUsers",
						Summary:     "Get users updated",
						Responses:   &openapi3.Responses{},
					},
					Post: &openapi3.Operation{
						OperationID: "createUser",
						Summary:     "Create user",
						Responses:   &openapi3.Responses{},
					},
				}
				newOpenapiSpec.Paths.Set("/users", newPathItem)

				err = mcpProxy.UpdateMCPServerFromOpenApiSpec(
					server, "test-server", 2, newOpenapiSpec, []string{"getUsers", "createUser"}, nil,
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(server.GetResourceVersionID()).To(Equal(2))
			})
		})

		Describe("Protocol Type Switch", func() {
			It("should create SSE server with correct protocol type", func() {
				openapiSpec := &openapi3.T{
					OpenAPI: "3.0.0",
					Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
					Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
					Paths:   &openapi3.Paths{},
				}

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"sse-server",
					1,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("sse-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeSSE))
				Expect(server.IsStreamableHTTP()).To(BeFalse())
			})

			It("should create Streamable HTTP server with correct protocol type", func() {
				openapiSpec := &openapi3.T{
					OpenAPI: "3.0.0",
					Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
					Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
					Paths:   &openapi3.Paths{},
				}

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"streamable-http-server",
					1,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeStreamableHTTP,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("streamable-http-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeStreamableHTTP))
				Expect(server.IsStreamableHTTP()).To(BeTrue())
			})

			It("should recreate server when protocol type changes from SSE to Streamable HTTP", func() {
				openapiSpec := &openapi3.T{
					OpenAPI: "3.0.0",
					Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
					Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
					Paths:   &openapi3.Paths{},
				}

				// First create SSE server
				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"switch-server",
					1,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("switch-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeSSE))

				// Delete and recreate with Streamable HTTP (simulating protocol switch)
				mcpProxy.DeleteMCPServer("switch-server")
				Expect(mcpProxy.IsMCPServerExist("switch-server")).To(BeFalse())

				err = mcpProxy.AddMCPServerFromOpenAPISpec(
					"switch-server",
					2,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeStreamableHTTP,
				)
				Expect(err).NotTo(HaveOccurred())

				newServer := mcpProxy.GetMCPServer("switch-server")
				Expect(newServer).NotTo(BeNil())
				Expect(newServer.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeStreamableHTTP))
				Expect(newServer.IsStreamableHTTP()).To(BeTrue())
				Expect(newServer.GetResourceVersionID()).To(Equal(2))
			})

			It("should recreate server when protocol type changes from Streamable HTTP to SSE", func() {
				openapiSpec := &openapi3.T{
					OpenAPI: "3.0.0",
					Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
					Servers: []*openapi3.Server{{URL: "https://api.example.com"}},
					Paths:   &openapi3.Paths{},
				}

				// First create Streamable HTTP server
				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"switch-server-2",
					1,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeStreamableHTTP,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("switch-server-2")
				Expect(server).NotTo(BeNil())
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeStreamableHTTP))

				// Delete and recreate with SSE (simulating protocol switch)
				mcpProxy.DeleteMCPServer("switch-server-2")
				Expect(mcpProxy.IsMCPServerExist("switch-server-2")).To(BeFalse())

				err = mcpProxy.AddMCPServerFromOpenAPISpec(
					"switch-server-2",
					2,
					openapiSpec,
					[]string{},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				newServer := mcpProxy.GetMCPServer("switch-server-2")
				Expect(newServer).NotTo(BeNil())
				Expect(newServer.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeSSE))
				Expect(newServer.IsStreamableHTTP()).To(BeFalse())
				Expect(newServer.GetResourceVersionID()).To(Equal(2))
			})
		})

		Describe("MCPServer Tools", func() {
			It("should get tools from server", func() {
				openapiSpec := &openapi3.T{
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
				}
				openapiSpec.Paths.Set("/users", pathItem)

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				tools := server.GetTools()
				Expect(tools).To(ContainElement("getUsers"))
			})

			It("should unregister tool from server", func() {
				openapiSpec := &openapi3.T{
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

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers", "createUser"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				tools := server.GetTools()
				Expect(tools).To(ContainElement("getUsers"))
				Expect(tools).To(ContainElement("createUser"))

				server.RemoveTool("createUser")

				tools = server.GetTools()
				Expect(tools).To(ContainElement("getUsers"))
				Expect(tools).NotTo(ContainElement("createUser"))
			})

			It("should detect new tools when resource_names changed but version unchanged", func() {
				openapiSpec := &openapi3.T{
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
					Delete: &openapi3.Operation{
						OperationID: "deleteUser",
						Summary:     "Delete user",
						Responses:   &openapi3.Responses{},
					},
				}
				openapiSpec.Paths.Set("/users", pathItem)

				// 初始只注册一个工具
				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetResourceVersionID()).To(Equal(1))

				tools := server.GetTools()
				Expect(tools).To(HaveLen(1))
				Expect(tools).To(ContainElement("getUsers"))

				// 模拟 resource_names 变化检测逻辑
				// 新的 resource_names 包含新工具
				newResourceNames := []string{"getUsers", "createUser", "deleteUser"}
				currentTools := server.GetTools()

				// 检测是否有新工具
				hasNewTools := false
				for _, resourceName := range newResourceNames {
					found := false
					for _, tool := range currentTools {
						if tool == resourceName {
							found = true
							break
						}
					}
					if !found {
						hasNewTools = true
						break
					}
				}
				Expect(hasNewTools).To(BeTrue())

				// 使用相同的 resourceVersionID 更新（模拟 resource_names 变化但版本不变的场景）
				err = mcpProxy.UpdateMCPServerFromOpenApiSpec(
					server, "test-server", 1, openapiSpec, newResourceNames, nil,
				)
				Expect(err).NotTo(HaveOccurred())

				// 验证新工具已注册
				tools = server.GetTools()
				Expect(tools).To(HaveLen(3))
				Expect(tools).To(ContainElement("getUsers"))
				Expect(tools).To(ContainElement("createUser"))
				Expect(tools).To(ContainElement("deleteUser"))
			})

			It("should not reload when resource_names unchanged and version unchanged", func() {
				openapiSpec := &openapi3.T{
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

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers", "createUser"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				// 模拟 resource_names 没有变化的检测逻辑
				sameResourceNames := []string{"getUsers", "createUser"}
				currentTools := server.GetTools()

				// 检测是否有新工具
				hasNewTools := false
				for _, resourceName := range sameResourceNames {
					found := false
					for _, tool := range currentTools {
						if tool == resourceName {
							found = true
							break
						}
					}
					if !found {
						hasNewTools = true
						break
					}
				}
				// 没有新工具，不需要重新加载
				Expect(hasNewTools).To(BeFalse())
			})

			It("should detect new tools when only partial tools exist", func() {
				openapiSpec := &openapi3.T{
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

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				// 新增一个工具 createUser
				newResourceNames := []string{"getUsers", "createUser"}
				currentTools := server.GetTools()

				// 检测是否有新工具
				hasNewTools := false
				for _, resourceName := range newResourceNames {
					found := false
					for _, tool := range currentTools {
						if tool == resourceName {
							found = true
							break
						}
					}
					if !found {
						hasNewTools = true
						break
					}
				}
				// 有新工具 createUser
				Expect(hasNewTools).To(BeTrue())
			})
		})

		Describe("Tool Name Mapping", func() {
			It("should use tool name mapping when adding server", func() {
				openapiSpec := &openapi3.T{
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

				// 使用工具名映射
				toolNameMap := map[string]string{
					"getUsers":   "list_users",
					"createUser": "add_user",
				}

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers", "createUser"},
					toolNameMap,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				// 验证工具名使用了映射后的名称
				tools := server.GetTools()
				Expect(tools).To(ContainElement("list_users"))
				Expect(tools).To(ContainElement("add_user"))
				Expect(tools).NotTo(ContainElement("getUsers"))
				Expect(tools).NotTo(ContainElement("createUser"))
			})

			It("should use original name when tool name mapping is nil", func() {
				openapiSpec := &openapi3.T{
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
				}
				openapiSpec.Paths.Set("/users", pathItem)

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				// 验证工具名使用了原始名称
				tools := server.GetTools()
				Expect(tools).To(ContainElement("getUsers"))
			})

			It("should update server with tool name mapping", func() {
				openapiSpec := &openapi3.T{
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

				// 初始使用原始名称
				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers"},
					nil,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())
				Expect(server.GetTools()).To(ContainElement("getUsers"))

				// 使用工具名映射进行更新
				toolNameMap := map[string]string{
					"getUsers":   "list_users",
					"createUser": "add_user",
				}

				err = mcpProxy.UpdateMCPServerFromOpenApiSpec(
					server, "test-server", 2, openapiSpec, []string{"getUsers", "createUser"}, toolNameMap,
				)
				Expect(err).NotTo(HaveOccurred())

				// 验证新工具名使用了映射后的名称
				tools := server.GetTools()
				Expect(tools).To(ContainElement("list_users"))
				Expect(tools).To(ContainElement("add_user"))
			})

			It("should handle partial tool name mapping", func() {
				openapiSpec := &openapi3.T{
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

				// 只映射部分工具名
				toolNameMap := map[string]string{
					"getUsers": "list_users",
					// createUser 不在映射中，应该使用原始名称
				}

				err := mcpProxy.AddMCPServerFromOpenAPISpec(
					"test-server",
					1,
					openapiSpec,
					[]string{"getUsers", "createUser"},
					toolNameMap,
					constant.MCPServerProtocolTypeSSE,
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				tools := server.GetTools()
				Expect(tools).To(ContainElement("list_users"))
				Expect(tools).To(ContainElement("createUser"))
			})
		})
	})
})
