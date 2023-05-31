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
	"errors"

	"core/pkg/database/dao"

	"github.com/TencentBlueKing/gopkg/cache"
)

// GatewayNameKey is the key of gateway
type GatewayNameKey struct {
	Name string
}

// Key return the key string of gateway
func (k GatewayNameKey) Key() string {
	return k.Name
}

func retrieveGatewayByName(k cache.Key) (interface{}, error) {
	key := k.(GatewayNameKey)

	manager := dao.NewGatewayManager()
	return manager.GetByName(key.Name)
}

// GetGatewayByName will get the gateway object from cache by name
func GetGatewayByName(name string) (gateway dao.Gateway, err error) {
	key := GatewayNameKey{
		Name: name,
	}
	var value interface{}
	value, err = gatewayCache.Get(key)
	if err != nil {
		return
	}

	var ok bool
	gateway, ok = value.(dao.Gateway)
	if !ok {
		err = errors.New("not dao.Gateway in cache")
		return
	}
	return
}
