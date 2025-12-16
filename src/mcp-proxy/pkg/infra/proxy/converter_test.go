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

var _ = Describe("OpenapiToMcpToolConfig", func() {
	Describe("Empty Spec", func() {
		It("should return empty result for empty spec", func() {
			spec := &openapi3.T{
				Paths: &openapi3.Paths{},
			}

			result := OpenapiToMcpToolConfig(spec, nil)
			Expect(result).To(BeEmpty())
		})
	})

	Describe("With Operations", func() {
		It("should convert operations to tool config", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
					Description: "Returns a list of users",
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)

			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
			Expect(result[0].Description).To(Equal("Returns a list of users"))
			Expect(result[0].Method).To(Equal("GET"))
			Expect(result[0].Url).To(Equal("/users"))
			Expect(result[0].Host).To(Equal("api.example.com"))
			Expect(result[0].BasePath).To(Equal("/v1"))
			Expect(result[0].Schema).To(Equal("https"))
		})
	})

	Describe("With OperationID Filter", func() {
		It("should filter operations by operationID", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
				},
				Post: &openapi3.Operation{
					OperationID: "createUser",
					Summary:     "Create a user",
				},
			}
			spec.Paths.Set("/users", pathItem)

			operationIDMap := map[string]struct{}{
				"getUsers": {},
			}

			result := OpenapiToMcpToolConfig(spec, operationIDMap)

			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
		})
	})

	Describe("Skips Empty OperationID", func() {
		It("should skip operations without operationID", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					Summary: "Get all users",
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)
			Expect(result).To(BeEmpty())
		})
	})

	Describe("With Query Parameters", func() {
		It("should include query parameters in param schema", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
					Parameters: openapi3.Parameters{
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:        "limit",
								In:          "query",
								Description: "Maximum number of results",
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
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)

			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUsers"))
			Expect(result[0].ParamSchema.Properties).NotTo(BeNil())
		})
	})

	Describe("With Path Parameters", func() {
		It("should include path parameters", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUser",
					Summary:     "Get a user by ID",
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
				},
			}
			spec.Paths.Set("/users/{id}", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)

			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("getUser"))
			Expect(result[0].Url).To(Equal("/users/{id}"))
		})
	})

	Describe("With Header Parameters", func() {
		It("should include header parameters in param schema", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
					Parameters: openapi3.Parameters{
						&openapi3.ParameterRef{
							Value: &openapi3.Parameter{
								Name:        "X-Custom-Header",
								In:          "header",
								Description: "Custom header",
								Required:    true,
								Schema: &openapi3.SchemaRef{
									Value: &openapi3.Schema{
										Type: &openapi3.Types{"string"},
									},
								},
							},
						},
					},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)

			Expect(result).To(HaveLen(1))
			Expect(result[0].ParamSchema.Properties).NotTo(BeNil())
		})
	})

	Describe("With Request Body", func() {
		It("should handle request body", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Post: &openapi3.Operation{
					OperationID: "createUser",
					Summary:     "Create a user",
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
											},
										},
									},
								},
							},
						},
					},
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)

			Expect(result).To(HaveLen(1))
			Expect(result[0].Name).To(Equal("createUser"))
			Expect(result[0].Method).To(Equal("POST"))
		})
	})

	Describe("Use Summary When No Description", func() {
		It("should use summary as description when description is empty", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "https://api.example.com/v1",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users summary",
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)

			Expect(result).To(HaveLen(1))
			Expect(result[0].Description).To(Equal("Get all users summary"))
		})
	})

	Describe("Invalid Server URL", func() {
		It("should skip operations with invalid server URLs", func() {
			spec := &openapi3.T{
				Servers: openapi3.Servers{
					&openapi3.Server{
						URL: "://invalid-url",
					},
				},
				Paths: &openapi3.Paths{},
			}

			pathItem := &openapi3.PathItem{
				Get: &openapi3.Operation{
					OperationID: "getUsers",
					Summary:     "Get all users",
				},
			}
			spec.Paths.Set("/users", pathItem)

			result := OpenapiToMcpToolConfig(spec, nil)
			Expect(result).To(BeEmpty())
		})
	})
})
