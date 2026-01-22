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

// Package model ...
package model

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"mcp_proxy/pkg/constant"
)

// McpServerStatusActive ...
const (
	McpServerStatusActive   = 1
	McpServerStatusInactive = 0
)

// ToolNameSeparator 工具名分隔符：resource_name@tool_name
const ToolNameSeparator = "@"

// MCPServer ...
type MCPServer struct {
	ID            int         `gorm:"primaryKey;autoIncrement;column:id"`
	Name          string      `gorm:"column:name;size:64;uniqueIndex"`
	Description   string      `gorm:"column:description;size:512"`
	IsPublic      bool        `gorm:"column:is_public"`
	Labels        ArrayString `gorm:"column:labels"`
	ResourceNames ArrayString `gorm:"column:resource_names"`
	Status        int         `gorm:"column:status"`
	GatewayID     int         `gorm:"column:gateway_id"`
	StageID       int         `gorm:"column:stage_id"`
	ProtocolType  string      `gorm:"column:protocol_type;size:32;default:sse"`
}

// GetProtocolType 获取协议类型，默认返回 SSE
func (m *MCPServer) GetProtocolType() string {
	if m.ProtocolType == "" {
		return constant.MCPServerProtocolTypeSSE
	}
	return m.ProtocolType
}

// IsStreamableHTTP 判断是否为 Streamable HTTP 协议
func (m *MCPServer) IsStreamableHTTP() bool {
	return m.ProtocolType == constant.MCPServerProtocolTypeStreamableHTTP
}

// parseResourceNames 解析资源名列表的底层方法
// position: 0 表示获取资源名（parts[0]），1 表示获取工具名（parts[1]）
func (m *MCPServer) parseResourceNames(position int) []string {
	if len(m.ResourceNames) == 0 {
		return []string{}
	}

	result := make([]string, 0, len(m.ResourceNames))
	for _, item := range m.ResourceNames {
		if strings.Contains(item, ToolNameSeparator) {
			parts := strings.SplitN(item, ToolNameSeparator, 2)
			if position == 1 && len(parts) > 1 && parts[1] != "" {
				result = append(result, parts[1])
			} else {
				result = append(result, parts[0])
			}
		} else {
			result = append(result, item)
		}
	}
	return result
}

// GetResourceNames 获取资源名称列表（去除工具名部分）
// 数据库存储格式：resource_name_1;resource_name_2@tool_name_2;resource_name_3@tool_name_3
// 返回：[resource_name_1, resource_name_2, resource_name_3]
func (m *MCPServer) GetResourceNames() []string {
	return m.parseResourceNames(0)
}

// GetToolNames 获取工具名列表（与 GetResourceNames 顺序对应）
// 如果没有设置工具名，使用资源名
// 数据库存储格式：resource_name_1;resource_name_2@tool_name_2;resource_name_3@tool_name_3
// 返回：[resource_name_1, tool_name_2, tool_name_3]
func (m *MCPServer) GetToolNames() []string {
	return m.parseResourceNames(1)
}

// GetToolNameMap 生成资源名到工具名的映射
// 返回：{resource_name_1: resource_name_1, resource_name_2: tool_name_2, resource_name_3: tool_name_3}
func (m *MCPServer) GetToolNameMap() map[string]string {
	if len(m.ResourceNames) == 0 {
		return map[string]string{}
	}

	result := make(map[string]string, len(m.ResourceNames))
	for _, item := range m.ResourceNames {
		if strings.Contains(item, ToolNameSeparator) {
			parts := strings.SplitN(item, ToolNameSeparator, 2)
			resourceName := parts[0]
			if len(parts) > 1 && parts[1] != "" {
				result[resourceName] = parts[1]
			} else {
				result[resourceName] = resourceName
			}
		} else {
			result[item] = item
		}
	}
	return result
}

// IsActive ...
func (m *MCPServer) IsActive() bool {
	return m.Status == McpServerStatusActive
}

// TableName ...
func (m *MCPServer) TableName() string {
	return "mcp_server"
}

// ArrayString ...
type ArrayString []string

// Scan 实现 Scanner 接口用于从数据库读取
func (r *ArrayString) Scan(value interface{}) error {
	str, ok := value.([]byte)
	if !ok {
		return errors.New("invalid resource_ids type")
	}

	if len(str) == 0 {
		*r = []string{}
		return nil
	}
	ids := strings.Split(string(str), ";")
	*r = ids
	return nil
}

// Value 实现 Valuer 接口用于写入数据库
func (r ArrayString) Value() (driver.Value, error) {
	if len(r) == 0 {
		return "", nil
	}
	strIDs := make([]string, len(r))
	return strings.Join(strIDs, ";"), nil
}

// MCPServerAppPermission ...
type MCPServerAppPermission struct {
	Id          int       `gorm:"column:id;AUTO_INCREMENT;primary_key"`
	BkAppCode   string    `gorm:"column:bk_app_code;NOT NULL"`
	Expires     time.Time `gorm:"column:expires"`
	GrantType   string    `gorm:"column:grant_type;NOT NULL"`
	McpServerId int       `gorm:"column:mcp_server_id;NOT NULL"`
}

// TableName ...
func (m *MCPServerAppPermission) TableName() string {
	return "mcp_server_app_permission"
}

// MCPServerExtend MCP Server 扩展信息
type MCPServerExtend struct {
	ID          int       `gorm:"primaryKey;autoIncrement;column:id"`
	McpServerID int       `gorm:"column:mcp_server_id;NOT NULL"`
	Type        string    `gorm:"column:type;size:32;NOT NULL"`
	Content     string    `gorm:"column:content;type:longtext;NOT NULL"`
	CreatedBy   string    `gorm:"column:created_by;size:32"`
	UpdatedBy   string    `gorm:"column:updated_by;size:32"`
	CreatedTime time.Time `gorm:"column:created_time;autoCreateTime"`
	UpdatedTime time.Time `gorm:"column:updated_time;autoUpdateTime"`
}

// TableName ...
func (m *MCPServerExtend) TableName() string {
	return "mcp_server_extend"
}

// MCPServerExtendType 扩展类型常量
const (
	MCPServerExtendTypePrompts = "prompts"
)

// GetPrompts 当 Type 为 prompts 时，解析 Content 为 Prompt 列表
func (m *MCPServerExtend) GetPrompts() (Prompts, error) {
	if m.Type != MCPServerExtendTypePrompts {
		return nil, nil
	}
	if m.Content == "" {
		return nil, nil
	}
	var items Prompts
	if err := json.Unmarshal([]byte(m.Content), &items); err != nil {
		return nil, err
	}
	return items, nil
}

// Prompt Prompt 配置项
type Prompt struct {
	ID        int      `json:"id"`
	Name      string   `json:"name"`
	Code      string   `json:"code"`
	Content   string   `json:"content"`
	Labels    []string `json:"labels"`
	IsPublic  bool     `json:"is_public"`
	SpaceCode string   `json:"space_code"`
	SpaceName string   `json:"space_name"`
}

// Prompts ....
type Prompts []*Prompt
