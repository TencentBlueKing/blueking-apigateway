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
	"fmt"

	"github.com/TencentBlueKing/gopkg/cache"
	jsoniter "github.com/json-iterator/go"
)

// MicroGatewayCredentialsCacheKey is the key of micro gateway credentials
type MicroGatewayCredentialsCacheKey struct {
	InstanceID     string
	InstanceSecret string
}

// Key return the key string of micro gateway credentials
func (k MicroGatewayCredentialsCacheKey) Key() string {
	return k.InstanceID + ":" + k.InstanceSecret
}

func retrieveAndVerifyMicroGatewayCredentials(k cache.Key) (interface{}, error) {
	key := k.(MicroGatewayCredentialsCacheKey)

	microGateway, err := GetMicroGateway(key.InstanceID)
	if err != nil {
		return false, fmt.Errorf("get micro_gateway fail, %w", err)
	}

	var config MicroGatewayConfig

	configData := microGateway.Config
	err = jsoniter.UnmarshalFromString(configData, &config)
	if err != nil {
		return false, fmt.Errorf("unmarshal micro_gateway.config fail, %w", err)
	}

	return config.JwtAuth.SecretKey == key.InstanceSecret, nil
}

// VerifyMicroGatewayCredentials will verify the micro gateway credentials from cache by instanceID and instanceSecret
// the result is cached, so it's fast
func VerifyMicroGatewayCredentials(instanceID, instanceSecret string) (bool, error) {
	key := MicroGatewayCredentialsCacheKey{
		InstanceID:     instanceID,
		InstanceSecret: instanceSecret,
	}
	var value interface{}
	value, err := microGatewayCredentialsCache.Get(key)
	if err != nil {
		return false, err
	}

	var ok bool
	allowed, ok := value.(bool)
	if !ok {
		err = errors.New("not bool in cache")
		return false, err
	}
	return allowed, nil
}
