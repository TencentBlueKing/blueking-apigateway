/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
	"fmt"
	"strings"

	jsonschema "github.com/swaggest/jsonschema-go"
)

// MCPServerConfig ...
type MCPServerConfig struct {
	Name  string        `json:"name"` // 唯一标识name，可以是：gateway_name+stage或者其他id
	Tools []*ToolConfig `json:"tools"`
}

// ToolConfig ...
type ToolConfig struct {
	Name         string            `json:"name"`
	Description  string            `json:"description"`
	Method       string            `json:"method"`
	Host         string            `json:"host"`
	BasePath     string            `json:"base_path"`
	Schema       string            `json:"schema"`
	Url          string            `json:"url"`
	ParamSchema  jsonschema.Schema `json:"param_schema"`
	OutputSchema json.RawMessage   `json:"output_schema"`
}

// String ...
func (t *ToolConfig) String() string {
	base := strings.TrimRight(t.Host, "/") + "/" +
		strings.Trim(strings.TrimLeft(t.BasePath, "/"), "/")
	fullUrl := strings.TrimRight(base, "/") + "/" +
		strings.TrimLeft(t.Url, "/")
	return fmt.Sprintf("tool:[name:%s,url:%s, method:%s]", t.Name, fullUrl, t.Method)
}
