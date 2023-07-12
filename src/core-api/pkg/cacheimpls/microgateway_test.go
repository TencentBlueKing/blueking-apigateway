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
	"testing"
	"time"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/TencentBlueKing/gopkg/cache/memory"
	"github.com/stretchr/testify/assert"

	"core/pkg/database/dao"
)

func TestMicroGatewayKey_Key(t *testing.T) {
	k := MicroGatewayKey{
		InstanceID: "hello",
	}
	assert.Equal(t, "hello", k.Key())
}

func TestGetMicroGateway(t *testing.T) {
	expiration := 5 * time.Minute

	// valid
	retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
		return dao.MicroGateway{}, nil
	}
	mockCache := memory.NewCache(
		"mockCache", false, retrieveFunc, expiration, nil)
	microGatewayCache = mockCache

	_, err := GetMicroGateway(context.Background(), "hello")
	assert.NoError(t, err)

	// error
	retrieveFunc = func(ctx context.Context, key cache.Key) (interface{}, error) {
		return false, errors.New("error here")
	}
	mockCache = memory.NewCache(
		"mockCache", false, retrieveFunc, expiration, nil)
	microGatewayCache = mockCache

	_, err = GetMicroGateway(context.Background(), "hello")
	assert.Error(t, err)
}
