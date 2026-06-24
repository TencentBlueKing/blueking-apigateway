/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/go-openapi/runtime"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/propagation"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/bkaidevtrace"
	"mcp_proxy/pkg/infra/trace"
	"mcp_proxy/pkg/util"
)

var _ = Describe("MCPProxy", func() {
	Describe("NewMCPProxy", func() {
		It("should create a new MCPProxy instance", func() {
			proxy := NewMCPProxy("", "")

			Expect(proxy).NotTo(BeNil())
			Expect(proxy.mcpServers).NotTo(BeNil())
			Expect(proxy.rwLock).NotTo(BeNil())
			Expect(proxy.activeMCPServers).NotTo(BeNil())
			Expect(proxy.mcpServers).To(BeEmpty())
			Expect(proxy.activeMCPServers).To(BeEmpty())
		})
	})

	Describe("IsMCPServerExist", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("", "")
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
			proxy = NewMCPProxy("", "")
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
			proxy := NewMCPProxy("", "")
			mockServer := &MCPServer{name: "test-server"}

			proxy.AddMCPServer("test-server", mockServer)

			Expect(proxy.IsMCPServerExist("test-server")).To(BeTrue())
			Expect(proxy.GetMCPServer("test-server")).To(Equal(mockServer))
		})

		It("should add multiple servers", func() {
			proxy := NewMCPProxy("", "")
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
			proxy = NewMCPProxy("", "")
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
			proxy := NewMCPProxy("", "")
			Expect(func() {
				proxy.DeleteMCPServer("non-existent")
			}).NotTo(Panic())
		})

		It("should mark server as existing before deletion", func() {
			proxy := NewMCPProxy("", "")
			proxy.rwLock.Lock()
			proxy.mcpServers["test-server"] = &MCPServer{name: "test-server"}
			proxy.activeMCPServers["test-server"] = struct{}{}
			proxy.rwLock.Unlock()

			Expect(proxy.IsMCPServerExist("test-server")).To(BeTrue())
		})
	})

	Describe("CleanupAll", func() {
		// newTestMCPServer creates a minimal MCPServer suitable for testing.
		newTestMCPServer := func(name string) *MCPServer {
			return &MCPServer{
				Server:  mcp.NewServer(&mcp.Implementation{Name: name}, nil),
				name:    name,
				rwLock:  &sync.RWMutex{},
				tools:   make(map[string]struct{}),
				prompts: make(map[string]struct{}),
			}
		}

		It("should return empty list when no servers exist", func() {
			proxy := NewMCPProxy("", "")
			names := proxy.CleanupAll()
			Expect(names).To(BeEmpty())
			Expect(proxy.GetActiveMCPServerNames()).To(BeEmpty())
		})

		It("should remove all servers and return their names", func() {
			proxy := NewMCPProxy("", "")
			// Manually add servers and mark them as active
			proxy.rwLock.Lock()
			proxy.mcpServers["server1"] = newTestMCPServer("server1")
			proxy.mcpServers["server2"] = newTestMCPServer("server2")
			proxy.activeMCPServers["server1"] = struct{}{}
			proxy.activeMCPServers["server2"] = struct{}{}
			proxy.rwLock.Unlock()

			Expect(proxy.IsMCPServerExist("server1")).To(BeTrue())
			Expect(proxy.IsMCPServerExist("server2")).To(BeTrue())

			names := proxy.CleanupAll()
			Expect(names).To(HaveLen(2))
			Expect(names).To(ContainElements("server1", "server2"))

			// Verify all servers are cleaned up
			Expect(proxy.IsMCPServerExist("server1")).To(BeFalse())
			Expect(proxy.IsMCPServerExist("server2")).To(BeFalse())
			Expect(proxy.GetActiveMCPServerNames()).To(BeEmpty())
		})

		It("should be safe to call multiple times", func() {
			proxy := NewMCPProxy("", "")
			proxy.rwLock.Lock()
			proxy.mcpServers["server1"] = newTestMCPServer("server1")
			proxy.activeMCPServers["server1"] = struct{}{}
			proxy.rwLock.Unlock()

			names := proxy.CleanupAll()
			Expect(names).To(HaveLen(1))

			// Second call should return empty
			names = proxy.CleanupAll()
			Expect(names).To(BeEmpty())
		})
	})

	Describe("CleanupStale", func() {
		newTestMCPServer := func(name string) *MCPServer {
			return &MCPServer{
				Server:  mcp.NewServer(&mcp.Implementation{Name: name}, nil),
				name:    name,
				rwLock:  &sync.RWMutex{},
				tools:   make(map[string]struct{}),
				prompts: make(map[string]struct{}),
			}
		}

		It("should return empty when no servers exist", func() {
			proxy := NewMCPProxy("", "")
			deleted := proxy.CleanupStale(map[string]struct{}{})
			Expect(deleted).To(BeEmpty())
		})

		It("should delete servers not in active set", func() {
			proxy := NewMCPProxy("", "")
			proxy.rwLock.Lock()
			proxy.mcpServers["server1"] = newTestMCPServer("server1")
			proxy.mcpServers["server2"] = newTestMCPServer("server2")
			proxy.mcpServers["server3"] = newTestMCPServer("server3")
			proxy.activeMCPServers["server1"] = struct{}{}
			proxy.activeMCPServers["server2"] = struct{}{}
			proxy.activeMCPServers["server3"] = struct{}{}
			proxy.rwLock.Unlock()

			activeSet := map[string]struct{}{
				"server1": {},
				"server3": {},
			}
			deleted := proxy.CleanupStale(activeSet)

			Expect(deleted).To(HaveLen(1))
			Expect(deleted).To(ContainElement("server2"))
			Expect(proxy.IsMCPServerExist("server1")).To(BeTrue())
			Expect(proxy.IsMCPServerExist("server2")).To(BeFalse())
			Expect(proxy.IsMCPServerExist("server3")).To(BeTrue())
		})

		It("should return empty when all servers are active", func() {
			proxy := NewMCPProxy("", "")
			proxy.rwLock.Lock()
			proxy.mcpServers["server1"] = newTestMCPServer("server1")
			proxy.activeMCPServers["server1"] = struct{}{}
			proxy.rwLock.Unlock()

			activeSet := map[string]struct{}{
				"server1": {},
			}
			deleted := proxy.CleanupStale(activeSet)
			Expect(deleted).To(BeEmpty())
			Expect(proxy.IsMCPServerExist("server1")).To(BeTrue())
		})

		It("should delete all servers when active set is empty", func() {
			proxy := NewMCPProxy("", "")
			proxy.rwLock.Lock()
			proxy.mcpServers["server1"] = newTestMCPServer("server1")
			proxy.mcpServers["server2"] = newTestMCPServer("server2")
			proxy.activeMCPServers["server1"] = struct{}{}
			proxy.activeMCPServers["server2"] = struct{}{}
			proxy.rwLock.Unlock()

			deleted := proxy.CleanupStale(map[string]struct{}{})
			Expect(deleted).To(HaveLen(2))
			Expect(deleted).To(ContainElements("server1", "server2"))
			Expect(proxy.GetActiveMCPServerNames()).To(BeEmpty())
		})
	})

	Describe("Run", func() {
		It("should not panic with no servers", func() {
			proxy := NewMCPProxy("", "")
			ctx := context.Background()

			Expect(func() {
				proxy.Run(ctx)
			}).NotTo(Panic())
			Expect(proxy.GetActiveMCPServerNames()).To(BeEmpty())
		})

		It("should skip already active servers", func() {
			proxy := NewMCPProxy("", "")
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
			proxy = NewMCPProxy("", "")
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

	Describe("StreamableHTTPHandler", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			gin.SetMode(gin.TestMode)
			proxy = NewMCPProxy("", "")
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
			proxy := NewMCPProxy("", "")

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

	Describe("buildMCPTool", func() {
		It("should build tool without output schema", func() {
			tool := buildMCPTool(&ToolConfig{
				Name:        "getUsers",
				Description: "Get users",
			}, "test-server")

			Expect(tool).NotTo(BeNil())
			Expect(tool.InputSchema).NotTo(BeNil())
			Expect(tool.OutputSchema).To(BeNil())
		})
	})

	Describe("buildToolResponseEnvelope", func() {
		It("should include response_body as nil when body is nil", func() {
			envelope := buildToolResponseEnvelope(204, "req-1", "trace-1", "x-req-1", nil)

			Expect(envelope).To(Equal(map[string]any{
				toolResponseStatusCodeField: 204,
				toolResponseRequestIDField:  "req-1",
				toolResponseTraceIDField:    "trace-1",
				toolResponseXRequestIDField: "x-req-1",
				toolResponseBodyField:       nil,
			}))
		})
	})

	Describe("buildToolResult", func() {
		It("should populate text content for envelope with object body", func() {
			envelope := buildToolResponseEnvelope(200, "req-1", "trace-1", "x-req-1", map[string]any{
				"timezone": "Asia/Shanghai",
				"datetime": "2026-03-19T15:04:05+08:00",
			})
			result := buildToolResult(envelope)

			Expect(result).NotTo(BeNil())
			Expect(result.StructuredContent).To(BeNil())
			Expect(result.Content).To(HaveLen(1))
			Expect(result.Content[0]).To(BeAssignableToTypeOf(&mcp.TextContent{}))
			Expect(
				result.Content[0].(*mcp.TextContent).Text,
			).To(MatchJSON(`{"status_code":200,"request_id":"req-1","trace_id":"trace-1","x_request_id":"x-req-1","response_body":{"datetime":"2026-03-19T15:04:05+08:00","timezone":"Asia/Shanghai"}}`))
		})

		It("should populate text content for envelope with array body", func() {
			envelope := buildToolResponseEnvelope(200, "req-1", "trace-1", "x-req-1", []any{"a", "b"})
			result := buildToolResult(envelope)

			Expect(result).NotTo(BeNil())
			Expect(result.StructuredContent).To(BeNil())
			Expect(result.Content).To(HaveLen(1))
			Expect(result.Content[0]).To(BeAssignableToTypeOf(&mcp.TextContent{}))
			Expect(
				result.Content[0].(*mcp.TextContent).Text,
			).To(MatchJSON(`{"status_code":200,"request_id":"req-1","trace_id":"trace-1","x_request_id":"x-req-1","response_body":["a","b"]}`))
		})

		It("should return raw API response directly when rawResponseEnabled is enabled", func() {
			// When rawResponseEnabled is true, the response result is the raw API response (not wrapped in
			// envelope)
			rawBody := map[string]any{
				"timezone": "Asia/Shanghai",
				"datetime": "2026-03-19T15:04:05+08:00",
			}
			result := buildToolResult(rawBody)

			Expect(result).NotTo(BeNil())
			Expect(result.Content).To(HaveLen(1))
			Expect(result.Content[0]).To(BeAssignableToTypeOf(&mcp.TextContent{}))
			// Raw response should NOT contain status_code, request_id, trace_id, x_request_id wrapper
			Expect(
				result.Content[0].(*mcp.TextContent).Text,
			).To(MatchJSON(`{"timezone":"Asia/Shanghai","datetime":"2026-03-19T15:04:05+08:00"}`))
		})

		It("should return raw string response directly when rawResponseEnabled is enabled", func() {
			rawBody := "plain text response"
			result := buildToolResult(rawBody)

			Expect(result).NotTo(BeNil())
			Expect(result.Content).To(HaveLen(1))
			Expect(result.Content[0]).To(BeAssignableToTypeOf(&mcp.TextContent{}))
			Expect(result.Content[0].(*mcp.TextContent).Text).To(Equal(`"plain text response"`))
		})
	})

	Describe("buildLoggingTransport", func() {
		It("should populate gateway name from context", func() {
			ctx := context.WithValue(context.Background(), constant.GatewayName, "test-gateway")
			toolConfig := &ToolConfig{
				Name:   "test-tool",
				Host:   "https://example.com",
				Url:    "/ping",
				Method: http.MethodGet,
			}

			transport := buildLoggingTransport(
				ctx,
				http.DefaultTransport,
				toolConfig,
				"test-app",
				"tester",
				"req-1",
				"x-req-1",
				"test-mcp-server",
			)

			Expect(transport).NotTo(BeNil())
			Expect(transport.gatewayName).To(Equal("test-gateway"))
			Expect(transport.mcpServerName).To(Equal("test-mcp-server"))
			Expect(transport.requestID).To(Equal("req-1"))
			Expect(transport.xRequestID).To(Equal("x-req-1"))
			Expect(transport.toolName).To(Equal(toolConfig.String()))
		})
	})

	Describe("RegisterPromptsToMCPServer", func() {
		var proxy *MCPProxy

		BeforeEach(func() {
			proxy = NewMCPProxy("", "")
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
			proxy = NewMCPProxy("", "")
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

	Describe("genPromptAndHandler", func() {
		It("should generate prompt with correct name and description", func() {
			config := &PromptConfig{
				Name:        "test-prompt",
				Description: "Test prompt description",
				Content:     "This is the prompt content",
			}

			prompt, handler := genPromptAndHandler(config)

			Expect(prompt).NotTo(BeNil())
			Expect(prompt.Name).To(Equal("test-prompt"))
			Expect(prompt.Description).To(Equal("Test prompt description"))
			Expect(handler).NotTo(BeNil())
		})

		It("should generate handler that returns correct result", func() {
			config := &PromptConfig{
				Name:        "greeting-prompt",
				Description: "A greeting prompt",
				Content:     "Hello, how can I help you?",
			}

			_, handler := genPromptAndHandler(config)

			ctx := context.Background()
			result, err := handler(ctx, nil)

			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Description).To(Equal("A greeting prompt"))
			Expect(result.Messages).To(HaveLen(1))
			Expect(string(result.Messages[0].Role)).To(Equal("user"))
		})

		It("should handle empty config", func() {
			config := &PromptConfig{}

			prompt, handler := genPromptAndHandler(config)

			Expect(prompt).NotTo(BeNil())
			Expect(prompt.Name).To(BeEmpty())
			Expect(prompt.Description).To(BeEmpty())
			Expect(handler).NotTo(BeNil())

			ctx := context.Background()
			result, err := handler(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.Messages).To(HaveLen(1))
		})
	})

	Describe("InitSharedTransport", func() {
		BeforeEach(func() {
			// Reset sync.Once so each test starts fresh
			sharedTransportOnce = sync.Once{}
			sharedTransport = nil
		})

		It("should initialize shared transport with config values", func() {
			cfg := config.Transport{
				InsecureSkipVerify:    true,
				MaxIdleConns:          100,
				MaxIdleConnsPerHost:   10,
				IdleConnTimeoutSecond: 60,
			}
			InitSharedTransport(cfg)

			Expect(sharedTransport).NotTo(BeNil())
			Expect(sharedTransport.MaxIdleConns).To(Equal(100))
			Expect(sharedTransport.MaxIdleConnsPerHost).To(Equal(10))
			Expect(sharedTransport.IdleConnTimeout).To(Equal(60 * time.Second))
			Expect(sharedTransport.TLSClientConfig).NotTo(BeNil())
			Expect(sharedTransport.TLSClientConfig.InsecureSkipVerify).To(BeTrue())
		})

		It("should only initialize once and ignore subsequent calls", func() {
			InitSharedTransport(config.Transport{MaxIdleConns: 50})
			Expect(sharedTransport.MaxIdleConns).To(Equal(50))

			// Second call should be a no-op
			InitSharedTransport(config.Transport{MaxIdleConns: 200})
			Expect(sharedTransport.MaxIdleConns).To(Equal(50))
		})
	})

	Describe("setupBkAIDevToolCallSpan", func() {
		It("should create tools/call span with expected attributes", func() {
			bkaidevtrace.ResetForTest()
			exporter := tracetest.NewInMemoryExporter()
			tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exporter))
			defer func() {
				_ = tp.Shutdown(context.Background())
				bkaidevtrace.ResetForTest()
			}()
			bkaidevtrace.SetTestProvider(tp, propagation.NewCompositeTextMapPropagator(
				propagation.TraceContext{},
				propagation.Baggage{},
			))

			ctx := context.Background()
			ctx = context.WithValue(ctx, constant.BkAppCode, "test-app")
			ctx = context.WithValue(ctx, constant.BkUsername, "tester")
			ctx = context.WithValue(ctx, constant.ClientIP, "127.0.0.1")
			ctx = context.WithValue(ctx, constant.ClientID, "client-a")
			ctx = context.WithValue(ctx, constant.GatewayName, "gw-a")
			ctx = context.WithValue(ctx, constant.RequestID, "req-1")
			ctx = context.WithValue(ctx, constant.XRequestID, "x-req-1")
			ctx = context.WithValue(ctx, constant.BkApiItsmFlexData, &util.ItsmFlexData{
				CallerExecutor:   "judge-caller",
				AgentCode:        "ai-test-appcode",
				ServiceCatalogue: "test1/test2/test3",
				CallerBizEnv:     "public",
				CallerBizID:      "6000086",
			})

			_, span := setupBkAIDevToolCallSpan(ctx, nil, "test-server", "test-tool")
			Expect(span).NotTo(BeNil())
			span.End()

			spans := exporter.GetSpans()
			Expect(spans).To(HaveLen(1))
			Expect(spans[0].Name).To(Equal("mcp_gw.test-server.tools/call"))

			attrMap := make(map[string]any)
			for _, attr := range spans[0].Attributes {
				attrMap[string(attr.Key)] = attr.Value.AsInterface()
			}
			Expect(attrMap["mcp_server_name"]).To(Equal("test-server"))
			Expect(attrMap["tool_name"]).To(Equal("test-tool"))
			Expect(attrMap["app_code"]).To(Equal("test-app"))
			Expect(attrMap["service_catalogue"]).To(Equal("test1/test2/test3"))
			Expect(attrMap["caller_bk_biz_env"]).To(Equal("public"))
			Expect(attrMap["caller_bk_biz_id"]).To(Equal("6000086"))
		})
	})

	Describe("loggingTransport", func() {
		var (
			originalConfig     *config.Config
			originalPropagator propagation.TextMapPropagator
		)

		BeforeEach(func() {
			originalConfig = config.G
			originalPropagator = otel.GetTextMapPropagator()
		})

		AfterEach(func() {
			config.G = originalConfig
			otel.SetTextMapPropagator(originalPropagator)
		})

		It("should inject traceparent header when tracing is enabled", func() {
			// Set up an in-memory span exporter and trace provider
			exporter := tracetest.NewInMemoryExporter()
			tp := sdktrace.NewTracerProvider(
				sdktrace.WithSyncer(exporter),
			)
			defer func() { _ = tp.Shutdown(context.Background()) }()

			otel.SetTracerProvider(tp)
			otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
				propagation.TraceContext{},
				propagation.Baggage{},
			))

			// Set the global tracer used by trace.StartTrace
			cleanup := trace.SetGlobalTracerForTest(
				tp.Tracer("test-service"),
				config.Tracing{Enable: true},
			)
			defer cleanup()

			// Enable MCP tracing via config
			config.G = &config.Config{
				Tracing: config.Tracing{
					Enable:      true,
					ServiceName: "test-service",
					Instrument:  config.Instrument{McpAPI: true},
				},
			}

			// Create a test backend that captures the incoming request headers
			var capturedHeaders http.Header
			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				capturedHeaders = r.Header.Clone()
				w.WriteHeader(http.StatusOK)
			}))
			defer backend.Close()

			logger := zap.NewNop().Sugar()
			transport := &loggingTransport{
				base:     backend.Client().Transport,
				logger:   logger,
				toolName: "test-tool",
			}

			req, err := http.NewRequest(http.MethodGet, backend.URL, nil)
			Expect(err).NotTo(HaveOccurred())

			resp, err := transport.RoundTrip(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(resp.StatusCode).To(Equal(http.StatusOK))
			_ = resp.Body.Close()

			// Verify traceparent header was injected
			traceparent := capturedHeaders.Get("Traceparent")
			Expect(traceparent).NotTo(BeEmpty(), "traceparent header should be injected")
			// W3C traceparent format: version-trace_id-span_id-flags (e.g. "00-xxx-yyy-01")
			Expect(traceparent).To(MatchRegexp(`^00-[a-f0-9]{32}-[a-f0-9]{16}-[a-f0-9]{2}$`))
		})

		It("should NOT inject traceparent header when tracing is disabled", func() {
			// Tracing disabled: config.G is nil or McpAPI is false
			config.G = nil

			var capturedHeaders http.Header
			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				capturedHeaders = r.Header.Clone()
				w.WriteHeader(http.StatusOK)
			}))
			defer backend.Close()

			logger := zap.NewNop().Sugar()
			transport := &loggingTransport{
				base:     backend.Client().Transport,
				logger:   logger,
				toolName: "test-tool",
			}

			req, err := http.NewRequest(http.MethodGet, backend.URL, nil)
			Expect(err).NotTo(HaveOccurred())

			resp, err := transport.RoundTrip(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(resp.StatusCode).To(Equal(http.StatusOK))
			_ = resp.Body.Close()

			// Verify traceparent header was NOT injected
			traceparent := capturedHeaders.Get("Traceparent")
			Expect(
				traceparent,
			).To(
				BeEmpty(),
				"traceparent header should NOT be injected when tracing is disabled",
			)
		})

		It("should NOT inject traceparent when McpAPI is false but tracing is enabled", func() {
			exporter := tracetest.NewInMemoryExporter()
			tp := sdktrace.NewTracerProvider(
				sdktrace.WithSyncer(exporter),
			)
			defer func() { _ = tp.Shutdown(context.Background()) }()

			otel.SetTracerProvider(tp)
			otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
				propagation.TraceContext{},
			))

			// Tracing enabled but McpAPI disabled
			config.G = &config.Config{
				Tracing: config.Tracing{
					Enable:      true,
					ServiceName: "test-service",
					Instrument:  config.Instrument{McpAPI: false},
				},
			}

			var capturedHeaders http.Header
			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				capturedHeaders = r.Header.Clone()
				w.WriteHeader(http.StatusOK)
			}))
			defer backend.Close()

			logger := zap.NewNop().Sugar()
			transport := &loggingTransport{
				base:     backend.Client().Transport,
				logger:   logger,
				toolName: "test-tool",
			}

			req, err := http.NewRequest(http.MethodGet, backend.URL, nil)
			Expect(err).NotTo(HaveOccurred())

			resp, err := transport.RoundTrip(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(resp.StatusCode).To(Equal(http.StatusOK))
			_ = resp.Body.Close()

			traceparent := capturedHeaders.Get("Traceparent")
			Expect(traceparent).To(BeEmpty(), "traceparent should NOT be injected when McpAPI is disabled")
		})

		It("should set span attributes correctly when tracing is enabled", func() {
			exporter := tracetest.NewInMemoryExporter()
			tp := sdktrace.NewTracerProvider(
				sdktrace.WithSyncer(exporter),
			)
			defer func() { _ = tp.Shutdown(context.Background()) }()

			otel.SetTracerProvider(tp)
			otel.SetTextMapPropagator(propagation.TraceContext{})

			cleanup := trace.SetGlobalTracerForTest(
				tp.Tracer("test-service"),
				config.Tracing{Enable: true},
			)
			defer cleanup()

			config.G = &config.Config{
				Tracing: config.Tracing{
					Enable:      true,
					ServiceName: "test-service",
					Instrument:  config.Instrument{McpAPI: true},
				},
			}

			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusOK)
			}))
			defer backend.Close()

			logger := zap.NewNop().Sugar()
			transport := &loggingTransport{
				base:     backend.Client().Transport,
				logger:   logger,
				toolName: "my-tool",
			}

			req, err := http.NewRequest(http.MethodPost, backend.URL+"/test/path", nil)
			Expect(err).NotTo(HaveOccurred())

			resp, err := transport.RoundTrip(req)
			Expect(err).NotTo(HaveOccurred())
			_ = resp.Body.Close()

			// Verify span was created with expected attributes
			spans := exporter.GetSpans()
			Expect(spans).To(HaveLen(1))
			span := spans[0]
			Expect(span.Name).To(Equal("mcp.upstream_http"))

			attrMap := make(map[string]any)
			for _, attr := range span.Attributes {
				attrMap[string(attr.Key)] = attr.Value.AsInterface()
			}
			Expect(attrMap).To(HaveKey("http.method"))
			Expect(attrMap).To(HaveKey("mcp.tool_name"))
			Expect(attrMap["mcp.tool_name"]).To(Equal("my-tool"))
		})

		It("should record error span attributes on HTTP failure", func() {
			exporter := tracetest.NewInMemoryExporter()
			tp := sdktrace.NewTracerProvider(
				sdktrace.WithSyncer(exporter),
			)
			defer func() { _ = tp.Shutdown(context.Background()) }()

			otel.SetTracerProvider(tp)
			otel.SetTextMapPropagator(propagation.TraceContext{})

			cleanup := trace.SetGlobalTracerForTest(
				tp.Tracer("test-service"),
				config.Tracing{Enable: true},
			)
			defer cleanup()

			config.G = &config.Config{
				Tracing: config.Tracing{
					Enable:      true,
					ServiceName: "test-service",
					Instrument:  config.Instrument{McpAPI: true},
				},
			}

			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusInternalServerError)
			}))
			defer backend.Close()

			logger := zap.NewNop().Sugar()
			transport := &loggingTransport{
				base:     backend.Client().Transport,
				logger:   logger,
				toolName: "fail-tool",
			}

			req, err := http.NewRequest(http.MethodGet, backend.URL, nil)
			Expect(err).NotTo(HaveOccurred())

			resp, err := transport.RoundTrip(req)
			Expect(err).NotTo(HaveOccurred())
			_ = resp.Body.Close()

			spans := exporter.GetSpans()
			Expect(spans).To(HaveLen(1))

			attrMap := make(map[string]any)
			for _, attr := range spans[0].Attributes {
				attrMap[string(attr.Key)] = attr.Value.AsInterface()
			}
			// http.status_code should be set
			Expect(attrMap).To(HaveKey("http.status_code"))
			Expect(attrMap["http.status_code"]).To(Equal(int64(500)))
		})

		It("should include gateway name in outgoing logs", func() {
			var buf bytes.Buffer
			encoder := zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())
			core := zapcore.NewCore(encoder, zapcore.AddSync(&buf), zap.InfoLevel)
			logger := zap.New(core).Sugar()

			backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusOK)
			}))
			defer backend.Close()

			transport := &loggingTransport{
				base:        backend.Client().Transport,
				logger:      logger,
				gatewayName: "test-gateway",
				toolName:    "test-tool",
			}

			req, err := http.NewRequest(http.MethodGet, backend.URL, nil)
			Expect(err).NotTo(HaveOccurred())

			resp, err := transport.RoundTrip(req)
			Expect(err).NotTo(HaveOccurred())
			_ = resp.Body.Close()

			lines := strings.Split(strings.TrimSpace(buf.String()), "\n")
			Expect(lines).To(HaveLen(2))

			var requestLog map[string]any
			Expect(json.Unmarshal([]byte(lines[0]), &requestLog)).To(Succeed())
			Expect(requestLog).To(HaveKeyWithValue("msg", "outgoing request"))
			Expect(requestLog).To(HaveKeyWithValue("gateway_name", "test-gateway"))

			var responseLog map[string]any
			Expect(json.Unmarshal([]byte(lines[1]), &responseLog)).To(Succeed())
			Expect(responseLog).To(HaveKeyWithValue("msg", "outgoing response"))
			Expect(responseLog).To(HaveKeyWithValue("gateway_name", "test-gateway"))
		})
	})

	Describe("stringifyRequestParamValue", func() {
		It("should keep large integer values in decimal format", func() {
			Expect(stringifyRequestParamValue(float64(2005000002))).To(Equal("2005000002"))
			Expect(stringifyRequestParamValue(json.Number("2005000002"))).To(Equal("2005000002"))
		})

		It("should keep decimal values without scientific notation", func() {
			Expect(stringifyRequestParamValue(1.25)).To(Equal("1.25"))
			Expect(stringifyRequestParamValue(float32(1.25))).To(Equal("1.25"))
		})

		It("should preserve non-numeric values", func() {
			Expect(stringifyRequestParamValue("abc123")).To(Equal("abc123"))
			Expect(stringifyRequestParamValue(true)).To(Equal("true"))
		})
	})

	Describe("setHandlerRequestParams", func() {
		It("should set array query values as repeated query params", func() {
			req := newRecordingClientRequest()
			handlerRequest := &HandlerRequest{
				QueryParam: QueryParam{
					"related": {"fields", "storages"},
				},
			}

			err := setHandlerRequestParams(req, handlerRequest, map[string]string{}, zap.NewNop())
			Expect(err).NotTo(HaveOccurred())
			Expect(req.GetQueryParams()["related"]).To(Equal([]string{"fields", "storages"}))
			Expect(req.GetQueryParams().Encode()).To(Equal("related=fields&related=storages"))
			Expect(req.GetQueryParams().Encode()).NotTo(ContainSubstring("%5Bfields+storages%5D"))
		})

		It("should keep scalar query values unchanged", func() {
			req := newRecordingClientRequest()
			handlerRequest := &HandlerRequest{
				QueryParam: QueryParam{
					"extra": {"true"},
					"ratio": {"1.25"},
				},
			}

			err := setHandlerRequestParams(req, handlerRequest, map[string]string{}, zap.NewNop())
			Expect(err).NotTo(HaveOccurred())
			Expect(req.GetQueryParams()["extra"]).To(Equal([]string{"true"}))
			Expect(req.GetQueryParams()["ratio"]).To(Equal([]string{"1.25"}))
		})

		It("should keep header and path params scalar", func() {
			req := newRecordingClientRequest()
			headerInfo := map[string]string{}
			handlerRequest := &HandlerRequest{
				HeaderParam: StringParamMap{"X-Trace-ID": "2005000002"},
				PathParam:   StringParamMap{"bk_biz_id": "2005000002"},
			}

			err := setHandlerRequestParams(req, handlerRequest, headerInfo, zap.NewNop())
			Expect(err).NotTo(HaveOccurred())
			Expect(req.GetHeaderParams().Values("X-Trace-ID")).To(Equal([]string{"2005000002"}))
			Expect(req.pathParams["bk_biz_id"]).To(Equal("2005000002"))
			Expect(headerInfo["X-Trace-ID"]).To(Equal("2005000002"))
		})
	})

	Describe("decodeHandlerRequest with UseNumber", func() {
		It("should preserve numbers for all request parameter groups", func() {
			arguments := map[string]any{
				"header_param": map[string]any{"X-Trace-ID": 2005000002},
				"query_param": map[string]any{
					"bk_biz_id": 2005000002,
					"ratio":     1.25,
					"ids":       []any{2005000002, json.Number("9007199254740992")},
				},
				"path_param": map[string]any{"bk_biz_id": 2005000002},
				"body_param": map[string]any{
					"bk_biz_id": 2005000002,
					"nested":    map[string]any{"id": 2005000003},
				},
			}

			argsBytes, err := json.Marshal(arguments)
			Expect(err).NotTo(HaveOccurred())

			var handlerRequest HandlerRequest
			decoder := json.NewDecoder(bytes.NewReader(argsBytes))
			decoder.UseNumber()
			err = decoder.Decode(&handlerRequest)
			Expect(err).NotTo(HaveOccurred())

			Expect(handlerRequest.HeaderParam["X-Trace-ID"]).To(Equal("2005000002"))
			Expect(handlerRequest.QueryParam["bk_biz_id"]).To(Equal([]string{"2005000002"}))
			Expect(handlerRequest.QueryParam["ratio"]).To(Equal([]string{"1.25"}))
			Expect(handlerRequest.QueryParam["ids"]).To(Equal([]string{"2005000002", "9007199254740992"}))
			Expect(handlerRequest.PathParam["bk_biz_id"]).To(Equal("2005000002"))

			// BodyParam is now json.RawMessage, preserving original JSON bytes
			Expect(string(handlerRequest.BodyParam)).To(ContainSubstring("2005000002"))
			Expect(string(handlerRequest.BodyParam)).To(ContainSubstring("2005000003"))
		})

		It("should preserve large integers in body param without precision loss", func() {
			// This is the exact scenario that causes precision loss with float64:
			// 7643696123382648115 exceeds float64 precision (2^53)
			arguments := json.RawMessage(`{
				"body_param": {"video_kol_item_list": [7643696123382648115], "unique_id": 1750035600002}
			}`)

			var handlerRequest HandlerRequest
			decoder := json.NewDecoder(bytes.NewReader(arguments))
			decoder.UseNumber()
			err := decoder.Decode(&handlerRequest)
			Expect(err).NotTo(HaveOccurred())

			// json.RawMessage preserves the exact original bytes
			Expect(string(handlerRequest.BodyParam)).To(ContainSubstring("7643696123382648115"))
			Expect(string(handlerRequest.BodyParam)).To(ContainSubstring("1750035600002"))
		})
	})
})

