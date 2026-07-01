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
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"net/http"
	"net/http/httptest"
	"net/url"
	"sync"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/util"
)

var _ = Describe("genToolHandler refactor compatibility", func() {
	It("returns the same envelope shape for a large JSON response", func() {
		responseBody := buildCompatJSONBody(64 << 10)
		upstream := newCompatUpstream(http.StatusOK, "application/json", "compat-upstream-req", responseBody)
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, false)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeFalse())
		text := compatToolResultText(result)
		var envelope struct {
			StatusCode   int             `json:"status_code"`
			RequestID    string          `json:"request_id"`
			XRequestID   string          `json:"x_request_id"`
			ResponseBody json.RawMessage `json:"response_body"`
		}
		Expect(json.Unmarshal([]byte(text), &envelope)).To(Succeed())
		Expect(envelope.StatusCode).To(Equal(http.StatusOK))
		Expect(envelope.RequestID).To(Equal("compat-upstream-req"))
		Expect(envelope.XRequestID).To(Equal("compat-x-request-id"))
		Expect(string(envelope.ResponseBody)).To(MatchJSON(string(responseBody)))
	})

	It("returns the upstream JSON body without an envelope when raw response is enabled", func() {
		responseBody := buildCompatJSONBody(64 << 10)
		upstream := newCompatUpstream(http.StatusOK, "application/json", "compat-upstream-req", responseBody)
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, true)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeFalse())
		Expect(compatToolResultText(result)).To(MatchJSON(string(responseBody)))
	})

	It("returns a tool error for invalid non-empty bodies declared as JSON in envelope mode", func() {
		upstream := newCompatUpstream(
			http.StatusOK,
			"application/json",
			"compat-upstream-req",
			[]byte(`{"bad"`),
		)
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, false)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeTrue())
		Expect(compatToolResultText(result)).NotTo(BeEmpty())
	})

	It("returns a tool error for invalid non-empty bodies declared as JSON in raw response mode", func() {
		upstream := newCompatUpstream(
			http.StatusOK,
			"application/json",
			"compat-upstream-req",
			[]byte(`{"bad"`),
		)
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, true)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeTrue())
		Expect(compatToolResultText(result)).NotTo(BeEmpty())
	})

	It("preserves an empty text response body as an empty string in the envelope", func() {
		upstream := newCompatUpstream(http.StatusOK, "text/plain", "compat-upstream-req", []byte{})
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, false)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeFalse())
		text := compatToolResultText(result)
		Expect(text).To(MatchJSON(`{
			"status_code": 200,
			"request_id": "compat-upstream-req",
			"trace_id": "",
			"x_request_id": "compat-x-request-id",
			"response_body": ""
		}`))
	})

	It("preserves an empty text response body as an empty string when raw response is enabled", func() {
		upstream := newCompatUpstream(http.StatusOK, "text/plain", "compat-upstream-req", []byte{})
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, true)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeFalse())
		Expect(compatToolResultText(result)).To(Equal(`""`))
	})

	It("returns IsError and preserves upstream JSON detail for non-2xx responses", func() {
		upstream := newCompatUpstream(
			http.StatusInternalServerError,
			"application/json",
			"compat-upstream-req",
			[]byte(`{"error":{"code":500,"message":"upstream boom"}}`),
		)
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, false)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeTrue())
		Expect(compatToolResultText(result)).To(ContainSubstring("upstream boom"))
	})

	It("returns IsError and preserves upstream text diagnostics for non-2xx responses", func() {
		upstream := newCompatUpstream(
			http.StatusInternalServerError,
			"text/html",
			"compat-upstream-req",
			[]byte(`<html><body>upstream boom</body></html>`),
		)
		defer upstream.Close()

		result := callCompatToolHandler(upstream.URL, false)

		Expect(result).NotTo(BeNil())
		Expect(result.IsError).To(BeTrue())
		Expect(compatToolResultText(result)).To(ContainSubstring("upstream boom"))
	})
})

