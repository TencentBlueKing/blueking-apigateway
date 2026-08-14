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
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"sync"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	segmentjson "github.com/segmentio/encoding/json"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/metric"
	"mcp_proxy/pkg/util"
)

var (
	benchmarkToolResult      *mcp.CallToolResult
	benchmarkWireMessage     jsonrpc.Message
	benchmarkCallToolParams  mcp.CallToolParamsRaw
	benchmarkWireBytes       []byte
	benchmarkResponseBody    []byte
	benchmarkMetricsInitOnce sync.Once
)

func BenchmarkGenToolHandlerLargeJSONResponse(b *testing.B) {
	initBenchmarkRuntime(b)

	for _, size := range []int{64 << 10, 1 << 20, 10 << 20} {
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

// BenchmarkGenToolHandlerLargeJSONRequest measures the production tools/call handler after
// the MCP SDK has decoded the wire request. The arguments contain a large POST body so the
// benchmark includes audit/API-log observation, HandlerRequest decoding, metrics, and the
// go-openapi request-body producer.
func BenchmarkGenToolHandlerLargeJSONRequest(b *testing.B) {
	initBenchmarkRuntime(b)

	for _, size := range []int{64 << 10, 1 << 20} {
		size := size
		b.Run(strconv.Itoa(size)+"B", func(b *testing.B) {
			arguments := buildBenchmarkRequestArguments(size)
			upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				_, _ = io.Copy(io.Discard, r.Body)
				w.Header().Set("Content-Type", "application/json")
				_, _ = w.Write([]byte(`{"ok":true}`))
			}))
			defer upstream.Close()

			upstreamURL, err := url.Parse(upstream.URL)
			if err != nil {
				b.Fatalf("parse upstream URL: %v", err)
			}

			toolConfig := &ToolConfig{
				Name:   "large_json_request",
				Method: http.MethodPost,
				Host:   upstreamURL.Host,
				Schema: upstreamURL.Scheme,
				Url:    "/",
			}
			handler := genToolHandler(toolConfig, "bench-server", func() bool {
				return false
			})
			req := benchmarkCallToolRequest(toolConfig.Name, arguments)
			ctx := benchmarkToolCallContext(b)

			b.ReportAllocs()
			b.SetBytes(int64(len(arguments)))
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
}

// BenchmarkMCPToolCallWireDecode isolates the official SDK's inbound copies before
// genToolHandler starts: JSON-RPC decoding retains raw params, then MCP decoding retains
// raw arguments. HTTP request-body io.ReadAll is intentionally outside this benchmark.
func BenchmarkMCPToolCallWireDecode(b *testing.B) {
	for _, size := range []int{64 << 10, 1 << 20} {
		size := size
		b.Run(strconv.Itoa(size)+"B", func(b *testing.B) {
			wireBody := buildBenchmarkToolCallWireBody(size)

			b.ReportAllocs()
			b.SetBytes(int64(len(wireBody)))
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				message, err := jsonrpc.DecodeMessage(wireBody)
				if err != nil {
					b.Fatalf("decode JSON-RPC message: %v", err)
				}
				request, ok := message.(*jsonrpc.Request)
				if !ok {
					b.Fatalf("decoded message has type %T", message)
				}
				var params mcp.CallToolParamsRaw
				decoder := segmentjson.NewDecoder(bytes.NewReader(request.Params))
				decoder.DontMatchCaseInsensitiveStructFields()
				if err := decoder.Decode(&params); err != nil {
					b.Fatalf("decode tools/call params: %v", err)
				}
				benchmarkWireMessage = message
				benchmarkCallToolParams = params
			}
		})
	}
}

// BenchmarkMCPToolResultWireEncode isolates the official SDK's outbound copies after
// genToolHandler returns: CallToolResult is first marshaled into Response.Result, then
// the complete JSON-RPC response is encoded for the transport.
func BenchmarkMCPToolResultWireEncode(b *testing.B) {
	for _, size := range []int{64 << 10, 1 << 20} {
		size := size
		b.Run(strconv.Itoa(size)+"B", func(b *testing.B) {
			body := buildBenchmarkJSONBody(size)
			payload := newToolResponsePayload(200, "bench-upstream", "application/json", body)
			id, err := jsonrpc.MakeID(float64(1))
			if err != nil {
				b.Fatalf("make JSON-RPC id: %v", err)
			}

			for _, rawResponseEnabled := range []bool{false, true} {
				rawResponseEnabled := rawResponseEnabled
				mode := "envelope"
				if rawResponseEnabled {
					mode = "raw-response"
				}

				b.Run(mode, func(b *testing.B) {
					var resultBytes []byte
					if rawResponseEnabled {
						resultBytes, err = payload.marshalRawResponse()
					} else {
						resultBytes, err = payload.marshalEnvelope(
							"bench-trace",
							"bench-x-request",
						)
					}
					if err != nil {
						b.Fatalf("build tool result: %v", err)
					}
					result := buildToolResultFromJSONBytes(resultBytes)

					b.ReportAllocs()
					b.SetBytes(int64(len(body)))
					b.ResetTimer()
					for i := 0; i < b.N; i++ {
						encodedResult, err := json.Marshal(result)
						if err != nil {
							b.Fatalf("marshal CallToolResult: %v", err)
						}
						wire, err := jsonrpc.EncodeMessage(&jsonrpc.Response{
							ID:     id,
							Result: encodedResult,
						})
						if err != nil {
							b.Fatalf("encode JSON-RPC response: %v", err)
						}
						benchmarkWireBytes = wire
					}
				})
			}
		})
	}
}

// BenchmarkReadLargeResponseBody compares the previous unhinted io.ReadAll path with
// the production response reader when an upstream Content-Length is available.
func BenchmarkReadLargeResponseBody(b *testing.B) {
	for _, size := range []int{64 << 10, 1 << 20, 10 << 20} {
		size := size
		b.Run(strconv.Itoa(size)+"B", func(b *testing.B) {
			body := buildBenchmarkJSONBody(size)

			b.Run("current-io-read-all", func(b *testing.B) {
				b.ReportAllocs()
				b.SetBytes(int64(len(body)))
				for i := 0; i < b.N; i++ {
					reader := benchmarkChunkReader{body: body}
					readBody, err := io.ReadAll(&reader)
					if err != nil {
						b.Fatalf("read response body: %v", err)
					}
					benchmarkResponseBody = readBody
				}
			})

			b.Run("production-content-length", func(b *testing.B) {
				b.ReportAllocs()
				b.SetBytes(int64(len(body)))
				for i := 0; i < b.N; i++ {
					reader := benchmarkChunkReader{body: body}
					readBody, err := readResponseBody(&reader, strconv.Itoa(len(body)))
					if err != nil {
						b.Fatalf("read response body: %v", err)
					}
					benchmarkResponseBody = readBody
				}
			})
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
	b.Setenv("DEBUG", "")
	b.Setenv("SWAGGER_DEBUG", "")

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
	benchmarkMetricsInitOnce.Do(func() {
		metric.InitMetrics("benchmark_")
	})
	sharedTransportOnce = sync.Once{}
	sharedTransport = nil
	InitSharedTransport(config.Transport{
		MaxIdleConns:          100,
		MaxIdleConnsPerHost:   100,
		IdleConnTimeoutSecond: 90,
	})
}

func benchmarkCallToolRequest(name string, arguments json.RawMessage) *mcp.CallToolRequest {
	return &mcp.CallToolRequest{
		Params: &mcp.CallToolParamsRaw{
			Name:      name,
			Arguments: arguments,
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

func buildBenchmarkRequestArguments(targetSize int) json.RawMessage {
	body := buildBenchmarkJSONBody(targetSize)
	arguments := make([]byte, 0, len(body)+len(`{"body_param":}`))
	arguments = append(arguments, `{"body_param":`...)
	arguments = append(arguments, body...)
	arguments = append(arguments, '}')
	return json.RawMessage(arguments)
}

func buildBenchmarkToolCallWireBody(targetSize int) []byte {
	arguments := buildBenchmarkRequestArguments(targetSize)
	wireBody := make([]byte, 0, len(arguments)+96)
	wireBody = append(
		wireBody,
		`{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"large_json","arguments":`...)
	wireBody = append(wireBody, arguments...)
	wireBody = append(wireBody, `}}`...)
	return wireBody
}

type benchmarkChunkReader struct {
	body   []byte
	offset int
}

func (r *benchmarkChunkReader) Read(p []byte) (int, error) {
	if r.offset >= len(r.body) {
		return 0, io.EOF
	}
	if len(p) > 32<<10 {
		p = p[:32<<10]
	}
	n := copy(p, r.body[r.offset:])
	r.offset += n
	return n, nil
}
