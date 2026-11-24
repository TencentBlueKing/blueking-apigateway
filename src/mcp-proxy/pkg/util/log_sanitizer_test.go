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
})
