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

package cacheimpls

import (
	"context"
	"errors"
	"fmt"

	"github.com/TencentBlueKing/gopkg/cache"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// McpPermissionCacheKey is the key of mcp permission
type McpPermissionCacheKey struct {
	McpServerID int
	AppCode     string
}

// Key return the key string of jwt public key
// This function returns a string representation of the GatewayID field of the McpPermissionCacheKey struct
func (k McpPermissionCacheKey) Key() string {
	// Convert the GatewayID field to a string using the cast.ToString function
	return fmt.Sprintf("%d:%s", k.McpServerID, k.AppCode)
}

// This function retrieves a permission from the cache using a given key
func retrievePermission(ctx context.Context, k cache.Key) (interface{}, error) {
	// Cast the key to the correct type
	key := k.(McpPermissionCacheKey)
	// Set the repository to the McpServerAppPermission
	r := repo.McpServerAppPermission
	// Use the CoreJWT repository to query the database for the permission
	return repo.CoreJWT.WithContext(ctx).Where(r.McpServerId.Eq(key.McpServerID), r.BkAppCode.Eq(key.AppCode)).Take()
}

// GetMcpPermission will get the mcp permission from cache by mcpServerID and appCode
func GetMcpPermission(ctx context.Context, bkAppCode string, mcpServerID int) (
	permission *model.McpServerAppPermission, err error,
) {
	key := McpPermissionCacheKey{
		McpServerID: mcpServerID,
		AppCode:     bkAppCode,
	}
	var value interface{}
	value, err = cacheGet(ctx, appMCPServerPermission, key)
	if err != nil {
		return
	}

	var ok bool
	permission, ok = value.(*model.McpServerAppPermission)
	if !ok {
		err = errors.New("not model.McpServerAppPermission in cache")
		return
	}
	return
}
