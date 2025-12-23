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
	"context"
	"net/http"
	"net/http/httptest"
	"sync"

	"github.com/gin-gonic/gin"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("MCPProxy", func() {
	Describe("NewMCPProxy", func() {
		It("should create a new MCPProxy instance", func() {
			messageUrlFormat := "/api/mcp/%s/message"
			proxy := NewMCPProxy(messageUrlFormat)

			Expect(proxy).NotTo(BeNil())
			Expect(proxy.mcpServers).NotTo(BeNil())
			Expect(proxy.rwLock).NotTo(BeNil())
			Expect(proxy.activeMCPServers).NotTo(BeNil())
			Expect(proxy.messageUrlFormat).To(Equal(messageUrlFormat))
			Expect(proxy.mcpServers).To(BeEmpty())
			Expect(proxy.activeMCPServers).To(BeEmpty())
		})
	})

	Describe("IsMCPServerExist", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should return false for non-existent server", func() {
			Expect(proxy.IsMCPServerExist("test-server")).To(BeFalse())
		})

		It("should return true for existent server", func() {
			proxy.rwLock.Lock()
			proxy.mcpServers["test-server"] = &MCPServer{}
			proxy.rwLock.Unlock()

			Expect(proxy.IsMCPServerExist("test-server")).To(BeTrue())
		})
	})

	Describe("GetMCPServer", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should return nil for non-existent server", func() {
			Expect(proxy.GetMCPServer("test-server")).To(BeNil())
		})

		It("should return server for existent server", func() {
			mockServer := &MCPServer{name: "test-server"}
			proxy.rwLock.Lock()
			proxy.mcpServers["test-server"] = mockServer
			proxy.rwLock.Unlock()

			result := proxy.GetMCPServer("test-server")
			Expect(result).NotTo(BeNil())
			Expect(result.name).To(Equal("test-server"))
		})
	})

	Describe("AddMCPServer", func() {
		It("should add server to proxy", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")
			mockServer := &MCPServer{name: "test-server"}

			proxy.AddMCPServer("test-server", mockServer)

			Expect(proxy.IsMCPServerExist("test-server")).To(BeTrue())
			Expect(proxy.GetMCPServer("test-server")).To(Equal(mockServer))
		})

		It("should add multiple servers", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")
			server1 := &MCPServer{name: "server1"}
			server2 := &MCPServer{name: "server2"}

			proxy.AddMCPServer("server1", server1)
			proxy.AddMCPServer("server2", server2)

			Expect(proxy.IsMCPServerExist("server1")).To(BeTrue())
			Expect(proxy.IsMCPServerExist("server2")).To(BeTrue())
		})
	})

	Describe("GetActiveMCPServerNames", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should return empty list initially", func() {
			names := proxy.GetActiveMCPServerNames()
			Expect(names).To(BeEmpty())
		})

		It("should return active server names", func() {
			proxy.rwLock.Lock()
			proxy.activeMCPServers["server1"] = struct{}{}
			proxy.activeMCPServers["server2"] = struct{}{}
			proxy.rwLock.Unlock()

			names := proxy.GetActiveMCPServerNames()
			Expect(names).To(HaveLen(2))
			Expect(names).To(ContainElements("server1", "server2"))
		})

		It("should return single active server", func() {
			proxy.rwLock.Lock()
			proxy.activeMCPServers["only-server"] = struct{}{}
			proxy.rwLock.Unlock()

			names := proxy.GetActiveMCPServerNames()
			Expect(names).To(HaveLen(1))
			Expect(names).To(ContainElement("only-server"))
		})
	})

	Describe("DeleteMCPServer", func() {
		It("should not panic when deleting non-existent server", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")
			Expect(func() {
				proxy.DeleteMCPServer("non-existent")
			}).NotTo(Panic())
		})

		It("should mark server as existing before deletion", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")
			proxy.rwLock.Lock()
			proxy.mcpServers["test-server"] = &MCPServer{name: "test-server"}
			proxy.activeMCPServers["test-server"] = struct{}{}
			proxy.rwLock.Unlock()

			Expect(proxy.IsMCPServerExist("test-server")).To(BeTrue())
		})
	})

	Describe("Run", func() {
		It("should not panic with no servers", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")
			ctx := context.Background()

			Expect(func() {
				proxy.Run(ctx)
			}).NotTo(Panic())
			Expect(proxy.GetActiveMCPServerNames()).To(BeEmpty())
		})

		It("should skip already active servers", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")
			ctx := context.Background()

			// Mark server as active without adding it
			proxy.rwLock.Lock()
			proxy.activeMCPServers["test-server"] = struct{}{}
			proxy.rwLock.Unlock()

			Expect(func() {
				proxy.Run(ctx)
			}).NotTo(Panic())
		})
	})

	Describe("SseHandler", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			gin.SetMode(gin.TestMode)
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should return error for non-existent server", func() {
			handler := proxy.SseHandler()
			Expect(handler).NotTo(BeNil())

			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodGet, "/mcp/non-existent/sse", nil)
			c.Params = gin.Params{{Key: "name", Value: "non-existent"}}

			handler(c)

			Expect(w.Code).To(Equal(http.StatusBadRequest))
		})
	})

	Describe("SseMessageHandler", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			gin.SetMode(gin.TestMode)
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should return error for non-existent server", func() {
			handler := proxy.SseMessageHandler()
			Expect(handler).NotTo(BeNil())

			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodPost, "/mcp/non-existent/message", nil)
			c.Params = gin.Params{{Key: "name", Value: "non-existent"}}

			handler(c)

			Expect(w.Code).To(Equal(http.StatusBadRequest))
		})
	})

	Describe("StreamableHTTPHandler", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			gin.SetMode(gin.TestMode)
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should return error for non-existent server", func() {
			handler := proxy.StreamableHTTPHandler()
			Expect(handler).NotTo(BeNil())

			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodPost, "/mcp/non-existent/mcp", nil)
			c.Params = gin.Params{{Key: "name", Value: "non-existent"}}

			handler(c)

			Expect(w.Code).To(Equal(http.StatusBadRequest))
		})

		It("should return error when server does not support Streamable HTTP protocol", func() {
			handler := proxy.StreamableHTTPHandler()
			Expect(handler).NotTo(BeNil())

			// Add a SSE server (which doesn't support Streamable HTTP)
			sseServer := &MCPServer{
				name:                  "sse-server",
				protocolType:          "sse",
				StreamableHTTPHandler: nil, // No Streamable HTTP handler
				rwLock:                &sync.RWMutex{},
				tools:                 make(map[string]struct{}),
				prompts:               make(map[string]struct{}),
			}
			proxy.AddMCPServer("sse-server", sseServer)

			w := httptest.NewRecorder()
			c, _ := gin.CreateTestContext(w)
			c.Request = httptest.NewRequest(http.MethodPost, "/mcp/sse-server/mcp", nil)
			c.Params = gin.Params{{Key: "name", Value: "sse-server"}}

			handler(c)

			Expect(w.Code).To(Equal(http.StatusBadRequest))
		})
	})

	Describe("Concurrent Access", func() {
		It("should handle concurrent reads and writes", func() {
			proxy := NewMCPProxy("/api/mcp/%s/message")

			var wg sync.WaitGroup
			for i := 0; i < 100; i++ {
				wg.Add(2)
				go func() {
					defer wg.Done()
					proxy.IsMCPServerExist("test")
					proxy.GetMCPServer("test")
					proxy.GetActiveMCPServerNames()
				}()
				go func(idx int) {
					defer wg.Done()
					server := &MCPServer{name: "server"}
					proxy.AddMCPServer("server", server)
				}(i)
			}
			wg.Wait()
		})
	})

	Describe("RegisterPromptsToMCPServer", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should not panic when server does not exist", func() {
			prompts := []*PromptConfig{
				{Name: "prompt1", Description: "desc1", Content: "content1"},
			}
			Expect(func() {
				proxy.RegisterPromptsToMCPServer("non-existent", prompts)
			}).NotTo(Panic())
		})
	})

	Describe("UpdateMCPServerPrompts", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("/api/mcp/%s/message")
		})

		It("should not panic when server does not exist", func() {
			prompts := []*PromptConfig{
				{Name: "prompt1", Description: "desc1", Content: "content1"},
			}
			Expect(func() {
				proxy.UpdateMCPServerPrompts("non-existent", prompts)
			}).NotTo(Panic())
		})
	})
})