type recordingClientRequest struct {
	headers    http.Header
	query      url.Values
	pathParams map[string]string
	bodyParam  any
	timeout    time.Duration
}

func newRecordingClientRequest() *recordingClientRequest {
	return &recordingClientRequest{
		headers:    http.Header{},
		query:      url.Values{},
		pathParams: map[string]string{},
	}
}

var _ runtime.ClientRequest = (*recordingClientRequest)(nil)

func (r *recordingClientRequest) SetHeaderParam(name string, values ...string) error {
	r.headers.Del(name)
	for _, value := range values {
		r.headers.Add(name, value)
	}
	return nil
}

func (r *recordingClientRequest) GetHeaderParams() http.Header {
	return r.headers.Clone()
}

func (r *recordingClientRequest) SetQueryParam(name string, values ...string) error {
	r.query[name] = values
	return nil
}

func (r *recordingClientRequest) SetFormParam(string, ...string) error {
	return nil
}

func (r *recordingClientRequest) SetPathParam(name, value string) error {
	r.pathParams[name] = value
	return nil
}

func (r *recordingClientRequest) GetQueryParams() url.Values {
	return r.query
}

func (r *recordingClientRequest) SetFileParam(string, ...runtime.NamedReadCloser) error {
	return nil
}

func (r *recordingClientRequest) SetBodyParam(body any) error {
	r.bodyParam = body
	return nil
}

func (r *recordingClientRequest) SetTimeout(timeout time.Duration) error {
	r.timeout = timeout
	return nil
}

func (r *recordingClientRequest) GetMethod() string {
	return ""
}

func (r *recordingClientRequest) GetPath() string {
	return ""
}

func (r *recordingClientRequest) GetBody() []byte {
	return nil
}

func (r *recordingClientRequest) GetBodyParam() any {
	return r.bodyParam
}

func (r *recordingClientRequest) GetFileParam() map[string][]runtime.NamedReadCloser {
	return nil
}
