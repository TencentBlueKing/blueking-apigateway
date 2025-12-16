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

package cacheimpls_test

import (
	"context"
	"errors"
	"time"

	"github.com/TencentBlueKing/gopkg/cache"
	"github.com/TencentBlueKing/gopkg/cache/memory"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/entity/model"
)

var _ = Describe("Gateway", func() {
	Describe("GatewayIDKey", func() {
		It("should return correct key", func() {
			k := cacheimpls.GatewayIDKey{ID: 1}
			Expect(k.Key()).To(Equal("1"))
		})
	})

	Describe("GetGatewayByID", func() {
		expiration := 5 * time.Minute

		It("should return gateway successfully", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return &model.Gateway{}, nil
			}
			mockCache := memory.NewCache("mockCache", retrieveFunc, expiration, nil)
			cacheimpls.SetGatewayIDCache(mockCache)

			_, err := cacheimpls.GetGatewayByID(context.Background(), 1)
			Expect(err).NotTo(HaveOccurred())
		})

		It("should return error when retrieval fails", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return false, errors.New("error here")
			}
			mockCache := memory.NewCache("mockCache", retrieveFunc, expiration, nil)
			cacheimpls.SetGatewayIDCache(mockCache)

			_, err := cacheimpls.GetGatewayByID(context.Background(), 1)
			Expect(err).To(HaveOccurred())
		})
	})
})
