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

	"mcp_proxy/pkg/infra/proxy"
)

var _ = Describe("MCP", func() {
	Describe("MCPProxy", func() {
		var mcpProxy *proxy.MCPProxy

		BeforeEach(func() {
			mcpProxy = proxy.NewMCPProxy("/mcp/%s/message")
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
					"Test API",
					1,
					openapiSpec,
					[]string{"getUsers"},
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
					"Test API",
					1,
					openapiSpec,
					[]string{"getUsers"},
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
					"Test API",
					1,
					openapiSpec,
					[]string{"getUsers"},
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
					server, "test-server", 2, newOpenapiSpec, []string{"getUsers", "createUser"},
				)
				Expect(err).NotTo(HaveOccurred())
				Expect(server.GetResourceVersionID()).To(Equal(2))
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
					"Test API",
					1,
					openapiSpec,
					[]string{"getUsers"},
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
					"Test API",
					1,
					openapiSpec,
					[]string{"getUsers", "createUser"},
				)
				Expect(err).NotTo(HaveOccurred())

				server := mcpProxy.GetMCPServer("test-server")
				Expect(server).NotTo(BeNil())

				tools := server.GetTools()
				Expect(tools).To(ContainElement("getUsers"))
				Expect(tools).To(ContainElement("createUser"))

				server.UnregisterTool("createUser")

				tools = server.GetTools()
				Expect(tools).To(ContainElement("getUsers"))
				Expect(tools).NotTo(ContainElement("createUser"))
			})
		})
	})
})
