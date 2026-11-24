/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * http://opensource.org/licenses/MIT
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package proxy

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/constant"
	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Credential masking tool pipeline", func() {
	DescribeTable("protects emitted API and audit logs without changing forwarding", func(status int, raw bool) {
		offsets := credentialLogOffsets()
		arguments := json.RawMessage(
			`{"header_param":{"aUtHoRiZaTiOn":"credential-header"},"query_param":{"token":["credential-query-1","credential-query-2"],"keep":["one","two"]},"body_param":{"BK_APP_SECRET":"credential-body","nested":{"body":"{\"access_token\":\"credential-embedded\"}"}}}`,
		)
		original := append([]byte(nil), arguments...)
		upstreamResponse := `{"token":"credential-response","ok":true}`
		var body []byte
		var authorization string
		var tokens []string
		upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			body, _ = io.ReadAll(r.Body)
			authorization = r.Header.Get("Authorization")
			tokens = r.URL.Query()["token"]
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set(constant.BkGatewayRequestIDKey, "upstream-req")
			w.WriteHeader(status)
			_, _ = io.WriteString(w, upstreamResponse)
		}))
		defer upstream.Close()
		result := callTestToolHandler(upstream.URL, raw, arguments)
		Expect([]byte(arguments)).To(Equal(original))
		Expect(authorization).To(Equal("credential-header"))
		Expect(tokens).To(Equal([]string{"credential-query-1", "credential-query-2"}))
		Expect(string(body)).To(ContainSubstring("credential-body"))
		Expect(result.IsError).To(Equal(status >= 400))
		Expect(result.Content[0].(*mcp.TextContent).Text).To(ContainSubstring("credential-response"))
		if raw && status == 200 {
			Expect(result.Content[0].(*mcp.TextContent).Text).To(MatchJSON(upstreamResponse))
		}
		logs := credentialReadLogs(offsets)
		for _, log := range logs {
			Expect(log).NotTo(ContainSubstring("credential-"))
			Expect(log).To(ContainSubstring("***"))
			var entry map[string]any
			for _, line := range strings.Split(log, "\n") {
				if json.Unmarshal([]byte(line), &entry) == nil && entry["response"] != nil {
					Expect(entry["request_body_size"]).To(Equal(float64(len(arguments))))
					Expect(entry["response_body_size"]).To(Equal(float64(len(upstreamResponse))))
				}
			}
		}
	},
		Entry("success envelope", 200, false), Entry("failure envelope", 500, false),
		Entry("success raw", 200, true), Entry("failure raw", 500, true),
	)

	It("protects parse failures and signing failures while retaining original arguments", func() {
		for _, arguments := range []json.RawMessage{
			json.RawMessage(`{"body_param":{"token":"credential-parse"},"query_param":"invalid"}`),
			json.RawMessage(`{"body_param":{"token":"credential-truncated`),
		} {
			offsets := credentialLogOffsets()
			original := append([]byte(nil), arguments...)
			handler := genToolHandler(
				&ToolConfig{Name: "list_items"},
				"test-server",
				func() bool { return false },
			)
			_, err := handler(testToolCallContext(), &mcp.CallToolRequest{
				Params: &mcp.CallToolParamsRaw{Name: "list_items", Arguments: arguments},
			})
			Expect(err).To(HaveOccurred())
			Expect([]byte(arguments)).To(Equal(original))
			for _, log := range credentialReadLogs(offsets) {
				Expect(log).NotTo(ContainSubstring("credential-"))
			}
		}
		offsets := credentialLogOffsets()
		handler := genToolHandler(&ToolConfig{Name: "list_items"}, "test-server", func() bool { return false })
		ctx := context.WithValue(testToolCallContext(), constant.BkGatewayPrivateKey, []byte(nil))
		_, err := handler(ctx, &mcp.CallToolRequest{Params: &mcp.CallToolParamsRaw{
			Name: "list_items", Arguments: json.RawMessage(`{"body_param":{"token":"credential-signing"}}`),
		}})
		Expect(err).To(HaveOccurred())
		for _, log := range credentialReadLogs(offsets) {
			Expect(log).NotTo(ContainSubstring("credential-"))
		}
	})

	DescribeTable(
		"hides bad upstream bodies in emitted envelopes",
		func(body, contentType string) {
			offsets := credentialLogOffsets()
			upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
				w.Header().Set("Content-Type", contentType)
				w.Header().Set(constant.BkGatewayRequestIDKey, "upstream-req")
				w.WriteHeader(502)
				_, _ = io.WriteString(w, body)
			}))
			defer upstream.Close()
			callTestToolHandler(upstream.URL, false)
			for _, log := range credentialReadLogs(offsets) {
				Expect(log).NotTo(ContainSubstring("credential-"))
				Expect(log).To(ContainSubstring("正文已屏蔽：截断或格式未知，无法可靠脱敏"))
				Expect(log).To(ContainSubstring("upstream-req"))
			}
		},
		Entry("invalid JSON", `{"token":"credential-bad`, "application/json"),
		Entry("unknown text", "credential-plain", "text/plain"),
		Entry("huge JSON", `{"value":"`+strings.Repeat("credential-huge", 90000)+`"}`, "application/json"),
		Entry(
			"too deep",
			strings.Repeat(`{"body":`, 40)+`{"token":"credential-deep"}`+strings.Repeat("}", 40),
			"application/json",
		),
	)
})

func credentialLogOffsets() map[string]int64 {
	offsets := make(map[string]int64)
	for _, path := range []string{apiLogPath, auditLogPath} {
		if info, err := os.Stat(path); err == nil {
			offsets[path] = info.Size()
		}
	}
	return offsets
}

func credentialReadLogs(offsets map[string]int64) []string {
	Expect(logging.GetAPILogger().Sync()).To(Succeed())
	Expect(logging.GetAuditLoggerWithContext(context.Background()).Sync()).To(Succeed())
	logs := make([]string, 0, 2)
	for _, path := range []string{apiLogPath, auditLogPath} {
		data, err := os.ReadFile(path)
		Expect(err).NotTo(HaveOccurred())
		logs = append(logs, string(data[offsets[path]:]))
	}
	return logs
}
