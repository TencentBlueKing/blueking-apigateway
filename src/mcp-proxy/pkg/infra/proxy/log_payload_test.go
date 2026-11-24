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
	"encoding/json"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/util"
)

var _ = Describe("Sanitized payload copies", func() {
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
