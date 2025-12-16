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

var _ = Describe("MCPServerPermission", func() {
	Describe("MCPPermissionCacheKey", func() {
		DescribeTable("should return correct key",
			func(mcpServerID int, appCode string, expectedKey string) {
				key := cacheimpls.MCPPermissionCacheKey{MCPServerID: mcpServerID, AppCode: appCode}
				Expect(key.Key()).To(Equal(expectedKey))
			},
			Entry("normal key", 123, "test-app", "123:test-app"),
			Entry("zero server id", 0, "test-app", "0:test-app"),
			Entry("empty app code", 123, "", "123:"),
		)
	})

	Describe("GetMCPServerPermission", func() {
		expiration := 5 * time.Minute

		It("should return permission successfully", func() {
			expectedPermission := &model.MCPServerAppPermission{
				Id:          1,
				BkAppCode:   "test-app",
				McpServerId: 123,
				GrantType:   "apply",
				Expires:     time.Now().Add(24 * time.Hour),
			}

			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return expectedPermission, nil
			}
			mockCache := memory.NewCache("mockPermissionCache", retrieveFunc, expiration, nil)
			cacheimpls.SetAppMCPServerPermission(mockCache)

			result, err := cacheimpls.GetMCPServerPermission(context.Background(), "test-app", 123)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.BkAppCode).To(Equal("test-app"))
			Expect(result.McpServerId).To(Equal(123))
			Expect(result.GrantType).To(Equal("apply"))
		})

		It("should return error when record not found", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return nil, errors.New("record not found")
			}
			mockCache := memory.NewCache("mockPermissionCache", retrieveFunc, expiration, nil)
			cacheimpls.SetAppMCPServerPermission(mockCache)

			_, err := cacheimpls.GetMCPServerPermission(context.Background(), "test-app", 123)
			Expect(err).To(HaveOccurred())
		})

		It("should return error for invalid type", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return "invalid type", nil
			}
			mockCache := memory.NewCache("mockPermissionCache", retrieveFunc, expiration, nil)
			cacheimpls.SetAppMCPServerPermission(mockCache)

			_, err := cacheimpls.GetMCPServerPermission(context.Background(), "test-app", 123)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("not model.McpServerAppPermission in cache"))
		})
	})
})
