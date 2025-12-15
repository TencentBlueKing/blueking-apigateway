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

func TestMCPPermissionCacheKey_Key(t *testing.T) {
	tests := []struct {
		name        string
		key         MCPPermissionCacheKey
		expectedKey string
	}{
		{
			name: "normal key",
			key: MCPPermissionCacheKey{
				MCPServerID: 123,
				AppCode:     "test-app",
			},
			expectedKey: "123:test-app",
		},
		{
			name: "zero server id",
			key: MCPPermissionCacheKey{
				MCPServerID: 0,
				AppCode:     "test-app",
			},
			expectedKey: "0:test-app",
		},
		{
			name: "empty app code",
			key: MCPPermissionCacheKey{
				MCPServerID: 123,
				AppCode:     "",
			},
			expectedKey: "123:",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.key.Key()
			assert.Equal(t, tt.expectedKey, result)
		})
	}
}

func TestGetMCPServerPermission_Success(t *testing.T) {
	expiration := 5 * time.Minute

	expectedPermission := &model.MCPServerAppPermission{
		Id:          1,
		BkAppCode:   "test-app",
		McpServerId: 123,
		GrantType:   "apply",
		Expires:     time.Now().Add(24 * time.Hour),
	}

	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return expectedPermission, nil
	}
	mockCache := memory.NewCache("mockPermissionCache", retrieveFunc, expiration, nil)
	appMCPServerPermission = mockCache

	result, err := GetMCPServerPermission(context.Background(), "test-app", 123)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	assert.Equal(t, "test-app", result.BkAppCode)
	assert.Equal(t, 123, result.McpServerId)
	assert.Equal(t, "apply", result.GrantType)
}

func TestGetMCPServerPermission_Error(t *testing.T) {
	expiration := 5 * time.Minute

	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return nil, errors.New("record not found")
	}
	mockCache := memory.NewCache("mockPermissionCache", retrieveFunc, expiration, nil)
	appMCPServerPermission = mockCache

	_, err := GetMCPServerPermission(context.Background(), "test-app", 123)
	assert.Error(t, err)
}

func TestGetMCPServerPermission_InvalidType(t *testing.T) {
	expiration := 5 * time.Minute

	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return "invalid type", nil // Return wrong type
	}
	mockCache := memory.NewCache("mockPermissionCache", retrieveFunc, expiration, nil)
	appMCPServerPermission = mockCache

	_, err := GetMCPServerPermission(context.Background(), "test-app", 123)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not model.McpServerAppPermission in cache")
}
