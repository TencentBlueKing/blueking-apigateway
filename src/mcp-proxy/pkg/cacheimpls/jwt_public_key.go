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

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
	"mcp_proxy/pkg/util"
)

// JWTInfoCacheKey is the key of jwt info
type JWTInfoCacheKey struct {
	GatewayID int
}

// Key return the key string of jwt public key
func (k JWTInfoCacheKey) Key() string {
	return cast.ToString(k.GatewayID)
}

func retrieveJWTInfo(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(JWTInfoCacheKey)
	r := repo.CoreJWT
	jwtInfo, err := repo.CoreJWT.WithContext(ctx).Where(r.GatewayID.Eq(key.GatewayID)).Take()
	if err != nil {
		return nil, err
	}
	decodePrivateKey, err := util.AESGCMDecrypt(
		config.G.McpServer.EncryptKey, config.G.McpServer.CryptoNonce, jwtInfo.EncryptedPrivateKey)
	if err != nil {
		return nil, err
	}
	jwtInfo.PrivateKey = decodePrivateKey
	return jwtInfo, nil
}

// GetJWTInfo will get the jwt info from cache by gatewayID
func GetJWTInfo(ctx context.Context, gatewayID int) (jwt *model.JWT, err error) {
	key := JWTInfoCacheKey{
		GatewayID: gatewayID,
	}
	var value interface{}
	value, err = cacheGet(ctx, jwtInfoCache, key)
	if err != nil {
		return
	}

	var ok bool
	jwt, ok = value.(*model.JWT)
	if !ok {
		err = errors.New("not model.CoreJWT in cache")
		return
	}
	return
}
