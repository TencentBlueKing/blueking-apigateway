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
	"testing"

	"github.com/getkin/kin-openapi/openapi3"
	"github.com/stretchr/testify/assert"
)

func TestOpenapiToMcpToolConfig_EmptySpec(t *testing.T) {
	spec := &openapi3.T{
		Paths: &openapi3.Paths{},
	}

	result := OpenapiToMcpToolConfig(spec, nil)
	assert.Empty(t, result)
}

func TestOpenapiToMcpToolConfig_WithOperations(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add a path with GET operation
	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get all users",
			Description: "Returns a list of users",
		},
	}
	spec.Paths.Set("/users", pathItem)

	result := OpenapiToMcpToolConfig(spec, nil)

	assert.Len(t, result, 1)
	assert.Equal(t, "getUsers", result[0].Name)
	assert.Equal(t, "Returns a list of users", result[0].Description)
	assert.Equal(t, "GET", result[0].Method)
	assert.Equal(t, "/users", result[0].Url)
	assert.Equal(t, "api.example.com", result[0].Host)
	assert.Equal(t, "/v1", result[0].BasePath)
	assert.Equal(t, "https", result[0].Schema)
}

func TestOpenapiToMcpToolConfig_WithOperationIDFilter(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add multiple operations
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

	// Filter to only include getUsers
	operationIDMap := map[string]struct{}{
		"getUsers": {},
	}

	result := OpenapiToMcpToolConfig(spec, operationIDMap)

	assert.Len(t, result, 1)
	assert.Equal(t, "getUsers", result[0].Name)
}

func TestOpenapiToMcpToolConfig_SkipsEmptyOperationID(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation without operationID
	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			Summary: "Get all users",
			// No OperationID
		},
	}
	spec.Paths.Set("/users", pathItem)

	result := OpenapiToMcpToolConfig(spec, nil)
	assert.Empty(t, result)
}

func TestOpenapiToMcpToolConfig_WithQueryParameters(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation with query parameters
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

	assert.Len(t, result, 1)
	assert.Equal(t, "getUsers", result[0].Name)
	// Check that param schema has query_param
	assert.NotNil(t, result[0].ParamSchema.Properties)
}

func TestOpenapiToMcpToolConfig_WithPathParameters(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation with path parameters
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

	assert.Len(t, result, 1)
	assert.Equal(t, "getUser", result[0].Name)
	assert.Equal(t, "/users/{id}", result[0].Url)
}

func TestOpenapiToMcpToolConfig_WithHeaderParameters(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation with header parameters
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

	assert.Len(t, result, 1)
	assert.NotNil(t, result[0].ParamSchema.Properties)
}

func TestOpenapiToMcpToolConfig_WithRequestBody(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation with request body
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

	assert.Len(t, result, 1)
	assert.Equal(t, "createUser", result[0].Name)
	assert.Equal(t, "POST", result[0].Method)
}

func TestOpenapiToMcpToolConfig_UseSummaryWhenNoDescription(t *testing.T) {
	spec := &openapi3.T{
		Servers: openapi3.Servers{
			&openapi3.Server{
				URL: "https://api.example.com/v1",
			},
		},
		Paths: &openapi3.Paths{},
	}

	// Add operation with only summary
	pathItem := &openapi3.PathItem{
		Get: &openapi3.Operation{
			OperationID: "getUsers",
			Summary:     "Get all users summary",
			// No Description
		},
	}
	spec.Paths.Set("/users", pathItem)

	result := OpenapiToMcpToolConfig(spec, nil)

	assert.Len(t, result, 1)
	assert.Equal(t, "Get all users summary", result[0].Description)
}

func TestOpenapiToMcpToolConfig_InvalidServerURL(t *testing.T) {
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
	// Should skip operations with invalid server URLs
	assert.Empty(t, result)
}
