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

	"github.com/stretchr/testify/assert"
)

func TestToolConfig_String(t *testing.T) {
	tests := []struct {
		name     string
		config   ToolConfig
		expected string
	}{
		{
			name: "basic config",
			config: ToolConfig{
				Name:     "getUsers",
				Host:     "api.example.com",
				BasePath: "/v1",
				Url:      "/users",
				Method:   "GET",
			},
			expected: "tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
		},
		{
			name: "host with trailing slash",
			config: ToolConfig{
				Name:     "getUsers",
				Host:     "api.example.com/",
				BasePath: "/v1",
				Url:      "/users",
				Method:   "GET",
			},
			expected: "tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
		},
		{
			name: "base path with leading and trailing slashes",
			config: ToolConfig{
				Name:     "getUsers",
				Host:     "api.example.com",
				BasePath: "/v1/",
				Url:      "/users",
				Method:   "GET",
			},
			expected: "tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
		},
		{
			name: "url without leading slash",
			config: ToolConfig{
				Name:     "getUsers",
				Host:     "api.example.com",
				BasePath: "/v1",
				Url:      "users",
				Method:   "GET",
			},
			expected: "tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
		},
		{
			name: "POST method",
			config: ToolConfig{
				Name:     "createUser",
				Host:     "api.example.com",
				BasePath: "/v1",
				Url:      "/users",
				Method:   "POST",
			},
			expected: "tool:[name:createUser,url:api.example.com/v1/users, method:POST]",
		},
		{
			name: "empty base path",
			config: ToolConfig{
				Name:     "getUsers",
				Host:     "api.example.com",
				BasePath: "",
				Url:      "/users",
				Method:   "GET",
			},
			expected: "tool:[name:getUsers,url:api.example.com/users, method:GET]",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.config.String()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMCPServerConfig(t *testing.T) {
	config := MCPServerConfig{
		Name:              "test-server",
		ResourceVersionID: 123,
		Tools: []*ToolConfig{
			{
				Name:        "tool1",
				Description: "Test tool 1",
				Method:      "GET",
				Host:        "api.example.com",
				BasePath:    "/v1",
				Url:         "/test",
			},
		},
	}

	assert.Equal(t, "test-server", config.Name)
	assert.Equal(t, 123, config.ResourceVersionID)
	assert.Len(t, config.Tools, 1)
	assert.Equal(t, "tool1", config.Tools[0].Name)
}