func newCompatUpstream(statusCode int, contentType, requestID string, body []byte) *httptest.Server {
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		if contentType != "" {
			w.Header().Set("Content-Type", contentType)
		}
		if requestID != "" {
			w.Header().Set(constant.BkGatewayRequestIDKey, requestID)
		}
		w.WriteHeader(statusCode)
		_, _ = w.Write(body)
	}))
}

func callCompatToolHandler(upstream string, rawResponseEnabled bool) *mcp.CallToolResult {
	upstreamURL, err := url.Parse(upstream)
	Expect(err).NotTo(HaveOccurred())

	sharedTransportOnce = sync.Once{}
	sharedTransport = nil
	InitSharedTransport(config.Transport{
		MaxIdleConns:          10,
		MaxIdleConnsPerHost:   10,
		IdleConnTimeoutSecond: 30,
	})

	toolConfig := &ToolConfig{
		Name:   "compat_tool",
		Method: http.MethodGet,
		Host:   upstreamURL.Host,
		Schema: upstreamURL.Scheme,
		Url:    "/",
	}
	handler := genToolHandler(toolConfig, "compat-server", func() bool {
		return rawResponseEnabled
	})
	result, err := handler(compatToolCallContext(), &mcp.CallToolRequest{
		Params: &mcp.CallToolParamsRaw{
			Name:      toolConfig.Name,
			Arguments: json.RawMessage(`{}`),
		},
	})
	Expect(err).NotTo(HaveOccurred())
	return result
}

func compatToolCallContext() context.Context {
	config.G = &config.Config{
		McpServer: config.McpServer{
			InnerJwtExpireTime: 5 * time.Minute,
		},
	}

	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	Expect(err).NotTo(HaveOccurred())
	privateKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(privateKey),
	})

	ctx := context.Background()
	ctx = context.WithValue(ctx, constant.BkGatewayJWTClaims, &util.JWTClaimsForLazySigning{
		AppCode:      "compat-app",
		AppVerified:  true,
		Username:     "compat-user",
		UserVerified: true,
		Issuer:       "compat-issuer",
		Audience:     []string{"compat-audience"},
	})
	ctx = context.WithValue(ctx, constant.BkGatewayPrivateKey, privateKeyPEM)
	ctx = context.WithValue(ctx, constant.MCPServerID, 123)
	ctx = context.WithValue(ctx, constant.MCPServerName, "compat-server")
	ctx = context.WithValue(ctx, constant.GatewayID, 456)
	ctx = context.WithValue(ctx, constant.GatewayName, "compat-gateway")
	ctx = context.WithValue(ctx, constant.BkAppCode, "compat-app")
	ctx = context.WithValue(ctx, constant.BkUsername, "compat-user")
	ctx = context.WithValue(ctx, constant.RequestID, "compat-request-id")
	ctx = context.WithValue(ctx, constant.XRequestID, "compat-x-request-id")
	ctx = context.WithValue(ctx, constant.ClientIP, "127.0.0.1")
	ctx = context.WithValue(ctx, constant.ClientID, "compat-client")
	return ctx
}

func compatToolResultText(result *mcp.CallToolResult) string {
	Expect(result.Content).To(HaveLen(1))
	textContent, ok := result.Content[0].(*mcp.TextContent)
	Expect(ok).To(BeTrue())
	return textContent.Text
}

func buildCompatJSONBody(targetSize int) []byte {
	const item = `{"id":123456789,"name":"abcdefghijklmnopqrstuvwxyz","enabled":true,"value":12345}`

	var buf bytes.Buffer
	buf.Grow(targetSize + len(item))
	buf.WriteString(`{"items":[`)
	for buf.Len()+len(item)+3 < targetSize {
		if buf.Bytes()[buf.Len()-1] != '[' {
			buf.WriteByte(',')
		}
		buf.WriteString(item)
	}
	buf.WriteString(`]}`)
	return buf.Bytes()
}
