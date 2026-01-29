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
	"fmt"

	"github.com/TencentBlueKing/gopkg/cache"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// MCPPermissionCacheKey is the key of mcp permission
type MCPPermissionCacheKey struct {
	MCPServerID int
	AppCode     string
}

// Key return the key string of jwt public key
// This function returns a string representation of the GatewayID field of the MCPPermissionCacheKey struct
func (k MCPPermissionCacheKey) Key() string {
	// Convert the GatewayID field to a string using the cast.ToString function
	return fmt.Sprintf("%d:%s", k.MCPServerID, k.AppCode)
}

// This function retrieves a permission from the cache using a given key
func retrieveMCPServerPermission(ctx context.Context, k cache.Key) (interface{}, error) {
	// Cast the key to the correct type
	key := k.(MCPPermissionCacheKey)
	// Set the repository to the McpServerAppPermission
	r := repo.MCPServerAppPermission
	// Use the CoreJWT repository to query the database for the permission
	return repo.MCPServerAppPermission.WithContext(ctx).
		Where(r.McpServerId.Eq(key.MCPServerID), r.BkAppCode.Eq(key.AppCode)).
		Take()
}

// GetMCPServerPermission will get the mcp permission from cache by mcpServerID and appCode
func GetMCPServerPermission(ctx context.Context, bkAppCode string, mcpServerID int) (
	permission *model.MCPServerAppPermission, err error,
) {
	key := MCPPermissionCacheKey{
		MCPServerID: mcpServerID,
		AppCode:     bkAppCode,
	}
	var value interface{}
	value, err = cacheGet(ctx, appMCPServerPermission, key)
	if err != nil {
		return
	}

	var ok bool
	permission, ok = value.(*model.MCPServerAppPermission)
	if !ok {
		err = errors.New("invalid cache value: expected *model.MCPServerAppPermission")
		return
	}
	return
}
