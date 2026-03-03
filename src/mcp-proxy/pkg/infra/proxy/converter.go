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
	"encoding/json"
	"net/url"

	"github.com/getkin/kin-openapi/openapi3"
	jsonschema "github.com/swaggest/jsonschema-go"
)

// OpenapiToMcpToolConfig ...
// nolint:gocyclo
// This function takes an OpenAPI specification and a map of operation IDs and returns a slice of ToolConfig structs.
// operationIDMap: 用于过滤需要转换的 operationID
// toolNameMap: 用于将 operationID (资源名) 映射到工具名，如果为 nil 或不存在，则使用 operationID 作为工具名
func OpenapiToMcpToolConfig(
	openApiSpec *openapi3.T,
	operationIDMap map[string]struct{},
	toolNameMap map[string]string,
) []*ToolConfig {
	// Initialize a slice of ToolConfig structs
	var toolConfigs []*ToolConfig
	// Iterate through each path in the OpenAPI specification
	for path, pathItem := range openApiSpec.Paths.Map() {
		// Iterate through each operation in the path
		for method, operation := range pathItem.Operations() {
			// If the operation does not have an operation ID, skip it
			if operation.OperationID == "" {
				continue
			}
			// If operationIDMap is not empty, check if the operation ID is in the map
			if len(operationIDMap) > 0 {
				// 如果指定了operationID，则只转换指定的operationID
				if _, ok := operationIDMap[operation.OperationID]; !ok {
					continue
				}
			}
			requestUrl := openApiSpec.Servers[0].URL
			urlInfo, err := url.Parse(requestUrl)
			if err != nil {
				continue
			}
			description := operation.Description
			if description == "" {
				description = operation.Summary
			}
			// 获取工具名：优先使用 toolNameMap 中的映射，否则使用 operationID
			toolName := operation.OperationID
			if toolNameMap != nil {
				if mappedName, ok := toolNameMap[operation.OperationID]; ok && mappedName != "" {
					toolName = mappedName
				}
			}
			toolConfig := &ToolConfig{
				Host:        urlInfo.Host,
				BasePath:    urlInfo.Path,
				Schema:      urlInfo.Scheme,
				Name:        toolName,
				Method:      method,
				Url:         path,
				Description: description,
				ParamSchema: jsonschema.Schema{},
			}
			j := jsonschema.Type{}
			paramSchema := jsonschema.Schema{
				Type: j.WithSimpleTypes(jsonschema.Object),
			}
			if operation.Parameters != nil {
				headerParamSchema := jsonschema.Schema{
					Type: j.WithSimpleTypes(jsonschema.Object),
				}
				queryParamSchema := jsonschema.Schema{
					Type: j.WithSimpleTypes(jsonschema.Object),
				}
				pathParamSchema := jsonschema.Schema{
					Type: j.WithSimpleTypes(jsonschema.Object),
				}
				for _, param := range operation.Parameters {
					if param.Value.Schema != nil {
						schema := param.Value.Schema.Value
						schema.Description = param.Value.Description
						schema.Example = param.Value.Example
						if param.Value.Required {
							schema.Required = []string{param.Value.Name}
						}
						marshalJSON, _ := schema.MarshalJSON()
						var jsonSchema jsonschema.Schema
						_ = jsonSchema.UnmarshalJSON(marshalJSON)
						if param.Value.In == "header" {
							headerParamSchema.WithPropertiesItem(param.Value.Name, jsonschema.SchemaOrBool{
								TypeObject: &jsonSchema,
							})
							if param.Value.Required {
								headerParamSchema.Required = append(headerParamSchema.Required, param.Value.Name)
							}
						}
						if param.Value.In == "query" {
							queryParamSchema.WithPropertiesItem(param.Value.Name, jsonschema.SchemaOrBool{
								TypeObject: &jsonSchema,
							})
							if param.Value.Required {
								queryParamSchema.Required = append(queryParamSchema.Required, param.Value.Name)
							}
						}
						if param.Value.In == "path" {
							pathParamSchema.Required = append(pathParamSchema.Required, param.Value.Name)
							pathParamSchema.WithPropertiesItem(param.Value.Name, jsonschema.SchemaOrBool{
								TypeObject: &jsonSchema,
							})
						}
					}
				}
				if len(headerParamSchema.Properties) > 0 {
					paramSchema.WithPropertiesItem("header_param", jsonschema.SchemaOrBool{
						TypeObject: &headerParamSchema,
					})
					if len(headerParamSchema.Required) > 0 {
						paramSchema.Required = append(paramSchema.Required, "header_param")
					}
				}
				if len(queryParamSchema.Properties) > 0 {
					paramSchema.WithPropertiesItem("query_param", jsonschema.SchemaOrBool{
						TypeObject: &queryParamSchema,
					})
					if len(queryParamSchema.Required) > 0 {
						paramSchema.Required = append(paramSchema.Required, "query_param")
					}
				}
				if len(pathParamSchema.Properties) > 0 {
					paramSchema.WithPropertiesItem("path_param", jsonschema.SchemaOrBool{
						TypeObject: &pathParamSchema,
					})
					paramSchema.Required = append(paramSchema.Required, "path_param")
				}
			}

			if operation.RequestBody != nil && operation.RequestBody.Value != nil {
				if content, ok := operation.RequestBody.Value.Content["application/json"]; ok && content != nil {
					schema := content.Schema
					marshalJSON, _ := schema.MarshalJSON()
					var jsonSchema jsonschema.Schema
					_ = json.Unmarshal(marshalJSON, &jsonSchema)
					paramSchema.WithPropertiesItem("body_param", jsonschema.SchemaOrBool{
						TypeObject: &jsonSchema,
					})
				}
			}

			if operation.Responses != nil {
				marshalJSON, _ := operation.Responses.MarshalJSON()
				toolConfig.OutputSchema = marshalJSON
			}

			toolConfig.ParamSchema = paramSchema
			toolConfigs = append(toolConfigs, toolConfig)
		}
	}
	return toolConfigs
}
