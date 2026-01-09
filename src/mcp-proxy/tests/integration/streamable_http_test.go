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
})
