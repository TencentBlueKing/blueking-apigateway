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

package cacheimpls

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/TencentBlueKing/gopkg/cache/memory"
	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/entity/model"
)

func TestMCPServerKey_Key(t *testing.T) {
	tests := []struct {
		name        string
		key         MCPServerKey
		expectedKey string
	}{
		{
			name: "normal name",
			key: MCPServerKey{
				Name: "test-server",
			},
			expectedKey: "test-server",
		},
		{
			name: "empty name",
			key: MCPServerKey{
				Name: "",
			},
			expectedKey: "",
		},
		{
			name: "name with special characters",
			key: MCPServerKey{
				Name: "test-server-123_abc",
			},
			expectedKey: "test-server-123_abc",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.key.Key()
			assert.Equal(t, tt.expectedKey, result)
		})
	}
}

func TestGetMCPServerByName_Success(t *testing.T) {
	expiration := 5 * time.Minute

	expectedServer := &model.MCPServer{
		ID:        1,
		Name:      "test-server",
		GatewayID: 123,
		StageID:   456,
		Status:    model.McpServerStatusActive,
	}

	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return expectedServer, nil
	}
	mockCache := memory.NewCache("mockMCPServerCache", retrieveFunc, expiration, nil)
	mcpServerCache = mockCache

	result, err := GetMCPServerByName(context.Background(), "test-server")
	assert.NoError(t, err)
	assert.NotNil(t, result)
	assert.Equal(t, "test-server", result.Name)
	assert.Equal(t, 123, result.GatewayID)
}

func TestGetMCPServerByName_Error(t *testing.T) {
	expiration := 5 * time.Minute

	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return nil, errors.New("record not found")
	}
	mockCache := memory.NewCache("mockMCPServerCache", retrieveFunc, expiration, nil)
	mcpServerCache = mockCache

	_, err := GetMCPServerByName(context.Background(), "non-existent")
	assert.Error(t, err)
}

func TestGetMCPServerByName_InvalidType(t *testing.T) {
	expiration := 5 * time.Minute

	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return "invalid type", nil
	}
	mockCache := memory.NewCache("mockMCPServerCache", retrieveFunc, expiration, nil)
	mcpServerCache = mockCache

	_, err := GetMCPServerByName(context.Background(), "test-server")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not model.mcp in cache")
}
