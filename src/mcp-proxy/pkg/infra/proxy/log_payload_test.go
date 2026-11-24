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
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"io"
	"mcp_proxy/pkg/infra/logging"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/util"
)

var _ = Describe("Sanitized payload copies", func() {
	It("keeps safe error categories without exposing network credentials", func() {
		var out bytes.Buffer
		logger := zap.New(zapcore.NewCore(zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()), zapcore.AddSync(&out), zap.DebugLevel), logging.WithDesensitize(nil))
		err := &url.Error{Op: "GET", URL: "https://credential-url:credential-password@example.com", Err: &net.DNSError{Err: "credential-error", Name: "credential-host", IsTimeout: true}}
		result := handleToolCallError(context.Background(), err, &ToolConfig{Name: "demo"}, logger, nil, nil, time.Now())
		Expect(result.IsError).To(BeTrue())
		Expect(out.String()).NotTo(ContainSubstring("credential-"))
		Expect(out.String()).To(ContainSubstring("timeout"))
	})

	It("keeps long sanitized previews useful after the final core validation", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		raw := json.RawMessage(`{"body_param":{"token":"credential-preview","message":"` + strings.Repeat("retained", 800) + `"}}`)
		payload, err := newToolRequestPayload(raw)
		Expect(err).NotTo(HaveOccurred())
		for _, text := range []string{payload.auditPreview(256), payload.bodyAuditPreview(256)} {
			Expect(json.Valid([]byte(text))).To(BeTrue())
			Expect(text).NotTo(ContainSubstring("credential-preview"))
			Expect(text).To(ContainSubstring("retained"))
			Expect(len(text)).To(BeNumerically("<=", 256))
			Expect(sanitizer.Sanitize("params", text)).NotTo(Equal(util.HiddenLogBody))
		}
		response := newToolResponsePayload(200, "req", "application/json", []byte(`{"token":"credential-preview","message":"`+strings.Repeat("retained", 800)+`"}`))
		text := response.EnvelopePreview("trace", "x-req", 256)
		final := sanitizer.Sanitize("response", text)
		Expect(final).NotTo(Equal(util.HiddenLogBody))
		Expect(final).To(ContainSubstring("retained"))
		Expect(final).To(ContainSubstring(`"request_id":"req"`))
		Expect(final).NotTo(ContainSubstring("credential-preview"))
	})

	It("writes valid long previews and safe status categories to API and Audit files", func() {
		offsets := credentialLogOffsets()
		arguments := json.RawMessage(`{"body_param":{"token":"credential-long-request","message":"` + strings.Repeat("retained", 800) + `"}}`)
		upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			raw, err := io.ReadAll(r.Body)
			Expect(err).NotTo(HaveOccurred())
			Expect(string(raw)).To(ContainSubstring("credential-long-request"))
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("X-Bkapi-Request-Id", "preview-req")
			w.WriteHeader(502)
			_, err = io.WriteString(w, `{"token":"credential-long-response","message":"`+strings.Repeat("retained", 800)+`"}`)
			Expect(err).NotTo(HaveOccurred())
		}))
		defer upstream.Close()
		result := callTestToolHandler(upstream.URL, false, arguments)
		Expect(result.IsError).To(BeTrue())
		Expect(result.Content[0].(*mcp.TextContent).Text).To(ContainSubstring("credential-long-response"))
		for _, log := range credentialReadLogs(offsets) {
			Expect(log).NotTo(ContainSubstring("credential-long-"))
			Expect(log).To(ContainSubstring("retained"))
			var entry map[string]any
			observed := false
			for _, line := range strings.Split(log, "\n") {
				if json.Unmarshal([]byte(line), &entry) != nil {
					continue
				}
				response, ok := entry["response"].(string)
				if !ok || response == "" {
					continue
				}
				observed = true
				Expect(json.Valid([]byte(response))).To(BeTrue())
				Expect(response).To(ContainSubstring("retained"))
				Expect(response).NotTo(ContainSubstring(util.HiddenLogBody))
			}
			Expect(observed).To(BeTrue())
		}
	})

	It("retains envelope IDs when a preview limit cannot carry its JSON keys", func() {
		payload := newToolResponsePayload(200, "req", "application/json", []byte(`{"long_member_name":"large-value"}`))
		text := payload.EnvelopePreview("trace", "x-req", 1)
		var envelope map[string]any
		Expect(json.Unmarshal([]byte(text), &envelope)).To(Succeed())
		Expect(envelope).To(HaveKeyWithValue("request_id", "req"))
		Expect(envelope).To(HaveKeyWithValue("response_body", util.HiddenLogBody))
	})

	It("reuses the safe copy across previews with identical rules", func() {
		copies := payloadLogCopies{}
		builds := 0
		build := func(*util.LogSanitizer) string { builds++; return `{"safe":true}` }
		copies.initialize(build)
		copies.initialize(build)
		Expect(builds).To(Equal(1))
		Expect(copies.apiText).To(Equal(copies.auditText))
	})
	It("keeps distinct API and audit rules and original bytes", func() {
		old := config.G
		cfg := *old
		cfg.Logger.API.Desensitization = config.DesensitizationConfig{
			Enabled: true,
			Fields: []config.DesensitizationFiled{
				{Key: "params", JsonPath: []string{"body_param.api_pin"}},
			},
		}
		cfg.Logger.Audit.Desensitization = config.DesensitizationConfig{
			Enabled: true,
			Fields: []config.DesensitizationFiled{
				{Key: "params", JsonPath: []string{"body_param.audit_pin"}},
			},
		}
		config.G = &cfg
		DeferCleanup(func() { config.G = old })
		raw := json.RawMessage(
			`{"body_param":{"token":"credential-default","api_pin":"api-value","audit_pin":"audit-value"}}`,
		)
		payload, err := newToolRequestPayload(raw)
		Expect(err).NotTo(HaveOccurred())
		api, size := payload.apiLogPreview(10000)
		audit := payload.auditPreview(10000)
		Expect(api).NotTo(ContainSubstring("credential-default"))
		Expect(audit).NotTo(ContainSubstring("credential-default"))
		Expect(api).NotTo(ContainSubstring("api-value"))
		Expect(api).To(ContainSubstring("audit-value"))
		Expect(audit).NotTo(ContainSubstring("audit-value"))
		Expect(audit).To(ContainSubstring("api-value"))
		Expect(size).To(Equal(int64(len(raw))))
		Expect(payload.rawArguments).To(Equal([]byte(raw)))
	})
	It("retains current envelope identifiers when reusing a response body", func() {
		payload := newToolResponsePayload(
			200,
			"upstream",
			"application/json",
			[]byte(`{"token":"credential-response","ok":true}`),
		)
		first := payload.EnvelopePreview("trace-first", "x-first", 10000)
		second := payload.EnvelopePreview("trace-second", "x-second", 10000)
		Expect(first).To(ContainSubstring(`"trace_id":"trace-first"`))
		Expect(second).To(ContainSubstring(`"trace_id":"trace-second"`))
		Expect(second).To(ContainSubstring(`"x_request_id":"x-second"`))
		Expect(second).NotTo(ContainSubstring("credential-response"))
	})
})
