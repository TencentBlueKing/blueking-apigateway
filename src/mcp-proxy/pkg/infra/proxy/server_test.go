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

package proxy

import (
	"sync"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("MCPServer", func() {
	Describe("MCPServer struct operations", func() {
		var server *MCPServer

		BeforeEach(func() {
			server = &MCPServer{
				name:              "test-server",
				resourceVersionID: 1,
				tools:             make(map[string]struct{}),
				rwLock:            &sync.RWMutex{},
			}
		})

		Describe("IsRegisteredTool", func() {
			It("should return false for unregistered tool", func() {
				Expect(server.IsRegisteredTool("unknown-tool")).To(BeFalse())
			})

			It("should return true for registered tool", func() {
				server.tools["my-tool"] = struct{}{}
				Expect(server.IsRegisteredTool("my-tool")).To(BeTrue())
			})
		})

		Describe("GetResourceVersionID", func() {
			It("should return the resource version ID", func() {
				Expect(server.GetResourceVersionID()).To(Equal(1))
			})
		})

		Describe("SetResourceVersionID", func() {
			It("should set the resource version ID", func() {
				server.SetResourceVersionID(42)
				Expect(server.GetResourceVersionID()).To(Equal(42))
			})
		})

		Describe("GetTools", func() {
			It("should return empty slice when no tools", func() {
				Expect(server.GetTools()).To(BeEmpty())
			})

			It("should return all registered tool names", func() {
				server.tools["tool1"] = struct{}{}
				server.tools["tool2"] = struct{}{}
				server.tools["tool3"] = struct{}{}

				tools := server.GetTools()
				Expect(tools).To(HaveLen(3))
				Expect(tools).To(ContainElements("tool1", "tool2", "tool3"))
			})
		})

		Describe("Concurrent access", func() {
			It("should handle concurrent reads and writes", func() {
				var wg sync.WaitGroup

				// Concurrent reads
				for i := 0; i < 50; i++ {
					wg.Add(1)
					go func() {
						defer wg.Done()
						_ = server.GetResourceVersionID()
						_ = server.GetTools()
						_ = server.IsRegisteredTool("some-tool")
					}()
				}

				// Concurrent writes
				for i := 0; i < 50; i++ {
					wg.Add(1)
					go func(idx int) {
						defer wg.Done()
						server.SetResourceVersionID(idx)
					}(i)
				}

				wg.Wait()
			})
		})
	})

	Describe("ToolConfig String method", func() {
		It("should format tool config correctly", func() {
			tc := &ToolConfig{
				Name:     "testTool",
				Host:     "api.example.com",
				BasePath: "/v1",
				Url:      "/users",
				Method:   "GET",
			}

			result := tc.String()
			Expect(result).To(ContainSubstring("testTool"))
			Expect(result).To(ContainSubstring("GET"))
		})
	})

	Describe("Prompt operations", func() {
		var server *MCPServer

		BeforeEach(func() {
			server = &MCPServer{
				name:              "test-server",
				resourceVersionID: 1,
				tools:             make(map[string]struct{}),
				prompts:           make(map[string]struct{}),
				rwLock:            &sync.RWMutex{},
			}
		})

		Describe("IsRegisteredPrompt", func() {
			It("should return false for unregistered prompt", func() {
				Expect(server.IsRegisteredPrompt("unknown-prompt")).To(BeFalse())
			})

			It("should return true for registered prompt", func() {
				server.prompts["my-prompt"] = struct{}{}
				Expect(server.IsRegisteredPrompt("my-prompt")).To(BeTrue())
			})
		})

		Describe("GetPrompts", func() {
			It("should return empty slice when no prompts", func() {
				Expect(server.GetPrompts()).To(BeEmpty())
			})

			It("should return all registered prompt names", func() {
				server.prompts["prompt1"] = struct{}{}
				server.prompts["prompt2"] = struct{}{}
				server.prompts["prompt3"] = struct{}{}

				prompts := server.GetPrompts()
				Expect(prompts).To(HaveLen(3))
				Expect(prompts).To(ContainElements("prompt1", "prompt2", "prompt3"))
			})
		})

		Describe("Concurrent prompt access", func() {
			It("should handle concurrent reads and writes for prompts", func() {
				var wg sync.WaitGroup

				// Concurrent reads
				for i := 0; i < 50; i++ {
					wg.Add(1)
					go func() {
						defer wg.Done()
						_ = server.GetPrompts()
						_ = server.IsRegisteredPrompt("some-prompt")
					}()
				}

				wg.Wait()
			})
		})
	})
})
