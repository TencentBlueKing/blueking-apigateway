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
	"strconv"
	"sync"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/util"
)

var benchmarkToolResult *mcp.CallToolResult

func BenchmarkGenToolHandlerLargeJSONResponse(b *testing.B) {
	initBenchmarkRuntime(b)

	for _, size := range []int{64 << 10, 1 << 20} {
		size := size
		b.Run(strconv.Itoa(size)+"B", func(b *testing.B) {
			responseBody := buildBenchmarkJSONBody(size)
			upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set(constant.BkGatewayRequestIDKey, "bench-upstream-request-id")
				_, _ = w.Write(responseBody)
			}))
			defer upstream.Close()

			upstreamURL, err := url.Parse(upstream.URL)
			if err != nil {
				b.Fatalf("parse upstream URL: %v", err)
			}

			for _, rawResponseEnabled := range []bool{false, true} {
				rawResponseEnabled := rawResponseEnabled
				mode := "envelope"
				if rawResponseEnabled {
					mode = "raw-response"
				}

				b.Run(mode, func(b *testing.B) {
					toolConfig := &ToolConfig{
						Name:   "large_json",
						Method: http.MethodGet,
						Host:   upstreamURL.Host,
						Schema: upstreamURL.Scheme,
						Url:    "/",
					}
					handler := genToolHandler(toolConfig, "bench-server", func() bool {
						return rawResponseEnabled
					})
					req := &mcp.CallToolRequest{
						Params: &mcp.CallToolParamsRaw{
							Name:      toolConfig.Name,
							Arguments: json.RawMessage(`{}`),
						},
						Extra: &mcp.RequestExtra{
							Header: http.Header{
								constant.RequestIDHeaderKey: []string{
									"bench-x-request-id",
								},
								constant.BkGatewayRequestIDKey: []string{
									"bench-request-id",
								},
								constant.BkGatewayJWTHeaderKey: []string{
									"bench-jwt",
								},
								constant.BkApiMCPServerIDKey: []string{"100"},
								constant.BkApiMCPServerNameKey: []string{
									"bench-server",
								},
								constant.BkApiAllowedHeadersKey: []string{""},
								constant.BkApiAuthorizationHeaderKey: []string{
									"bench-authorization",
								},
							},
						},
					}
					ctx := benchmarkToolCallContext(b)

					b.ReportAllocs()
					b.SetBytes(int64(len(responseBody)))
					b.ResetTimer()
					for i := 0; i < b.N; i++ {
						result, err := handler(ctx, req)
						if err != nil {
							b.Fatalf("tool handler returned error: %v", err)
						}
						if result == nil || len(result.Content) == 0 {
							b.Fatal("tool handler returned empty result")
						}
						benchmarkToolResult = result
					}
				})
			}
		})
	}
}

// BenchmarkEnvelopePreview measures the cost of rendering the envelope preview used by
// audit/API logs. It exercises three regimes: a small JSON body that fits the limit (raw
// embed), a large JSON body that requires truncation (string-encoded), and a non-JSON HTML
// body (always string-encoded). Preview cost should be O(min(len(body), limit)) and remain
// well below the cost of the upstream call itself.
func BenchmarkEnvelopePreview(b *testing.B) {
	cases := []struct {
		name        string
		contentType string
		body        []byte
		limit       int
	}{
		{
			name:        "json-fits-1KB",
			contentType: "application/json",
			body:        buildBenchmarkJSONBody(1 << 10),
			limit:       4096,
		},
		{
			name:        "json-truncated-1MB",
			contentType: "application/json",
			body:        buildBenchmarkJSONBody(1 << 20),
			limit:       16384,
		},
		{
			name:        "html-truncated-1MB",
			contentType: "text/html",
			body:        bytes.Repeat([]byte("<p>error</p>"), (1<<20)/12),
			limit:       16384,
		},
	}

	for _, tc := range cases {
		tc := tc
		b.Run(tc.name, func(b *testing.B) {
			payload := newToolResponsePayload(500, "bench-upstream", tc.contentType, tc.body)

			var sink string
			b.ReportAllocs()
			b.SetBytes(int64(len(tc.body)))
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				sink = payload.EnvelopePreview("bench-trace", "bench-x-request", tc.limit)
			}
			benchmarkEnvelopePreviewSink = sink
		})
	}
}

var benchmarkEnvelopePreviewSink string

func initBenchmarkRuntime(b *testing.B) {
	b.Helper()

	disabledLog := config.LogConfig{
		Level:    "fatal",
		Writer:   "os",
		Settings: map[string]string{"name": "stdout"},
	}
	config.G = &config.Config{
		Logger: config.Logger{
			Default:  disabledLog,
			API:      disabledLog,
			Audit:    disabledLog,
			Database: disabledLog,
		},
		McpServer: config.McpServer{
			InnerJwtExpireTime: 5 * time.Minute,
		},
	}
	logging.InitLogger(config.G)
	sharedTransportOnce = sync.Once{}
	sharedTransport = nil
	InitSharedTransport(config.Transport{
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   100,
		IdleConnTimeoutSecond: 90,
	})
}

func benchmarkToolCallContext(b *testing.B) context.Context {
	b.Helper()

	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		b.Fatalf("generate private key: %v", err)
	}
	privateKeyPEM := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(privateKey),
	})

	ctx := context.Background()
	ctx = context.WithValue(ctx, constant.BkGatewayJWTClaims, &util.JWTClaimsForLazySigning{
		AppCode:      "bench-app",
		AppVerified:  true,
		Username:     "bench-user",
		UserVerified: true,
		Issuer:       "bench-issuer",
		Audience:     []string{"bench-audience"},
	})
	ctx = context.WithValue(ctx, constant.BkGatewayPrivateKey, privateKeyPEM)
	ctx = context.WithValue(ctx, constant.MCPServerID, 100)
	ctx = context.WithValue(ctx, constant.MCPServerName, "bench-server")
	ctx = context.WithValue(ctx, constant.GatewayID, 200)
	ctx = context.WithValue(ctx, constant.GatewayName, "bench-gateway")
	ctx = context.WithValue(ctx, constant.BkAppCode, "bench-app")
	ctx = context.WithValue(ctx, constant.BkUsername, "bench-user")
	ctx = context.WithValue(ctx, constant.RequestID, "bench-request-id")
	ctx = context.WithValue(ctx, constant.XRequestID, "bench-x-request-id")
	ctx = context.WithValue(ctx, constant.ClientIP, "127.0.0.1")
	ctx = context.WithValue(ctx, constant.ClientID, "bench-client")
	return ctx
}

func buildBenchmarkJSONBody(targetSize int) []byte {
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
