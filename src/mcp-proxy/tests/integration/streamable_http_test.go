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

package integration_test

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("Streamable HTTP Protocol", func() {
	var (
		client   *TestClient
		jwtToken string
		ctx      context.Context
		cancel   context.CancelFunc
	)

	BeforeEach(func() {
		var err error
		client, err = NewTestClient()
		Expect(err).NotTo(HaveOccurred())

		// 生成 JWT token
		jwtToken, err = client.GenerateJWT("test-app", "test-user")
		Expect(err).NotTo(HaveOccurred())

		ctx, cancel = context.WithTimeout(context.Background(), 30*time.Second)
	})

	AfterEach(func() {
		cancel()
	})

	Describe("Initialize", func() {
		It("should initialize successfully using MCP SDK", func() {
			// 使用官方 MCP SDK 的 StreamableClientTransport
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			// 创建带 JWT 认证的 HTTP 客户端
			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			// 创建 MCP 客户端
			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			// 连接到服务器（Connect 会自动发送 initialize 请求）
			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(session).NotTo(BeNil())
			defer session.Close()

			// 验证连接成
			// 功
			err = session.Ping(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
		})
	})

	Describe("Tools List", func() {
		It("should list all tools using MCP SDK", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 列出工具
			result, err := session.ListTools(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Tools).NotTo(BeNil())
		})
	})

	Describe("Tools Call", func() {
		It("should call tool successfully using MCP SDK", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 调用工具
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello, World!",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should return error for non-existent tool", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 调用不存在的工具
			_, err = session.CallTool(ctx, &mcp.CallToolParams{
				Name:      "non_existent_tool_xyz_123",
				Arguments: map[string]any{},
			})
			// 不存在的工具应该返回错误
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("Prompts", func() {
		It("should list prompts using MCP SDK", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 列出 prompts
			result, err := session.ListPrompts(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
		})

		It("should get prompt using MCP SDK", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 先获取 prompts 列表
			listResult, err := session.ListPrompts(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			if len(listResult.Prompts) > 0 {
				// 获取第一个 prompt
				result, err := session.GetPrompt(ctx, &mcp.GetPromptParams{
					Name: listResult.Prompts[0].Name,
				})
				Expect(err).NotTo(HaveOccurred())
				Expect(result).NotTo(BeNil())
			}
		})
	})

	Describe("Authentication", func() {
		It("should reject request without JWT token", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			// 不带 JWT 的 HTTP 客户端
			httpClient := &http.Client{
				Timeout: 10 * time.Second,
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			// 连接应该失败
			_, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})

		It("should reject request with invalid JWT token", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			// 带无效 JWT 的 HTTP 客户端
			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: "invalid-token",
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			// 连接应该失败
			_, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("X-Request-ID Propagation", func() {
		It("should propagate X-Request-ID through the full chain", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			xRequestID := "global-chain-id-integration-test-12345"
			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
					extraHeaders: map[string]string{
						"X-Request-Id": xRequestID,
					},
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 验证连接成功
			err = session.Ping(ctx, nil)
			Expect(err).NotTo(HaveOccurred())

			// 调用工具，验证带 X-Request-ID 的请求正常工作
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello with X-Request-ID",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should work without X-Request-ID header", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 不带 X-Request-ID 也应该正常工作
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello without X-Request-ID",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should propagate both X-Request-ID and X-Bkapi-Request-ID independently", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			xRequestID := "full-chain-id-abc-789"
			bkapiRequestID := "segment-id-xyz-456"
			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
					extraHeaders: map[string]string{
						"X-Request-Id":       xRequestID,
						"X-Bkapi-Request-ID": bkapiRequestID,
					},
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 两个 ID 同时存在时应正常工作
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello with both IDs",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("MCP Server Not Found", func() {
		It("should return error for non-existent MCP server", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "non-existent-server-xyz")

			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			// 连接应该失败
			_, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("Trace Context Propagation", func() {
		It("should propagate incoming traceparent through to tool call without error", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			// Include a W3C traceparent header to simulate an instrumented caller
			incomingTraceID := "abcdef1234567890abcdef1234567890"
			incomingSpanID := "1234567890abcdef"
			traceparent := fmt.Sprintf("00-%s-%s-01", incomingTraceID, incomingSpanID)

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
					extraHeaders: map[string]string{
						"Traceparent": traceparent,
					},
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// Verify tool call works with traceparent present
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello with trace context",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should work normally without traceparent header", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// Without traceparent, tool call should still succeed
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello without trace context",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should propagate both traceparent and X-Request-ID simultaneously", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			incomingTraceID := "11223344556677889900aabbccddeeff"
			incomingSpanID := "aabbccddeeff0011"
			traceparent := fmt.Sprintf("00-%s-%s-01", incomingTraceID, incomingSpanID)
			xRequestID := "trace-and-request-id-combined-test"

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
					extraHeaders: map[string]string{
						"Traceparent":  traceparent,
						"X-Request-Id": xRequestID,
					},
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// Both headers should coexist without issues
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello with both trace and request ID",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("Client Info Propagation", func() {
		It("should preserve clientInfo through initialize and subsequent tool calls", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			// Connect with a specific client name to verify clientInfo propagation
			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "integration-test-client",
				Version: "3.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// Verify the session works — clientInfo should have been sent during initialize
			err = session.Ping(ctx, nil)
			Expect(err).NotTo(HaveOccurred())

			// List tools to verify normal operations work with clientInfo set
			listResult, err := session.ListTools(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(listResult).NotTo(BeNil())

			// Call a tool — the LoggingMiddleware should log client_id as "integration-test-client"
			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello from integration-test-client",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should work with different client names", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			// Use a different client name (simulating cursor, claude-code, etc.)
			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "cursor",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello from cursor",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("Permission", func() {
		It("should reject connection with expired permission", func() {
			// 使用 expired-app 的 JWT，其权限已过期
			expiredToken, err := client.GenerateJWT("expired-app", "expired-user")
			Expect(err).NotTo(HaveOccurred())

			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: expiredToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			// 连接应该失败
			_, err = mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})

		It("should reject connection with unauthorized app", func() {
			// 使用完全没有权限记录的 app_code
			unauthorizedToken, err := client.GenerateJWT("unauthorized-app", "some-user")
			Expect(err).NotTo(HaveOccurred())

			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: unauthorizedToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			// 连接应该失败
			_, err = mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("Tool Name Mapping", func() {
		It("should list tools with renamed tool names via Streamable HTTP", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-renamed-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListTools(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Tools).NotTo(BeNil())

			// echo 映射为 echo_message, ping 保持原名
			toolNames := make([]string, len(result.Tools))
			for i, tool := range result.Tools {
				toolNames[i] = tool.Name
			}
			Expect(toolNames).To(ContainElement("echo_message"))
			Expect(toolNames).To(ContainElement("ping"))
			Expect(toolNames).NotTo(ContainElement("echo"))
		})

		It("should call renamed tool via Streamable HTTP", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-renamed-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo_message",
				Arguments: map[string]any{
					"body_param": map[string]any{
						"message": "Hello from renamed HTTP tool",
					},
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("GET Tool Call", func() {
		It("should call GET type tool (ping) via Streamable HTTP", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name:      "ping",
				Arguments: map[string]any{},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("Tools List Validation", func() {
		It("should list exactly the expected tools with correct names", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListTools(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			// test-http-server 有 echo 和 ping 两个工具
			Expect(result.Tools).To(HaveLen(2))

			toolNames := make([]string, len(result.Tools))
			for i, tool := range result.Tools {
				toolNames[i] = tool.Name
			}
			Expect(toolNames).To(ContainElement("echo"))
			Expect(toolNames).To(ContainElement("ping"))
		})
	})

	Describe("Prompts Validation", func() {
		It("should list prompts with correct names", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListPrompts(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Prompts).To(HaveLen(1))
			// Prompt 注册时使用 code 字段作为 MCP prompt name
			Expect(result.Prompts[0].Name).To(Equal("http-test-prompt"))
		})

		It("should get prompt with correct content", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 使用 code 字段作为 prompt name
			result, err := session.GetPrompt(ctx, &mcp.GetPromptParams{
				Name: "http-test-prompt",
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Messages).To(HaveLen(1))
			textContent, ok := result.Messages[0].Content.(*mcp.TextContent)
			Expect(ok).To(BeTrue())
			Expect(textContent.Text).To(Equal("This is a test prompt for HTTP MCP server."))
		})

		It("should return error for non-existent prompt", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			_, err = session.GetPrompt(ctx, &mcp.GetPromptParams{
				Name: "non-existent-prompt-xyz",
			})
			Expect(err).To(HaveOccurred())
		})

		It("should return empty prompts list for MCP server without prompts", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-no-prompts-http")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListPrompts(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Prompts).To(BeEmpty())
		})
	})

	Describe("Multiple Calls in Same Session", func() {
		It("should handle multiple consecutive tool calls in the same session", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-http-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			// 连续调用 3 次
			for i := 0; i < 3; i++ {
				result, err := session.CallTool(ctx, &mcp.CallToolParams{
					Name: "echo",
					Arguments: map[string]any{
						"message": fmt.Sprintf("HTTP call #%d", i+1),
					},
				})
				Expect(err).NotTo(HaveOccurred())
				Expect(result).NotTo(BeNil())
				Expect(result.Content).NotTo(BeEmpty())
			}
		})
	})

	Describe("Large Integer Path/Query Params", func() {
		It("should preserve large integer path and query params without scientific notation", func() {
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-path-param-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.StreamableClientTransport{
				Endpoint:   mcpURL,
				HTTPClient: httpClient,
			}

			mcpClient := mcp.NewClient(&mcp.Implementation{
				Name:    "test-client",
				Version: "1.0.0",
			}, nil)

			session, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "list_biz_hosts",
				Arguments: map[string]any{
					"path_param":  map[string]any{"bk_biz_id": 2005000002},
					"query_param": map[string]any{"limit": 20},
					"body_param":  map[string]any{"fields": []string{"bk_host_id", "bk_host_innerip"}},
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())

			envelope, err := extractToolResponseEnvelope(result)
			Expect(err).NotTo(HaveOccurred())

			responseBody, ok := envelope["response_body"].(map[string]any)
			Expect(ok).To(BeTrue())

			// go-httpbin's /anything endpoint echoes back the URL
			requestURL, ok := responseBody["url"].(string)
			Expect(ok).To(BeTrue())
			Expect(requestURL).To(ContainSubstring("/2005000002/"))
			Expect(requestURL).NotTo(ContainSubstring("e+"))
			Expect(requestURL).To(ContainSubstring("limit=20"))
		})
	})
})
