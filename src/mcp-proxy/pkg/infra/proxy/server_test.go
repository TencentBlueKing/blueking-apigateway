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

	"mcp_proxy/pkg/constant"
)

var _ = Describe("MCPServer", func() {
	Describe("MCPServer struct operations", func() {
		var server *MCPServer

		BeforeEach(func() {
			server = &MCPServer{
				name:              "test-server",
				resourceVersionID: 1,
				tools:             make(map[string]struct{}),
				protocolType:      constant.MCPServerProtocolTypeSSE,
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

		Describe("GetProtocolType", func() {
			It("should return SSE protocol type", func() {
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeSSE))
			})

			It("should return Streamable HTTP protocol type", func() {
				server.protocolType = constant.MCPServerProtocolTypeStreamableHTTP
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeStreamableHTTP))
			})
		})

		Describe("IsStreamableHTTP", func() {
			It("should return false for SSE protocol", func() {
				server.protocolType = constant.MCPServerProtocolTypeSSE
				Expect(server.IsStreamableHTTP()).To(BeFalse())
			})

			It("should return true for Streamable HTTP protocol", func() {
				server.protocolType = constant.MCPServerProtocolTypeStreamableHTTP
				Expect(server.IsStreamableHTTP()).To(BeTrue())
			})
		})

		Describe("HandleSSE", func() {
			It("should return nil when SSEHandler is nil", func() {
				server.SSEHandler = nil
				Expect(server.HandleSSE()).To(BeNil())
			})
		})

		Describe("HandleMCP", func() {
			It("should return nil when StreamableHTTPHandler is nil", func() {
				server.StreamableHTTPHandler = nil
				Expect(server.HandleMCP()).To(BeNil())
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
						_ = server.GetProtocolType()
						_ = server.IsStreamableHTTP()
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

		Describe("GetPromptNames", func() {
			It("should return empty slice when no prompts", func() {
				Expect(server.GetPromptNames()).To(BeEmpty())
			})

			It("should return all registered prompt names", func() {
				server.prompts["prompt1"] = struct{}{}
				server.prompts["prompt2"] = struct{}{}
				server.prompts["prompt3"] = struct{}{}

				prompts := server.GetPromptNames()
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
						_ = server.GetPromptNames()
						_ = server.IsRegisteredPrompt("some-prompt")
					}()
				}

				wg.Wait()
			})
		})

		Describe("AddPrompt and RemovePrompt", func() {
			It("should add prompt to internal map", func() {
				// Directly add to internal map (since we can't call AddPrompt without a real mcp.Server)
				server.rwLock.Lock()
				server.prompts["test-prompt"] = struct{}{}
				server.rwLock.Unlock()

				Expect(server.IsRegisteredPrompt("test-prompt")).To(BeTrue())
				Expect(server.GetPromptNames()).To(ContainElement("test-prompt"))
			})

			It("should remove prompt from internal map", func() {
				// Add first
				server.rwLock.Lock()
				server.prompts["prompt-to-remove"] = struct{}{}
				server.rwLock.Unlock()

				Expect(server.IsRegisteredPrompt("prompt-to-remove")).To(BeTrue())

				// Remove
				server.rwLock.Lock()
				delete(server.prompts, "prompt-to-remove")
				server.rwLock.Unlock()

				Expect(server.IsRegisteredPrompt("prompt-to-remove")).To(BeFalse())
			})

			It("should handle multiple prompts", func() {
				server.rwLock.Lock()
				server.prompts["prompt-a"] = struct{}{}
				server.prompts["prompt-b"] = struct{}{}
				server.prompts["prompt-c"] = struct{}{}
				server.rwLock.Unlock()

				Expect(server.GetPromptNames()).To(HaveLen(3))

				// Remove one
				server.rwLock.Lock()
				delete(server.prompts, "prompt-b")
				server.rwLock.Unlock()

				Expect(server.GetPromptNames()).To(HaveLen(2))
				Expect(server.IsRegisteredPrompt("prompt-b")).To(BeFalse())
				Expect(server.IsRegisteredPrompt("prompt-a")).To(BeTrue())
				Expect(server.IsRegisteredPrompt("prompt-c")).To(BeTrue())
			})
		})
	})

	Describe("MCPServer initialization", func() {
		Describe("SSE MCPServer", func() {
			It("should have correct protocol type for SSE server", func() {
				server := &MCPServer{
					name:              "sse-server",
					resourceVersionID: 1,
					protocolType:      constant.MCPServerProtocolTypeSSE,
					tools:             make(map[string]struct{}),
					prompts:           make(map[string]struct{}),
					rwLock:            &sync.RWMutex{},
				}

				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeSSE))
				Expect(server.IsStreamableHTTP()).To(BeFalse())
				Expect(server.HandleMCP()).To(BeNil())
			})
		})

		Describe("Streamable HTTP MCPServer", func() {
			It("should have correct protocol type for Streamable HTTP server", func() {
				server := &MCPServer{
					name:              "streamable-http-server",
					resourceVersionID: 2,
					protocolType:      constant.MCPServerProtocolTypeStreamableHTTP,
					tools:             make(map[string]struct{}),
					prompts:           make(map[string]struct{}),
					rwLock:            &sync.RWMutex{},
				}

				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeStreamableHTTP))
				Expect(server.IsStreamableHTTP()).To(BeTrue())
				Expect(server.HandleSSE()).To(BeNil())
			})

			It("should initialize with correct fields", func() {
				server := &MCPServer{
					name:              "test-streamable",
					resourceVersionID: 10,
					protocolType:      constant.MCPServerProtocolTypeStreamableHTTP,
					tools:             make(map[string]struct{}),
					prompts:           make(map[string]struct{}),
					rwLock:            &sync.RWMutex{},
				}

				Expect(server.name).To(Equal("test-streamable"))
				Expect(server.GetResourceVersionID()).To(Equal(10))
				Expect(server.GetProtocolType()).To(Equal(constant.MCPServerProtocolTypeStreamableHTTP))
				Expect(server.IsStreamableHTTP()).To(BeTrue())
				Expect(server.GetTools()).To(BeEmpty())
				Expect(server.GetPromptNames()).To(BeEmpty())
			})
		})
	})
})
