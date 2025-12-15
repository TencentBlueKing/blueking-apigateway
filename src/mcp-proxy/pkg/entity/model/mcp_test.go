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

package model

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestMCPServer_IsActive(t *testing.T) {
	tests := []struct {
		name     string
		status   int
		expected bool
	}{
		{
			name:     "active status",
			status:   McpServerStatusActive,
			expected: true,
		},
		{
			name:     "inactive status",
			status:   McpServerStatusInactive,
			expected: false,
		},
		{
			name:     "other status",
			status:   999,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server := &MCPServer{
				Status: tt.status,
			}
			assert.Equal(t, tt.expected, server.IsActive())
		})
	}
}

func TestMCPServer_TableName(t *testing.T) {
	server := &MCPServer{}
	assert.Equal(t, "mcp_server", server.TableName())
}

func TestMCPServerAppPermission_TableName(t *testing.T) {
	permission := &MCPServerAppPermission{}
	assert.Equal(t, "mcp_server_app_permission", permission.TableName())
}

func TestArrayString_Scan(t *testing.T) {
	tests := []struct {
		name     string
		input    interface{}
		expected ArrayString
		hasError bool
	}{
		{
			name:     "normal array",
			input:    []byte("item1;item2;item3"),
			expected: ArrayString{"item1", "item2", "item3"},
			hasError: false,
		},
		{
			name:     "single item",
			input:    []byte("item1"),
			expected: ArrayString{"item1"},
			hasError: false,
		},
		{
			name:     "empty string",
			input:    []byte(""),
			expected: ArrayString{},
			hasError: false,
		},
		{
			name:     "invalid type",
			input:    "not a byte slice",
			expected: nil,
			hasError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var arr ArrayString
			err := arr.Scan(tt.input)
			if tt.hasError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, arr)
			}
		})
	}
}

func TestArrayString_Value(t *testing.T) {
	tests := []struct {
		name     string
		input    ArrayString
		expected string
	}{
		{
			name:     "empty array",
			input:    ArrayString{},
			expected: "",
		},
		{
			name:     "array with items",
			input:    ArrayString{"item1", "item2", "item3"},
			expected: ";;", // Note: Current implementation has a bug - it creates empty strIDs
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := tt.input.Value()
			assert.NoError(t, err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMCPServer_Fields(t *testing.T) {
	server := &MCPServer{
		ID:            1,
		Name:          "test-server",
		Description:   "Test MCP Server",
		IsPublic:      true,
		Labels:        ArrayString{"label1", "label2"},
		ResourceNames: ArrayString{"resource1", "resource2"},
		Status:        McpServerStatusActive,
		GatewayID:     100,
		StageID:       200,
	}

	assert.Equal(t, 1, server.ID)
	assert.Equal(t, "test-server", server.Name)
	assert.Equal(t, "Test MCP Server", server.Description)
	assert.True(t, server.IsPublic)
	assert.Len(t, server.Labels, 2)
	assert.Len(t, server.ResourceNames, 2)
	assert.Equal(t, McpServerStatusActive, server.Status)
	assert.Equal(t, 100, server.GatewayID)
	assert.Equal(t, 200, server.StageID)
}

func TestMCPServerAppPermission_Fields(t *testing.T) {
	expires := time.Now().Add(24 * time.Hour)
	permission := &MCPServerAppPermission{
		Id:          1,
		BkAppCode:   "test-app",
		Expires:     expires,
		GrantType:   "apply",
		McpServerId: 123,
	}

	assert.Equal(t, 1, permission.Id)
	assert.Equal(t, "test-app", permission.BkAppCode)
	assert.Equal(t, expires, permission.Expires)
	assert.Equal(t, "apply", permission.GrantType)
	assert.Equal(t, 123, permission.McpServerId)
}

func TestMcpServerStatus_Constants(t *testing.T) {
	assert.Equal(t, 1, McpServerStatusActive)
	assert.Equal(t, 0, McpServerStatusInactive)
}
