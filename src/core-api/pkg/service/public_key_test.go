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

package service

import (
	"context"
	"errors"

	gomonkey "github.com/agiledragon/gomonkey/v2"
	"github.com/golang/mock/gomock"
	. "github.com/onsi/ginkgo/v2"
	"github.com/stretchr/testify/assert"

	"core/pkg/cacheimpls"
	"core/pkg/database/dao/mock"
)

var _ = Describe("GatewayPublicKeyService", func() {
	Describe("Get cases", func() {
		var ctl *gomock.Controller
		var instanceID, gatewayName string
		var patches *gomonkey.Patches
		var svc GatewayPublicKeyService

		BeforeEach(func() {
			patches = gomonkey.NewPatches()
			ctl = gomock.NewController(GinkgoT())
			instanceID = "hello"
			gatewayName = "world"

			mockManager := mock.NewMockJWTManager(ctl)

			svc = &gatewayPublicKeyService{
				jwtManager: mockManager,
			}
		})

		AfterEach(func() {
			ctl.Finish()
			patches.Reset()
		})

		It("error", func() {
			patches.ApplyFunc(
				getGatewayID,
				func(ctx context.Context, instanceID, gatewayName string) (int64, error) {
					return 1, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetJWTPublicKey,
				func(ctx context.Context, gatewayID int64) (string, error) {
					return "", errors.New("get GetActionDetail fail")
				},
			)

			publicKey, err := svc.Get(context.Background(), instanceID, gatewayName)
			assert.Empty(GinkgoT(), publicKey)
			assert.Error(GinkgoT(), err)
		})

		It("ok", func() {
			patches.ApplyFunc(
				getGatewayID,
				func(ctx context.Context, instanceID, gatewayName string) (int64, error) {
					return 1, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetJWTPublicKey,
				func(ctx context.Context, gatewayID int64) (string, error) {
					return "publicKey", nil
				},
			)

			publicKey, err := svc.Get(context.Background(), instanceID, gatewayName)
			assert.Equal(GinkgoT(), "publicKey", publicKey)
			assert.NoError(GinkgoT(), err)
		})
	})
})
