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

var _ = Describe("Application Mode Routes", func() {
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

		jwtToken, err = client.GenerateJWT("test-app", "test-user")
		Expect(err).NotTo(HaveOccurred())

		ctx, cancel = context.WithTimeout(context.Background(), 30*time.Second)
	})

	AfterEach(func() {
		cancel()
	})

	Describe("SSE Application Mode", func() {
		It("should establish SSE connection via application route and initialize", func() {
			sseURL := fmt.Sprintf("%s/%s/application/sse", client.BaseURL, "test-sse-server")

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

			err = session.Ping(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
		})

		It("should list tools via SSE application route", func() {
			session, err := connectSSEApplication(ctx, client.BaseURL, "test-sse-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListTools(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Tools).To(HaveLen(2))

			toolNames := make([]string, len(result.Tools))
			for i, tool := range result.Tools {
				toolNames[i] = tool.Name
			}
			Expect(toolNames).To(ContainElement("echo"))
			Expect(toolNames).To(ContainElement("ping"))
		})

		It("should call tool via SSE application route", func() {
			session, err := connectSSEApplication(ctx, client.BaseURL, "test-sse-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello SSE Application Mode",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should list prompts via SSE application route", func() {
			session, err := connectSSEApplication(ctx, client.BaseURL, "test-sse-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListPrompts(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Prompts).To(HaveLen(1))
		})

		It("should reject SSE application route without JWT", func() {
			sseURL := fmt.Sprintf("%s/%s/application/sse", client.BaseURL, "test-sse-server")

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

		It("should reject SSE application route with expired permission", func() {
			expiredToken, err := client.GenerateJWT("expired-app", "expired-user")
			Expect(err).NotTo(HaveOccurred())

			sseURL := fmt.Sprintf("%s/%s/application/sse", client.BaseURL, "test-sse-server")

			httpClient := &http.Client{
				Timeout: 10 * time.Second,
				Transport: &jwtRoundTripper{
					token: expiredToken,
					base:  http.DefaultTransport,
				},
			}

			req, err := http.NewRequestWithContext(ctx, http.MethodGet, sseURL, nil)
			Expect(err).NotTo(HaveOccurred())
			req.Header.Set("Accept", "text/event-stream")
			req.Header.Set(constant.BkGatewayJWTHeaderKey, expiredToken)

			resp, err := httpClient.Do(req)
			Expect(err).NotTo(HaveOccurred())
			defer resp.Body.Close()

			Expect(resp.StatusCode).To(Equal(http.StatusForbidden))
		})
	})

	Describe("Streamable HTTP Application Mode", func() {
		It("should initialize via Streamable HTTP application route", func() {
			session, err := connectStreamableHTTPApplication(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			err = session.Ping(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
		})

		It("should list tools via Streamable HTTP application route", func() {
			session, err := connectStreamableHTTPApplication(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListTools(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Tools).To(HaveLen(2))

			toolNames := make([]string, len(result.Tools))
			for i, tool := range result.Tools {
				toolNames[i] = tool.Name
			}
			Expect(toolNames).To(ContainElement("echo"))
			Expect(toolNames).To(ContainElement("ping"))
		})

		It("should call tool via Streamable HTTP application route", func() {
			session, err := connectStreamableHTTPApplication(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "Hello HTTP Application Mode",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Content).NotTo(BeEmpty())
		})

		It("should list prompts via Streamable HTTP application route", func() {
			session, err := connectStreamableHTTPApplication(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.ListPrompts(ctx, nil)
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())
			Expect(result.Prompts).To(HaveLen(1))
		})

		It("should reject Streamable HTTP application route without JWT", func() {
			mcpURL := fmt.Sprintf("%s/%s/application/mcp", client.BaseURL, "test-http-server")

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

			_, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})

		It("should reject Streamable HTTP application route with expired permission", func() {
			expiredToken, err := client.GenerateJWT("expired-app", "expired-user")
			Expect(err).NotTo(HaveOccurred())

			mcpURL := fmt.Sprintf("%s/%s/application/mcp", client.BaseURL, "test-http-server")

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

			_, err = mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})
	})
})
