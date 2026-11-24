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

package util_test

import (
	"encoding/json"
	"net/url"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/util"
)

var _ = Describe("Bounded credential log sanitizer", func() {
	It("keeps mixed arrays, empty values and numbers while masking whole credentials", func() {
		sanitizer := util.NewLogSanitizer(
			config.DesensitizationConfig{SensitiveHeaders: []string{"X-Custom-Auth"}},
		)
		input := `[{"AUTHORIZATION":{"value":"credential-object"},"token":false,"password":0,"secret":[],"client_secret":null,"X-Custom-Auth":"credential-header","items":[1,[{"api_key":"credential-array"}]],"status_code":200},{"t\u006fken":"credential-escaped"}]`
		original := input
		output := sanitizer.JSON("body", []byte(input))
		Expect(output).NotTo(ContainSubstring("credential-"))
		Expect(
			output,
		).To(
			MatchJSON(
				`[{"AUTHORIZATION":"***","token":"***","password":"***","secret":[],"client_secret":null,"X-Custom-Auth":"***","items":[1,[{"api_key":"***"}]],"status_code":200},{"token":"***"}]`,
			),
		)
		Expect(input).To(Equal(original))
		Expect(sanitizer.JSON("body", []byte("null"))).To(Equal("null"))
	})
	It("preserves repeated encoded form parameters and rejects ambiguous JSON", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		result := sanitizer.Sanitize(
			"query",
			"t%6fken=credential-first&token=credential-second&keep=one&keep=two&blank=",
		)
		values, err := url.ParseQuery(result.(string))
		Expect(err).NotTo(HaveOccurred())
		Expect(values["token"]).To(Equal([]string{"***", "***"}))
		Expect(values["keep"]).To(Equal([]string{"one", "two"}))
		Expect(values["blank"]).To(Equal([]string{""}))
		for _, raw := range []string{`{"token":"credential=value`, `[{"token":"credential=value`, `"credential=value`, "token=%zz", "token=credential\nvalue"} {
			Expect(sanitizer.Sanitize("body", raw)).To(Equal(util.HiddenLogBody))
		}
	})
	It("applies arbitrary field paths additively to objects and serialized values", func() {
		sanitizer := util.NewLogSanitizer(
			config.DesensitizationConfig{
				Enabled: true,
				Fields: []config.DesensitizationFiled{
					{Key: "custom", JsonPath: []string{"rows.#.pin"}},
				},
			},
		)
		input := map[string]any{"rows": []any{map[string]any{"pin": 0, "token": "credential-default"}}}
		safe := sanitizer.Sanitize("CUSTOM", input)
		encoded, err := json.Marshal(safe)
		Expect(err).NotTo(HaveOccurred())
		Expect(string(encoded)).To(MatchJSON(`{"rows":[{"pin":"***","token":"***"}]}`))
		Expect(input["rows"].([]any)[0].(map[string]any)["pin"]).To(Equal(0))
		raw, err := json.Marshal(input)
		Expect(err).NotTo(HaveOccurred())
		Expect(sanitizer.JSON("custom", raw)).To(MatchJSON(string(encoded)))
	})
	It("sanitizes SDK content in both object and wire representations", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		result := &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: `{"token":"credential-sdk"}`},
				&mcp.TextContent{Text: "credential-unknown"},
			},
		}
		safe := sanitizer.Sanitize("result", result)
		encoded, err := json.Marshal(safe)
		Expect(err).NotTo(HaveOccurred())
		Expect(string(encoded)).NotTo(ContainSubstring("credential-"))
		Expect(string(encoded)).To(ContainSubstring(util.HiddenLogBody))
		Expect(string(encoded)).To(ContainSubstring(`"type":"text"`))
		raw, err := json.Marshal(result)
		Expect(err).NotTo(HaveOccurred())
		Expect(sanitizer.JSON("result", raw)).NotTo(ContainSubstring("credential-"))
		Expect(result.Content[0].(*mcp.TextContent).Text).To(Equal(`{"token":"credential-sdk"}`))
	})
	It("fails closed for byte, node, depth, decode budgets and cycles", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		cyclic := map[string]any{"token": "credential-cycle"}
		cyclic["data"] = cyclic
		inputs := []any{
			strings.Repeat("credential-bytes", 100000), make([]any, 10001), cyclic,
			strings.Repeat(`{"data":`, 40) + `{"token":"credential-depth"}` + strings.Repeat("}", 40),
		}
		nested := `{"token":"credential-decode"}`
		for range 5 {
			raw, err := json.Marshal(nested)
			Expect(err).NotTo(HaveOccurred())
			nested = string(raw)
		}
		inputs = append(inputs, nested)
		for _, input := range inputs {
			Expect(sanitizer.Sanitize("body", input)).To(Equal(util.HiddenLogBody))
		}
		Expect(
			sanitizer.JSON("body", []byte(strings.Repeat("credential-bytes", 100000))),
		).To(
			Equal(util.HiddenLogBody),
		)
	})
	It("rejects unknown equals-bearing bodies instead of guessing forms", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		for _, raw := range []string{
			`<html><input name="token" value="credential-html"></html>`,
			`<token value="credential-xml"/>`,
			`Authorization: Bearer credential-header=tail`,
			`name=credential raw`, `name=credential=tail`, `=credential`, `name=%zz`,
			`name=credential&`, `name=credential&&keep=yes`, `name=credential/path`,
		} {
			for _, key := range []string{"body", "request_body", "body_param", "response_body"} {
				Expect(sanitizer.Sanitize(key, raw)).To(Equal(util.HiddenLogBody), key+": "+raw)
				Expect(sanitizer.JSON(key, []byte(raw))).To(Equal(util.HiddenLogBody), key+": "+raw)
			}
		}
		Expect(sanitizer.Sanitize("response_body", "token=credential-response")).To(Equal(util.HiddenLogBody))
	})
	It("preserves ordinary business carrier names in every payload representation", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		raw := `{"query":"hello","response":"ok","request":"GET","result":"success","id":1,"items":[{"query":"hello","token":"credential-business"}]}`
		expected := `{"query":"hello","response":"ok","request":"GET","result":"success","id":1,"items":[{"query":"hello","token":"***"}]}`
		var object any
		Expect(json.Unmarshal([]byte(raw), &object)).To(Succeed())
		for _, key := range []string{"body", "response_body", "params", "request", "response", "result", "custom"} {
			Expect(sanitizer.JSON(key, []byte(raw))).To(MatchJSON(expected), key)
			for _, input := range []any{raw, object, json.RawMessage(raw)} {
				output := sanitizer.Sanitize(key, input)
				if text, ok := output.(string); ok {
					Expect(text).To(MatchJSON(expected), key)
				} else {
					encoded, err := json.Marshal(output)
					Expect(err).NotTo(HaveOccurred())
					Expect(string(encoded)).To(MatchJSON(expected), key)
				}
			}
		}
	})
	It("preserves business request and response form values while masking credentials", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		for _, key := range []string{"body", "query", "params"} {
			output := sanitizer.JSON(
				key,
				[]byte("request=GET&response=ok&result=success&token=credential-form"),
			)
			values, err := url.ParseQuery(output)
			Expect(err).NotTo(HaveOccurred())
			Expect(values.Get("request")).To(Equal("GET"), key)
			Expect(values.Get("response")).To(Equal("ok"), key)
			Expect(values.Get("result")).To(Equal("success"), key)
			Expect(values.Get("token")).To(Equal(util.CredentialMask), key)
		}
	})
	It("dispatches outer log records while retaining nested body and SDK safeguards", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		record := map[string]any{
			"query": "token=credential-query&keep=yes", "request_id": "request-safe",
			"body": "credential-unknown", "error": "credential-error",
			"response": `{"status_code":200,"response_body":"credential-response","result":"ok"}`,
		}
		safe, ok := sanitizer.Sanitize("", record).(map[string]any)
		Expect(ok).To(BeTrue())
		Expect(safe["query"]).To(Equal("token=%2A%2A%2A&keep=yes"))
		Expect(safe["request_id"]).To(Equal("request-safe"))
		Expect(safe["body"]).To(Equal(util.HiddenLogBody))
		Expect(safe["error"]).To(Equal(util.CredentialMask))
		var response map[string]any
		Expect(json.Unmarshal([]byte(safe["response"].(string)), &response)).To(Succeed())
		Expect(response["response_body"]).To(Equal(util.HiddenLogBody))
		Expect(response["result"]).To(Equal("ok"))
		raw, err := json.Marshal(record)
		Expect(err).NotTo(HaveOccurred())
		Expect(sanitizer.JSON("", raw)).NotTo(ContainSubstring("credential-"))
		body := `{"nested":{"body":"credential-body","response_body":"credential-response"},"content":[{"type":"text","text":"credential-sdk"}],"result":"success"}`
		var decoded map[string]any
		Expect(json.Unmarshal([]byte(sanitizer.JSON("body", []byte(body))), &decoded)).To(Succeed())
		Expect(decoded["result"]).To(Equal("success"))
		Expect(
			decoded["nested"],
		).To(
			Equal(map[string]any{"body": util.HiddenLogBody, "response_body": util.HiddenLogBody}),
		)
		Expect(decoded["content"]).To(Equal([]any{map[string]any{"type": "text", "text": util.HiddenLogBody}}))
	})
	It("keeps ordinary paths and invalid structured prefixes as metadata", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		for _, text := range []string{"dir/a.txt", "[WARN] retry", "{name} is required", "[Beta] tool description"} {
			for _, key := range []string{"path", "message", "description"} {
				Expect(sanitizer.Sanitize(key, text)).To(Equal(text), key)
			}
		}
		raw := `{"path":"dir/a.txt","message":"[WARN] retry","description":"{name} is required"}`
		Expect(sanitizer.JSON("body", []byte(raw))).To(MatchJSON(raw))
		for _, text := range []string{"[WARN] retry", "{name} is required"} {
			Expect(sanitizer.Sanitize("body", text)).To(Equal(util.HiddenLogBody))
			Expect(sanitizer.Sanitize("response_body", text)).To(Equal(util.HiddenLogBody))
			result := &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: text}}}
			encoded, err := json.Marshal(sanitizer.Sanitize("result", result))
			Expect(err).NotTo(HaveOccurred())
			Expect(string(encoded)).To(ContainSubstring(util.HiddenLogBody))
		}
	})
	It("masks valid embedded JSON strings in arrays, business fields and metadata", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		raw := `["{\"token\":\"credential-array\"}",{"data":"{\"token\":\"credential-data\"}"}]`
		expected := `["{\"token\":\"***\"}",{"data":"{\"token\":\"***\"}"}]`
		Expect(sanitizer.JSON("body", []byte(raw))).To(MatchJSON(expected))
		for _, key := range []string{"path", "message", "data"} {
			Expect(sanitizer.Sanitize(key, `{"token":"credential-embedded","query":"hello"}`)).To(
				MatchJSON(`{"token":"***","query":"hello"}`), key,
			)
		}
	})
	It("preserves business error metadata and SDK isError types", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		raw := `{"error":"missing argument","panic":"retry","isError":true,"parseError":"bad format","token":"credential-error"}`
		expected := `{"error":"missing argument","panic":"retry","isError":true,"parseError":"bad format","token":"***"}`
		for _, key := range []string{"body", "params", "response", "result"} {
			Expect(sanitizer.JSON(key, []byte(raw))).To(MatchJSON(expected), key)
		}
		result := &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: `{"error":"missing argument"}`}},
		}
		encoded, err := json.Marshal(sanitizer.Sanitize("result", result))
		Expect(err).NotTo(HaveOccurred())
		Expect(
			string(encoded),
		).To(
			MatchJSON(
				`{"isError":true,"content":[{"type":"text","text":"{\"error\":\"missing argument\"}"}]}`,
			),
		)
	})
	It("keeps structured top-level error classifications and masks unknown error text", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		raw := `{"category":"jsonrpc_error","code":-32602,"status_code":400}`
		for _, key := range []string{"error", "panic", "ERROR", "PANIC"} {
			Expect(sanitizer.Sanitize(key, "credential-raw")).To(Equal(util.CredentialMask), key)
			Expect(
				sanitizer.Sanitize(key, `{"category":"credential-invalid`),
			).To(
				Equal(util.CredentialMask),
				key,
			)
			Expect(sanitizer.JSON(key, []byte(raw))).To(MatchJSON(raw), key)
			Expect(sanitizer.Sanitize(key, "")).To(Equal(""), key)
			Expect(sanitizer.Sanitize(key, nil)).To(BeNil(), key)
			Expect(sanitizer.Sanitize(key, true)).To(BeTrue(), key)
			var object any
			Expect(json.Unmarshal([]byte(raw), &object)).To(Succeed())
			encoded, err := json.Marshal(sanitizer.Sanitize(key, object))
			Expect(err).NotTo(HaveOccurred())
			Expect(string(encoded)).To(MatchJSON(raw), key)
		}
	})
	It("rejects arbitrary JSON errors unless they contain only a safe classification", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		for _, raw := range []string{
			`{"message":"credential-error"}`, `{"category":"credential-error"}`,
			`{"category":"invalid_json","token":"credential-error"}`,
			`{"category":"invalid_json","error":"credential-error"}`,
			`{"category":"invalid_json","code":"credential-error"}`,
			`{"category":"invalid_json","status_code":true}`, `[{"category":"invalid_json"}]`,
		} {
			for _, key := range []string{"error", "panic"} {
				Expect(sanitizer.JSON(key, []byte(raw))).To(Equal(util.CredentialMask), key)
				var value any
				Expect(json.Unmarshal([]byte(raw), &value)).To(Succeed())
				Expect(sanitizer.Sanitize(key, value)).To(Equal(util.CredentialMask), key)
			}
		}
		for _, category := range []string{
			"panic", "error_details_hidden", "timeout", "dns_error", "network_error", "connection_refused",
			"invalid_parameter_type", "invalid_json", "upstream_http_error", "jsonrpc_error", "canceled", "deadline_exceeded",
		} {
			raw := `{"category":"` + category + `"}`
			Expect(sanitizer.JSON("error", []byte(raw))).To(MatchJSON(raw))
		}
	})
	It("supports HandlerRequest fields without reinterpreting ordinary params business names", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		raw := `{"query_param":"token=credential-query&keep=yes","header_param":{"Authorization":"credential-header"},"path_param":{"name":"{name} is required"},"body_param":{"error":"missing argument","query":"hello"},"query":"hello","error":"missing argument"}`
		expected := `{"query_param":"token=%2A%2A%2A&keep=yes","header_param":{"Authorization":"***"},"path_param":{"name":"{name} is required"},"body_param":{"error":"missing argument","query":"hello"},"query":"hello","error":"missing argument"}`
		for _, key := range []string{"params", "arguments", "request"} {
			Expect(sanitizer.JSON(key, []byte(raw))).To(MatchJSON(expected), key)
			var object any
			Expect(json.Unmarshal([]byte(raw), &object)).To(Succeed())
			encoded, err := json.Marshal(sanitizer.Sanitize(key, object))
			Expect(err).NotTo(HaveOccurred())
			Expect(string(encoded)).To(MatchJSON(expected), key)
		}
	})
	It("preserves quoted prose and masks multiply serialized embedded JSON", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		embedded := `{"token":"credential-quoted","query":"hello"}`
		expected := `{"query":"hello","token":"***"}`
		for range 2 {
			raw, err := json.Marshal(embedded)
			Expect(err).NotTo(HaveOccurred())
			embedded = string(raw)
			raw, err = json.Marshal(expected)
			Expect(err).NotTo(HaveOccurred())
			expected = string(raw)
			Expect(sanitizer.Sanitize("message", embedded)).To(MatchJSON(expected))
			raw, err = json.Marshal([]any{embedded})
			Expect(err).NotTo(HaveOccurred())
			output := sanitizer.JSON("body", raw)
			Expect(output).NotTo(ContainSubstring("credential-quoted"))
			var items []string
			Expect(json.Unmarshal([]byte(output), &items)).To(Succeed())
			Expect(items[0]).To(MatchJSON(expected))
		}
		for _, text := range []string{`"ordinary prose"`, `"{name} is required"`, `"[WARN] retry"`} {
			Expect(sanitizer.Sanitize("message", text)).To(Equal(text))
		}
	})
	It("hides credible truncated JSON inside supported arrays and business fields", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		for _, fragment := range []string{
			`{"token":"credential-truncated`, `{ "token": "credential-truncated`,
			`[{"token":"credential-truncated`, `["credential-truncated`,
			`[null,{"token":"credential-truncated`,
			`"{\"token\":\"credential-truncated`, `"  [\"credential-truncated`,
		} {
			for _, value := range []any{[]any{fragment}, []any{map[string]any{"data": fragment}}} {
				raw, err := json.Marshal(value)
				Expect(err).NotTo(HaveOccurred())
				output := sanitizer.JSON("body", raw)
				Expect(output).NotTo(ContainSubstring("credential-truncated"))
				Expect(output).To(ContainSubstring(util.HiddenLogBody))
			}
			quoted, err := json.Marshal(fragment)
			Expect(err).NotTo(HaveOccurred())
			Expect(
				sanitizer.Sanitize("message", string(quoted)),
			).NotTo(
				ContainSubstring("credential-truncated"),
			)
		}
	})
	It("aligns strict body forms and bare query flags with the shared wire grammar", func() {
		sanitizer := util.NewLogSanitizer(config.DesensitizationConfig{})
		for _, key := range []string{"body", "query", "query_param", "params"} {
			output := sanitizer.JSON(key, []byte("keep=*.~_-+%2F&token=credential-wire"))
			values, err := url.ParseQuery(output)
			Expect(err).NotTo(HaveOccurred())
			Expect(values.Get("keep")).To(Equal("*.~_- /"), key)
			Expect(values.Get("token")).To(Equal(util.CredentialMask), key)
		}
		for _, key := range []string{"query", "query_param", "params"} {
			output := sanitizer.JSON(key, []byte("debug&token=credential-flag&id=1"))
			values, err := url.ParseQuery(output)
			Expect(err).NotTo(HaveOccurred())
			Expect(values["debug"]).To(Equal([]string{""}), key)
			Expect(values.Get("token")).To(Equal(util.CredentialMask), key)
			Expect(values.Get("id")).To(Equal("1"), key)
			Expect(sanitizer.Sanitize(key, "debug")).To(Equal("debug="), key)
		}
		Expect(sanitizer.Sanitize("body", "debug&token=credential-flag")).To(Equal(util.HiddenLogBody))
	})
})
