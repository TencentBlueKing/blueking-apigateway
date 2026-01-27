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

	"mcp_proxy/pkg/constant"
)

var _ = Describe("SSE Protocol", func() {
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

	Describe("SSE Connection", func() {
		It("should establish SSE connection and initialize successfully using MCP SDK", func() {
			// 使用官方 MCP SDK 的 SSEClientTransport
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			// 创建带 JWT 认证的 HTTP 客户端
			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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

			// 验证连接成功
			err = session.Ping(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
		})

		It("should reject SSE connection without JWT", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			// 不带 JWT 的 HTTP 客户端
			httpClient := &http.Client{
				Timeout: 10 * time.Second,
			}

			req, err := http.NewRequestWithContext(ctx, http.MethodGet, sseURL, nil)
			Expect(err).NotTo(HaveOccurred())
			req.Header.Set("Accept", "text/event-stream")

			resp, err := httpClient.Do(req)
			Expect(err).NotTo(HaveOccurred())
			defer resp.Body.Close()

			Expect(resp.StatusCode).To(Equal(http.StatusUnauthorized))
		})
	})

	Describe("SSE Tools List", func() {
		It("should list tools via SSE protocol using MCP SDK", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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

	Describe("SSE Tools Call", func() {
		It("should call tool via SSE protocol using MCP SDK", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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
					"message": "Hello SSE",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})
	})

	Describe("SSE Prompts", func() {
		It("should list prompts via SSE protocol using MCP SDK", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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

		It("should get prompt via SSE protocol using MCP SDK", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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

	Describe("SSE Authentication", func() {
		It("should reject SSE connection with invalid JWT", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			// 带无效 JWT 的 HTTP 客户端
			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: "invalid-token",
					base:  http.DefaultTransport,
				},
			}

			req, err := http.NewRequestWithContext(ctx, http.MethodGet, sseURL, nil)
			Expect(err).NotTo(HaveOccurred())
			req.Header.Set("Accept", "text/event-stream")
			req.Header.Set(constant.BkGatewayJWTHeaderKey, "invalid-token")

			resp, err := httpClient.Do(req)
			Expect(err).NotTo(HaveOccurred())
			defer resp.Body.Close()

			Expect(resp.StatusCode).To(Equal(http.StatusUnauthorized))
		})
	})

	Describe("SSE Tools Error Handling", func() {
		It("should return error for non-existent tool via SSE", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-sse-server")

			httpClient := &http.Client{
				Timeout: 30 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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

	Describe("SSE MCP Server Not Found", func() {
		It("should reject connection for non-existent MCP server via SSE", func() {
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "non-existent-server-xyz")

			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: jwtToken,
					base:  http.DefaultTransport,
				},
			}

			transport := &mcp.SSEClientTransport{
				Endpoint:   sseURL,
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
})

// jwtRoundTripper 是一个自定义的 http.RoundTripper，用于在每个请求中添加 JWT 认证头
type jwtRoundTripper struct {
	token string
	base  http.RoundTripper
}

func (j *jwtRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	// 克隆请求以避免修改原始请求
	reqClone := req.Clone(req.Context())
	reqClone.Header.Set(constant.BkGatewayJWTHeaderKey, j.token)
	return j.base.RoundTrip(reqClone)
}
