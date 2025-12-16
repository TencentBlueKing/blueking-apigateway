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

var _ = Describe("JWTPublicKey", func() {
	Describe("JWTInfoCacheKey", func() {
		DescribeTable("should return correct key",
			func(gatewayID int, expectedKey string) {
				key := cacheimpls.JWTInfoCacheKey{GatewayID: gatewayID}
				Expect(key.Key()).To(Equal(expectedKey))
			},
			Entry("normal gateway id", 123, "123"),
			Entry("zero gateway id", 0, "0"),
			Entry("large gateway id", 999999, "999999"),
		)
	})

	Describe("GetJWTInfo", func() {
		expiration := 5 * time.Minute

		It("should return JWT info successfully", func() {
			expectedJWT := &model.JWT{
				GatewayID:  123,
				PublicKey:  "test-public-key",
				PrivateKey: "test-private-key",
			}

			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return expectedJWT, nil
			}
			mockCache := memory.NewCache("mockJWTCache", retrieveFunc, expiration, nil)
			cacheimpls.SetJWTInfoCache(mockCache)

			result, err := cacheimpls.GetJWTInfo(context.Background(), 123)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.GatewayID).To(Equal(123))
			Expect(result.PublicKey).To(Equal("test-public-key"))
		})

		It("should return error when record not found", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return nil, errors.New("record not found")
			}
			mockCache := memory.NewCache("mockJWTCache", retrieveFunc, expiration, nil)
			cacheimpls.SetJWTInfoCache(mockCache)

			_, err := cacheimpls.GetJWTInfo(context.Background(), 123)
			Expect(err).To(HaveOccurred())
		})

		It("should return error for invalid type", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return "invalid type", nil
			}
			mockCache := memory.NewCache("mockJWTCache", retrieveFunc, expiration, nil)
			cacheimpls.SetJWTInfoCache(mockCache)

			_, err := cacheimpls.GetJWTInfo(context.Background(), 123)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("not model.CoreJWT in cache"))
		})
	})
})
