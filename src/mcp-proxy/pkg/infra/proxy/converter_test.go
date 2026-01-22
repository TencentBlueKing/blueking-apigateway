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

package proxy

import (
	"github.com/getkin/kin-openapi/openapi3"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("Converter", func() {
	Describe("OpenapiToMcpToolConfig", func() {
		It("should return empty slice for empty paths", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(BeEmpty())
		})

		It("should skip operations without operation ID", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					Summary:   "Get users without operation ID",
					Responses: &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(BeEmpty())
		})

		It("should convert simple GET operation", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
					Description: "Retrieve a list of all users",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
			Expect(result[0].Method).To(Equal("GET"))
			Expect(result[0].Url).To(Equal("/users"))
			Expect(result[0].Host).To(Equal("api.example.com"))
			Expect(result[0].BasePath).To(Equal("/v1"))
			Expect(result[0].Schema).To(Equal("https"))
			Expect(result[0].Description).To(Equal("Retrieve a list of all users"))
		})

		It("should use summary when description is empty", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].Description).To(Equal("Get all users"))
		})

		It("should filter by operation ID map", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
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
			spec.Paths.Set("/users", pathItem)

			operationIDMap := map[string]struct{}{
				"getUsers": {},
			}

			result := OpenapiToMcpToolConfig(spec, operationIDMap, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
		})

		It("should handle query parameters", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get users",
					Parameters: openapi3.Parameters{
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:        "limit",
								In:          "query",
								Description: "Number of results to return",
								Required:    true,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{
										Type: &openapi3.Types{"integer"},
									},
								},
							},
						},
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:        "offset",
								In:          "query",
								Description: "Offset for pagination",
								Required:    false,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{
										Type: &openapi3.Types{"integer"},
									},
								},
							},
						},
					},
					Responses: &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("query_param"))
			Expect(result[0].ParamSchema.Required).To(ContainElement("query_param"))
		})

		It("should handle path parameters", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUserById",
					Summary:     "Get user by ID",
					Parameters: openapi3.Parameters{
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:        "id",
								In:          "path",
								Description: "User ID",
								Required:    true,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{
										Type: &openapi3.Types{"string"},
									},
								},
							},
						},
					},
					Responses: &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users/{id}", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("path_param"))
			Expect(result[0].ParamSchema.Required).To(ContainElement("path_param"))
		})

		It("should handle header parameters", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get users",
					Parameters: openapi3.Parameters{
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:        "X-Request-ID",
								In:          "header",
								Description: "Request tracking ID",
								Required:    true,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{
										Type: &openapi3.Types{"string"},
									},
								},
							},
						},
					},
					Responses: &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("header_param"))
			Expect(result[0].ParamSchema.Required).To(ContainElement("header_param"))
		})

		It("should handle request body with JSON content", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Post: &openapi3.Operation{
					OperationID: "createUser",
					Summary:     "Create a new user",
					RequestBody: &openapi3.RequestBodyRef{
						Value: &openapi3.RequestBody{
							Content: openapi3.Content{
								"application/json": &openapi3.MediaType{
									Schema: &openapi3.SchemaRef{
										Value: &openapi3.Schema{
											Type: &openapi3.Types{"object"},
											Properties: openapi3.Schemas{
												"name": &openapi3.SchemaRef{
													Value: &openapi3.Schema{
														Type: &openapi3.Types{"string"},
													},
												},
												"email": &openapi3.SchemaRef{
													Value: &openapi3.Schema{
														Type: &openapi3.Types{"string"},
													},
												},
											},
											Required: []string{"name", "email"},
										},
									},
								},
							},
						},
					},
					Responses: &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("createUser"))
			Expect(result[0].Method).To(Equal("POST"))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("body_param"))
		})

		It("should handle responses", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			responses := &openapi3.Responses{}
			responses.Set("200", &openapi3.ResponseRef{
				Value: &openapi3.Response{
					Description: ptrString("Successful response"),
				},
			})

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get users",
					Responses:   responses,
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].OutputSchema).NotTo(BeNil())
		})

		It("should handle multiple operations in one path", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
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
				Put: &openapi3.Operation{
					OperationID: "updateUser",
					Summary:     "Update user",
					Responses:   &openapi3.Responses{},
				},
				Delete: &openapi3.Operation{
					OperationID: "deleteUser",
					Summary:     "Delete user",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(4))

			names := make([]string, len(result))
			for i, tc := range result {
				names[i] = tc.Name
			}
			Expect(names).To(ContainElements("getUsers", "createUser", "updateUser", "deleteUser"))
		})

		It("should handle multiple paths", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			usersPath := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get users",
					Responses:   &openapi3.Responses{},
				},
			}
			ordersPath := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getOrders",
					Summary:     "Get orders",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", usersPath)
			spec.Paths.Set("/orders", ordersPath)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(2))
		})

		It("should handle mixed parameters", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUserOrders",
					Summary:     "Get user orders",
					Parameters: openapi3.Parameters{
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:     "userId",
								In:       "path",
								Required: true,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{Type: &openapi3.Types{"string"}},
								},
							},
						},
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:     "limit",
								In:       "query",
								Required: false,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{Type: &openapi3.Types{"integer"}},
								},
							},
						},
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:     "X-Trace-ID",
								In:       "header",
								Required: false,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{Type: &openapi3.Types{"string"}},
								},
							},
						},
					},
					Responses: &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users/{userId}/orders", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil, nil)
			Expect(result).To(HaveLen(1))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("path_param"))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("query_param"))
			Expect(result[0].ParamSchema.Properties).To(HaveKey("header_param"))
			Expect(result[0].ParamSchema.Required).To(ContainElement("path_param"))
		})

		It("should use tool name from toolNameMap when provided", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
					Responses:   &openapi3.Responses{},
				},
				Post: &openapi3.Operation{
					OperationID: "createUser",
					Summary:     "Create user",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			// 只映射 getUsers，createUser 保持原名
			toolNameMap := map[string]string{
				"getUsers": "list_users",
			}

			result := OpenapiToMcpToolConfig(spec, nil, toolNameMap)
			Expect(result).To(HaveLen(2))

			// 找到对应的工具并验证名称
			var getUsersTool, createUserTool *ToolConfig
			for _, tc := range result {
				if tc.Method == "GET" {
					getUsersTool = tc
				} else if tc.Method == "POST" {
					createUserTool = tc
				}
			}
			Expect(getUsersTool).NotTo(BeNil())
			Expect(getUsersTool.Name).To(Equal("list_users"))

			Expect(createUserTool).NotTo(BeNil())
			Expect(createUserTool.Name).To(Equal("createUser"))
		})

		It("should apply tool name mapping with filter", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
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
			spec.Paths.Set("/users", pathItem)

			// 只包含 getUsers 和 createUser
			operationIDMap := map[string]struct{}{
				"getUsers":   {},
				"createUser": {},
			}

			// 映射工具名
			toolNameMap := map[string]string{
				"getUsers":   "fetch_users",
				"createUser": "add_user",
				"deleteUser": "remove_user", // 这个不会生效因为被过滤了
			}

			result := OpenapiToMcpToolConfig(spec, operationIDMap, toolNameMap)
			Expect(result).To(HaveLen(2))

			names := make([]string, len(result))
			for i, tc := range result {
				names[i] = tc.Name
			}
			Expect(names).To(ContainElements("fetch_users", "add_user"))
			Expect(names).NotTo(ContainElement("remove_user"))
		})

		It("should handle empty tool name in mapping", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get users",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			// 空的工具名应该使用 operationID
			toolNameMap := map[string]string{
				"getUsers": "",
			}

			result := OpenapiToMcpToolConfig(spec, nil, toolNameMap)
			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
		})

		It("should use operationID when not in toolNameMap", func() {
			spec := &openapi3.T{
				OpenAPI: "3.0.0",
				Info:    &openapi3.Info{Title: "Test API", Version: "1.0.0"},
				Servers: []*openapi3.Server{{URL: "https://api.example.com/v1"}},
				Paths:   &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get users",
					Responses:   &openapi3.Responses{},
				},
			}
			spec.Paths.Set("/users", pathItem)

			// toolNameMap 不包含 getUsers
			toolNameMap := map[string]string{
				"otherOperation": "other_tool",
			}

			result := OpenapiToMcpToolConfig(spec, nil, toolNameMap)
			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
		})
	})

	Describe("ToolConfig", func() {
		Describe("String", func() {
			It("should format tool config as string", func() {
				tc := &ToolConfig{
					Name:     "getUsers",
					Host:     "api.example.com",
					BasePath: "/v1",
					Url:      "/users",
					Method:   "GET",
				}

				result := tc.String()
				Expect(result).To(ContainSubstring("getUsers"))
				Expect(result).To(ContainSubstring("GET"))
				Expect(result).To(ContainSubstring("api.example.com"))
			})

			It("should handle trailing slashes in host", func() {
				tc := &ToolConfig{
					Name:     "getUsers",
					Host:     "api.example.com/",
					BasePath: "/v1/",
					Url:      "/users",
					Method:   "GET",
				}

				result := tc.String()
				Expect(result).To(ContainSubstring("api.example.com"))
				Expect(result).NotTo(ContainSubstring("//"))
			})

			It("should handle leading slashes in url", func() {
				tc := &ToolConfig{
					Name:     "getUsers",
					Host:     "api.example.com",
					BasePath: "v1",
					Url:      "users",
					Method:   "GET",
				}

				result := tc.String()
				Expect(result).To(ContainSubstring("api.example.com"))
			})
		})
	})
})

func ptrString(s string) *string {
	return &s
}
