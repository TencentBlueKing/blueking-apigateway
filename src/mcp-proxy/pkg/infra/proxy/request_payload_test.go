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
)

var _ = Describe("toolRequestPayload", func() {
	It("canonicalizes arguments once and preserves parameter semantics", func() {
		arguments := json.RawMessage(`{
			"header_param": {"X-Trace-ID": 2005000002},
			"query_param": {"ids": [2005000002, 9007199254740992]},
			"path_param": {"id": 7643696123382648115},
			"body_param": {"html": "<p>value</p>", "id": 7643696123382648115}
		}`)
		expected, err := json.Marshal(arguments)
		Expect(err).NotTo(HaveOccurred())

		payload, err := newToolRequestPayload(arguments)
		Expect(err).NotTo(HaveOccurred())
		Expect(payload.rawArguments).To(Equal(expected))
		Expect(payload.auditSize()).To(Equal(int64(len(expected))))
		Expect(payload.metricSize()).To(Equal(int64(len(expected))))

		handlerRequest, err := payload.decodeHandlerRequest()
		Expect(err).NotTo(HaveOccurred())
		Expect(handlerRequest.HeaderParam["X-Trace-ID"]).To(Equal("2005000002"))
		Expect(handlerRequest.QueryParam["ids"]).To(Equal([]string{"2005000002", "9007199254740992"}))
		Expect(handlerRequest.PathParam["id"]).To(Equal("7643696123382648115"))
		Expect(string(handlerRequest.BodyParam)).To(Equal(
			`{"html":"\u003cp\u003evalue\u003c/p\u003e","id":7643696123382648115}`,
		))
	})

	It("keeps the existing audit and API log truncation formats", func() {
		arguments := json.RawMessage(`{"body_param":{"value":"abcdefghijklmnopqrstuvwxyz"}}`)
		payload, err := newToolRequestPayload(arguments)
		Expect(err).NotTo(HaveOccurred())

		Expect(payload.auditPreview(20)).To(Equal(
			string(payload.rawArguments[:20]) + truncatedSuffix,
		))
		params, size := payload.apiLogPreview(20)
		Expect(params).To(Equal(string(payload.rawArguments[:20])))
		Expect(size).To(Equal(int64(len(payload.rawArguments))))

		handlerRequest, err := payload.decodeHandlerRequest()
		Expect(err).NotTo(HaveOccurred())
		Expect(payload.bodyAuditPreview(handlerRequest.BodyParam, 20)).To(Equal(
			string(handlerRequest.BodyParam[:20]) + truncatedSuffix,
		))
	})

	DescribeTable("preserves null request compatibility",
		func(arguments json.RawMessage) {
			payload, err := newToolRequestPayload(arguments)
			Expect(err).NotTo(HaveOccurred())

			handlerRequest, err := payload.decodeHandlerRequest()
			Expect(err).NotTo(HaveOccurred())
			Expect(payload.bodyAuditPreview(handlerRequest.BodyParam, 100)).To(Equal("null"))
		},
		Entry("missing body_param", json.RawMessage(`{}`)),
		Entry("explicit null body_param", json.RawMessage(`{"body_param":null}`)),
	)

	It("keeps nil arguments empty in API logs and metrics but null in audit logs", func() {
		payload, err := newToolRequestPayload(nil)
		Expect(err).NotTo(HaveOccurred())

		Expect(payload.auditPreview(100)).To(Equal("null"))
		Expect(payload.auditSize()).To(Equal(int64(4)))
		Expect(payload.metricSize()).To(BeZero())
		params, size := payload.apiLogPreview(100)
		Expect(params).To(BeEmpty())
		Expect(size).To(BeZero())
	})
})
