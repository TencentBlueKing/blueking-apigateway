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

var _ = Describe("MCPServerPrompt", func() {
	Describe("MCPServerPromptKey", func() {
		DescribeTable("should return correct key",
			func(mcpServerID int, expectedKey string) {
				key := cacheimpls.MCPServerPromptKey{McpServerID: mcpServerID}
				Expect(key.Key()).To(Equal(expectedKey))
			},
			Entry("normal id", 123, "123"),
			Entry("zero id", 0, "0"),
			Entry("large id", 999999, "999999"),
		)
	})

	Describe("GetMCPServerExtendByMcpServerID", func() {
		expiration := 5 * time.Minute

		It("should return MCP server extend successfully", func() {
			expectedExtend := &model.MCPServerExtend{
				ID:          1,
				McpServerID: 123,
				Type:        model.MCPServerExtendTypePrompts,
				Content:     `[{"id":1,"name":"test-prompt","code":"test","content":"Hello World"}]`,
			}

			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return expectedExtend, nil
			}
			mockCache := memory.NewCache("mockMCPServerPromptCache", retrieveFunc, expiration, nil)
			cacheimpls.SetMCPServerPromptCache(mockCache)

			result, err := cacheimpls.GetMCPServerExtendByMcpServerID(context.Background(), 123)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.McpServerID).To(Equal(123))
			Expect(result.Type).To(Equal(model.MCPServerExtendTypePrompts))
		})

		It("should return error when record not found", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return nil, errors.New("record not found")
			}
			mockCache := memory.NewCache("mockMCPServerPromptCache", retrieveFunc, expiration, nil)
			cacheimpls.SetMCPServerPromptCache(mockCache)

			_, err := cacheimpls.GetMCPServerExtendByMcpServerID(context.Background(), 999)
			Expect(err).To(HaveOccurred())
		})

		It("should return error for invalid type", func() {
			retrieveFunc := func(ctx context.Context, key cache.Key) (interface{}, error) {
				return "invalid type", nil
			}
			mockCache := memory.NewCache("mockMCPServerPromptCache", retrieveFunc, expiration, nil)
			cacheimpls.SetMCPServerPromptCache(mockCache)

			_, err := cacheimpls.GetMCPServerExtendByMcpServerID(context.Background(), 123)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("not model.MCPServerExtend in cache"))
		})
	})
})
