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
	"strconv"

	"core/pkg/database/dao"

	"github.com/TencentBlueKing/gopkg/cache"
)

// JWTPublicKeyCacheKey is the key of jwt public key
type JWTPublicKeyCacheKey struct {
	GatewayID int64
}

// Key return the key string of jwt public key
func (k JWTPublicKeyCacheKey) Key() string {
	return strconv.FormatInt(k.GatewayID, 10)
}

func retrieveJWTPublicKey(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(JWTPublicKeyCacheKey)

	manager := dao.NewJWTManager()

	jwt, err := manager.Get(ctx, key.GatewayID)
	if err != nil {
		return "", err
	}

	return jwt.PublicKey, nil
}

// GetJWTPublicKey will get the jwt public key from cache by gatewayID
func GetJWTPublicKey(ctx context.Context, gatewayID int64) (publicKey string, err error) {
	key := JWTPublicKeyCacheKey{
		GatewayID: gatewayID,
	}
	var value interface{}
	value, err = cacheGet(ctx, jwtPublicKeyCache, key)
	if err != nil {
		return
	}

	var ok bool
	publicKey, ok = value.(string)
	if !ok {
		err = errors.New("not string in cache")
		return
	}
	return
}
