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
	"strconv"

	"github.com/TencentBlueKing/gopkg/cache"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// MCPServerExtendKey is the key for mcp server prompt cache
type MCPServerExtendKey struct {
	McpServerID int
	Type        string
}

// Key return the key string
func (k MCPServerExtendKey) Key() string {
	return strconv.Itoa(k.McpServerID)
}

func retrieveMCPServerExtendByMcpServerID(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(MCPServerExtendKey)
	r := repo.MCPServerExtend
	return repo.MCPServerExtend.WithContext(ctx).
		Where(r.McpServerID.Eq(key.McpServerID)).
		Where(r.Type.Eq(key.Type)).Take()
}

// GetMCPServerExtendByMcpServerID 根据 MCP Server ID 获取扩展配置
func GetMCPServerExtendByMcpServerID(ctx context.Context, mcpServerID int, extendType string) (
	extend *model.MCPServerExtend, err error,
) {
	key := MCPServerExtendKey{
		McpServerID: mcpServerID,
		Type:        extendType,
	}
	var value interface{}
	value, err = cacheGet(ctx, mcpServerExtendCache, key)
	if err != nil {
		return
	}

	var ok bool
	extend, ok = value.(*model.MCPServerExtend)
	if !ok {
		err = errors.New("not model.MCPServerExtend in cache")
		return
	}
	return
}
