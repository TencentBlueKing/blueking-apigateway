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

	"github.com/TencentBlueKing/gopkg/cache"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// McpKey  is the key of mcp
type McpKey struct {
	Name string
}

// Key return the key string of stage
func (k McpKey) Key() string {
	return k.Name
}

func retrieveMcpByName(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(McpKey)
	r := repo.McpServer
	return repo.McpServer.WithContext(ctx).Where(r.Name.Eq(key.Key())).Take()
}

// GetMcpByName will return mcp by name from cache
func GetMcpByName(ctx context.Context, name string) (mcp *model.McpServer, err error) {
	key := McpKey{
		Name: name,
	}
	var value interface{}
	value, err = cacheGet(ctx, mcpCache, key)
	if err != nil {
		return
	}

	var ok bool
	mcp, ok = value.(*model.McpServer)
	if !ok {
		err = errors.New("not model.mcp in cache")
		return
	}
	return
}
