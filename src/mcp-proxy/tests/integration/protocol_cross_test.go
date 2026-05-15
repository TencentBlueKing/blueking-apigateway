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

var _ = Describe("Protocol Cross-Validation", func() {
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

	Describe("SSE Server via Streamable HTTP Endpoint", func() {
		It("should fail when accessing SSE-only server via /mcp endpoint", func() {
			// test-sse-server 的 protocol_type 是 sse，通过 /mcp 端点访问应失败
			mcpURL := fmt.Sprintf("%s/%s/mcp", client.BaseURL, "test-sse-server")

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

			// 连接应该失败，因为 SSE server 不支持 Streamable HTTP 协议
			_, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})
	})

	Describe("Streamable HTTP Server via SSE Endpoint", func() {
		It("should fail when accessing Streamable HTTP server via /sse endpoint", func() {
			// test-http-server 的 protocol_type 是 streamable_http，通过 /sse 端点访问应失败
			sseURL := fmt.Sprintf("%s/%s/sse", client.BaseURL, "test-http-server")

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

			// 连接应该失败，因为 HTTP server 不支持 SSE 协议
			_, err := mcpClient.Connect(ctx, transport, nil)
			Expect(err).To(HaveOccurred())
		})
	})
})
