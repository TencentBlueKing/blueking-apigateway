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

var _ = Describe("MCPServer", func() {
	Describe("MCPServerKey", func() {
		DescribeTable("should return correct key",
			func(name string, expectedKey string) {
				key := cacheimpls.MCPServerKey{Name: name}
				Expect(key.Key()).To(Equal(expectedKey))
			},
			Entry("normal name", "test-server", "test-server"),
			Entry("empty name", "", ""),
			Entry("name with special characters", "test-server-123_abc", "test-server-123_abc"),
		)
	})

	Describe("GetMCPServerByName", func() {
		expiration := 5 * time.Minute

		It("should return MCP server successfully", func() {
			expectedServer := &model.MCPServer{
				ID:        1,
				Name:      "test-server",
				GatewayID: 123,
				StageID:   456,
				Status:    model.McpServerStatusActive,
			}

			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return expectedServer, nil
			}
			mockCache := memory.NewCache("mockMCPServerCache", retrieveFunc, expiration, nil)
			cacheimpls.SetMCPServerCache(mockCache)

			result, err := cacheimpls.GetMCPServerByName(context.Background(), "test-server")
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Name).To(Equal("test-server"))
			Expect(result.GatewayID).To(Equal(123))
		})

		It("should return error when record not found", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return nil, errors.New("record not found")
			}
			mockCache := memory.NewCache("mockMCPServerCache", retrieveFunc, expiration, nil)
			cacheimpls.SetMCPServerCache(mockCache)

			_, err := cacheimpls.GetMCPServerByName(context.Background(), "non-existent")
			Expect(err).To(HaveOccurred())
		})

		It("should return error for invalid type", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return "invalid type", nil
			}
			mockCache := memory.NewCache("mockMCPServerCache", retrieveFunc, expiration, nil)
			cacheimpls.SetMCPServerCache(mockCache)

			_, err := cacheimpls.GetMCPServerByName(context.Background(), "test-server")
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("not model.mcp in cache"))
		})
	})
})
