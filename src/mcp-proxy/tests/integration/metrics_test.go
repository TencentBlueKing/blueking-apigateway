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
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

// fetchMetrics retrieves the Prometheus metrics output from the /metrics endpoint
func fetchMetrics(baseURL string) (string, error) {
	url := fmt.Sprintf("%s/metrics", baseURL)
	resp, err := http.Get(url)
	if err != nil {
		return "", fmt.Errorf("failed to fetch metrics: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read metrics body: %w", err)
	}
	return string(body), nil
}

// containsMetricLine checks whether the metrics output contains a line matching the given metric name and labels.
// It uses exact label key=value matching within the label section of the Prometheus exposition line.
func containsMetricLine(metricsOutput, metricName string, labels map[string]string) bool {
	prefix := metricName + "{"
	for _, line := range strings.Split(metricsOutput, "\n") {
		if !strings.HasPrefix(line, prefix) {
			continue
		}
		// Extract the label section between "{" and "}"
		labelStart := strings.Index(line, "{")
		labelEnd := strings.Index(line, "}")
		if labelStart < 0 || labelEnd < 0 || labelEnd <= labelStart {
			continue
		}
		labelSection := line[labelStart+1 : labelEnd]

		match := true
		for k, v := range labels {
			expected := fmt.Sprintf(`%s="%s"`, k, v)
			// Check that the expected label appears as a complete key="value" pair,
			// bounded by start-of-labels, comma, or end-of-labels
			found := false
			for _, part := range strings.Split(labelSection, ",") {
				if strings.TrimSpace(part) == expected {
					found = true
					break
				}
			}
			if !found {
				match = false
				break
			}
		}
		if match {
			return true
		}
	}
	return false
}

// connectStreamableHTTP creates a streamable HTTP MCP session for the given server name.
func connectStreamableHTTP(
	ctx context.Context, baseURL, serverName, jwtToken string,
) (*mcp.ClientSession, error) {
	mcpURL := fmt.Sprintf("%s/%s/mcp", baseURL, serverName)

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

	return mcpClient.Connect(ctx, transport, nil)
}

// connectSSE creates an SSE MCP session for the given server name.
func connectSSE(
	ctx context.Context, baseURL, serverName, jwtToken string,
) (*mcp.ClientSession, error) {
	sseURL := fmt.Sprintf("%s/%s/sse", baseURL, serverName)

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

	return mcpClient.Connect(ctx, transport, nil)
}

var _ = Describe("MCP Protocol Metrics", func() {
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

	Describe("Streamable HTTP Metrics", func() {
		It("should report mcp_requests_total after initialize and tools/call", func() {
			session, err := connectStreamableHTTP(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "metrics integration test",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_requests_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"method":          "initialize",
			"app_code":        "test-app",
			"error":           "0",
		})).To(BeTrue(), "should have mcp_requests_total for initialize")

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_requests_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"method":          "tools/call",
			"app_code":        "test-app",
			"error":           "0",
		})).To(BeTrue(), "should have mcp_requests_total for tools/call")
		})

		It("should report mcp_request_duration_milliseconds after method calls", func() {
			session, err := connectStreamableHTTP(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			_, err = session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "duration test",
				},
			})
			Expect(err).NotTo(HaveOccurred())

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		Expect(
			containsMetricLine(
				metricsOutput,
				"bk_apigateway_mcp_proxy_mcp_request_duration_milliseconds_count",
				map[string]string{
					"gateway_name":    "bk-apigateway",
					"mcp_server_name": "test-http-server",
					"method":          "tools/call",
					"app_code":        "test-app",
				},
			),
		).To(BeTrue(), "should have mcp_request_duration_milliseconds for tools/call")
		})

		It("should report mcp_tool_calls_total with tool name", func() {
			session, err := connectStreamableHTTP(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			_, err = session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "tool call metric test",
				},
			})
			Expect(err).NotTo(HaveOccurred())

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_tool_calls_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"tool_name":       "echo",
			"app_code":        "test-app",
			"error":           "0",
		})).To(BeTrue(), "should have mcp_tool_calls_total for echo tool")
		})

		It("should report mcp_sessions_active after initialize", func() {
			session, err := connectStreamableHTTP(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_sessions_active", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"app_code":        "test-app",
		})).To(BeTrue(), "should have mcp_sessions_active for test-http-server")
		})

		It("should report mcp_errors_total when calling non-existent tool", func() {
			session, err := connectStreamableHTTP(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			_, err = session.CallTool(ctx, &mcp.CallToolParams{
				Name:      "non_existent_tool_for_metrics",
				Arguments: map[string]any{},
			})
			Expect(err).To(HaveOccurred())

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_errors_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"method":          "tools/call",
			"app_code":        "test-app",
			"error_code":      "invalid_params",
		})).To(BeTrue(), "should have mcp_errors_total for failed tools/call")

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_requests_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"method":          "tools/call",
			"app_code":        "test-app",
			"error":           "1",
		})).To(BeTrue(), "should have mcp_requests_total with error for failed tools/call")
		})
	})

	Describe("SSE Metrics", func() {
		It("should report mcp metrics for SSE protocol", func() {
			session, err := connectSSE(ctx, client.BaseURL, "test-sse-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			result, err := session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "SSE metrics test",
				},
			})
			Expect(err).NotTo(HaveOccurred())
			Expect(result).NotTo(BeNil())

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_requests_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-sse-server",
			"method":          "initialize",
			"app_code":        "test-app",
			"error":           "0",
		})).To(BeTrue(), "should have mcp_requests_total for SSE initialize")

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_requests_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-sse-server",
			"method":          "tools/call",
			"app_code":        "test-app",
			"error":           "0",
		})).To(BeTrue(), "should have mcp_requests_total for SSE tools/call")

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_tool_calls_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-sse-server",
			"tool_name":       "echo",
			"app_code":        "test-app",
			"error":           "0",
		})).To(BeTrue(), "should have mcp_tool_calls_total for SSE echo tool")

		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_sessions_active", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-sse-server",
			"app_code":        "test-app",
		})).To(BeTrue(), "should have mcp_sessions_active for test-sse-server")
		})
	})

	Describe("Metrics Gateway Name Label", func() {
		It("should include gateway_name label in metrics", func() {
			session, err := connectStreamableHTTP(ctx, client.BaseURL, "test-http-server", jwtToken)
			Expect(err).NotTo(HaveOccurred())
			defer session.Close()

			_, err = session.CallTool(ctx, &mcp.CallToolParams{
				Name: "echo",
				Arguments: map[string]any{
					"message": "gateway name test",
				},
			})
			Expect(err).NotTo(HaveOccurred())

			metricsOutput, err := fetchMetrics(client.BaseURL)
			Expect(err).NotTo(HaveOccurred())

		// The gateway_name should be "bk-apigateway" (from init.sql test data)
		Expect(containsMetricLine(metricsOutput, "bk_apigateway_mcp_proxy_mcp_requests_total", map[string]string{
			"gateway_name":    "bk-apigateway",
			"mcp_server_name": "test-http-server",
			"method":          "tools/call",
			"app_code":        "test-app",
		})).To(BeTrue(), "should have gateway_name=bk-apigateway in mcp_requests_total")
		})
	})
})
