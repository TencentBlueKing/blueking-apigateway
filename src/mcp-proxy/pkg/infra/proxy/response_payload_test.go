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
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("toolResponsePayload", func() {
	Describe("newToolResponsePayload", func() {
		It("captures JSON response metadata and preview", func() {
			payload := newToolResponsePayload(
				200,
				"req-1",
				"application/json",
				[]byte(`{"items":[{"id":1}]}`),
				10,
			)

			Expect(payload.statusCode).To(Equal(200))
			Expect(payload.upstreamRequestID).To(Equal("req-1"))
			Expect(payload.contentType).To(Equal("application/json"))
			Expect(payload.rawBody).To(Equal([]byte(`{"items":[{"id":1}]}`)))
			Expect(payload.isJSON).To(BeTrue())
			Expect(payload.truncatedPreview).To(Equal(`{"items":[...(truncated)`))
		})
	})

	Describe("marshalEnvelope", func() {
		It("marshals JSON response into the envelope without changing response semantics", func() {
			payload := newToolResponsePayload(
				200,
				"req-1",
				"application/json",
				[]byte(`{"items":[1]}`),
				4096,
			)
			data, err := payload.marshalEnvelope("trace-1", "x-req-1")

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(MatchJSON(`{
				"status_code": 200,
				"request_id": "req-1",
				"trace_id": "trace-1",
				"x_request_id": "x-req-1",
				"response_body": {"items":[1]}
			}`))
		})

		It("marshals non-JSON response body as a JSON string", func() {
			payload := newToolResponsePayload(200, "req-1", "text/plain", []byte(`plain text`), 4096)
			data, err := payload.marshalEnvelope("", "")

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(MatchJSON(`{
				"status_code": 200,
				"request_id": "req-1",
				"trace_id": "",
				"x_request_id": "",
				"response_body": "plain text"
			}`))
		})
	})

	Describe("marshalRawResponse", func() {
		It("returns raw JSON body unchanged for valid JSON responses", func() {
			payload := newToolResponsePayload(
				200,
				"req-1",
				"application/json",
				[]byte(`{"items":[1]}`),
				4096,
			)
			data, err := payload.marshalRawResponse()

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(MatchJSON(`{"items":[1]}`))
		})

		It("treats invalid JSON content type as string body", func() {
			payload := newToolResponsePayload(200, "req-1", "application/json", []byte(`{"bad"`), 4096)
			data, err := payload.marshalRawResponse()

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(MatchJSON(`"{\"bad\""`))
		})
	})
})
