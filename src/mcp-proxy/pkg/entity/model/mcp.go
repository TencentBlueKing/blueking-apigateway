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

package model

import (
	"database/sql/driver"
	"errors"
	"strings"
	"time"
)

// McpServerStatusActive ...
const (
	McpServerStatusActive   = 1
	McpServerStatusInactive = 0
)

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
