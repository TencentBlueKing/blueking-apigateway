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
	"github.com/spf13/cast"

	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// GatewayIDKey is the key of gateway
type GatewayIDKey struct {
	ID int
}

// Key return the key string of gateway
func (k GatewayIDKey) Key() string {
	return cast.ToString(k.ID)
}

func retrieveGatewayByID(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(GatewayIDKey)
	r := repo.Gateway
	return repo.Gateway.WithContext(ctx).Where(r.ID.Eq(key.ID)).Take()
}

// GetGatewayByID GetGatewayByName will get the gateway object from cache by name
func GetGatewayByID(ctx context.Context, id int) (gateway *model.Gateway, err error) {
	key := GatewayIDKey{
		ID: id,
	}
	var value interface{}
	value, err = cacheGet(ctx, gatewayIDCache, key)
	if err != nil {
		return
	}
	var ok bool
	gateway, ok = value.(*model.Gateway)
	if !ok {
		err = errors.New("not model.Gateway in cache")
		return
	}
	return
}

// GatewayNameKey is the key of gateway
type GatewayNameKey struct {
	Name string
}

// Key return the key string of gateway
// This function returns a string representation of the GatewayIDKey's ID
func (k GatewayNameKey) Key() string {
	// Convert the ID to a string using the cast package
	return cast.ToString(k.Name)
}

func retrieveGatewayByName(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(GatewayNameKey)
	r := repo.Gateway
	return repo.Gateway.WithContext(ctx).Where(r.Name.Eq(key.Name)).Take()
}

// GetGatewayByName will get the gateway object from cache by name
func GetGatewayByName(ctx context.Context, name string) (gateway *model.Gateway, err error) {
	key := GatewayNameKey{
		Name: name,
	}
	var value interface{}
	value, err = cacheGet(ctx, gatewayNameCache, key)
	if err != nil {
		return
	}
	var ok bool
	gateway, ok = value.(*model.Gateway)
	if !ok {
		err = errors.New("not model.Gateway in cache")
		return
	}
	return
}
