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

	"core/pkg/database/dao"

	"github.com/TencentBlueKing/gopkg/cache"
)

// MicroGatewayKey is the key of micro gateway
type MicroGatewayKey struct {
	InstanceID string
}

// Key return the key string of micro gateway
func (k MicroGatewayKey) Key() string {
	return k.InstanceID
}

func retrieveMicroGateway(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(MicroGatewayKey)

	instanceID := key.InstanceID
	manager := dao.NewMicroGatewayManager()
	return manager.Get(ctx, instanceID)
}

// GetMicroGateway will get the micro gateway object from cache by instanceID
func GetMicroGateway(ctx context.Context, instanceID string) (microGateway dao.MicroGateway, err error) {
	key := MicroGatewayKey{InstanceID: instanceID}
	var value interface{}
	value, err = cacheGet(ctx, microGatewayCache, key)
	if err != nil {
		return
	}

	var ok bool
	microGateway, ok = value.(dao.MicroGateway)
	if !ok {
		err = errors.New("not dao.MicroGateway in cache")
		return
	}
	return
}

// MicroGatewayConfig is the config of micro gateway, it configured on dashboard, saved into db as a json
// the schema is like {secret_key: {jwt_auth: xxxxx}}
// here we use the jwt_auth as the credentials of the micro gateway with the instance id
// Note: The original credentials were a JWT token, and after refactoring we changed to the instance_id + token in the header.
type MicroGatewayConfig struct {
	JwtAuth JwtAuth `json:"jwt_auth"`
}

// JwtAuth ...
type JwtAuth struct {
	SecretKey string `json:"secret_key"`
}
