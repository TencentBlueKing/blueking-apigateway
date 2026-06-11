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
	"strings"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("toolResponsePayload", func() {
	Describe("newToolResponsePayload", func() {
		It("captures JSON response metadata", func() {
			payload := newToolResponsePayload(
				200,
				"req-1",
				"application/json",
				[]byte(`{"items":[{"id":1}]}`),
			)

			Expect(payload.statusCode).To(Equal(200))
			Expect(payload.upstreamRequestID).To(Equal("req-1"))
			Expect(payload.contentType).To(Equal("application/json"))
			Expect(payload.rawBody).To(Equal([]byte(`{"items":[{"id":1}]}`)))
			Expect(payload.isDeclaredJSON).To(BeTrue())
		})

		It("classifies declared JSON by Content-Type without validating the body", func() {
			payload := newToolResponsePayload(200, "req-1", "application/json", []byte(`{"bad"`))
			Expect(payload.isDeclaredJSON).To(BeTrue())
		})

		It("treats non-JSON content type as non-JSON even when body is valid JSON", func() {
			payload := newToolResponsePayload(200, "req-1", "text/plain", []byte(`{"items":[]}`))
			Expect(payload.isDeclaredJSON).To(BeFalse())
		})
	})

	Describe("EnvelopePreview body field", func() {
		It("returns null for empty body", func() {
			payload := newToolResponsePayload(204, "", "application/json", nil)
			out := payload.EnvelopePreview("", "", 100)
			Expect(out).To(ContainSubstring(`"response_body":null`))
			Expect(out).To(ContainSubstring(`"status_code":204`))
		})

		It("embeds raw JSON when valid and fits within limit", func() {
			payload := newToolResponsePayload(200, "req-1", "application/json", []byte(`{"a":1,"b":[2,3]}`))
			out := payload.EnvelopePreview("trace-1", "x-req-1", 100)
			Expect(out).To(MatchJSON(`{
				"status_code": 200,
				"request_id": "req-1",
				"trace_id": "trace-1",
				"x_request_id": "x-req-1",
				"response_body": {"a":1,"b":[2,3]}
			}`))
		})

		It("falls back to JSON string when JSON body needs truncation", func() {
			big := []byte(`{"items":[` + strings.Repeat(`1,`, 1000) + `0]}`)
			payload := newToolResponsePayload(200, "", "application/json", big)
			out := payload.EnvelopePreview("", "", 50)
			// response_body becomes a quoted string ending with the truncated suffix
			Expect(out).To(ContainSubstring(`"response_body":"`))
			Expect(out).To(ContainSubstring(truncatedSuffix))
		})

		It("preserves non-JSON HTML body as a JSON string", func() {
			html := []byte(`<html><body>500 Internal Server Error</body></html>`)
			payload := newToolResponsePayload(500, "upstream-req-1", "text/html", html)
			out := payload.EnvelopePreview("trace-1", "x-req-1", 16384)
			Expect(out).To(MatchJSON(`{
				"status_code": 500,
				"request_id": "upstream-req-1",
				"trace_id": "trace-1",
				"x_request_id": "x-req-1",
				"response_body": "<html><body>500 Internal Server Error</body></html>"
			}`))
			Expect(out).NotTo(ContainSubstring(`"response_body":null`))
		})

		It("preserves non-JSON plain text body as a JSON string", func() {
			payload := newToolResponsePayload(
				500,
				"",
				"text/plain; charset=utf-8",
				[]byte("upstream timeout"),
			)
			out := payload.EnvelopePreview("", "", 16384)
			Expect(out).To(ContainSubstring(`"response_body":"upstream timeout"`))
		})

		It("preserves malformed JSON body (Content-Type lied) as a JSON string", func() {
			payload := newToolResponsePayload(500, "", "application/json", []byte(`{not valid json`))
			out := payload.EnvelopePreview("", "", 16384)
			Expect(out).To(ContainSubstring(`"response_body":"{not valid json"`))
			Expect(out).NotTo(ContainSubstring(`"response_body":null`))
		})

		It("truncates non-JSON bodies that exceed the limit", func() {
			huge := []byte(strings.Repeat("x", 5000))
			payload := newToolResponsePayload(500, "", "text/plain", huge)
			out := payload.EnvelopePreview("", "", 100)
			Expect(out).To(ContainSubstring(truncatedSuffix))
		})
	})

	Describe("marshalEnvelope", func() {
		It("marshals JSON response into the envelope without changing response semantics", func() {
			payload := newToolResponsePayload(
				200,
				"req-1",
				"application/json",
				[]byte(`{"items":[1]}`),
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
			payload := newToolResponsePayload(200, "req-1", "text/plain", []byte(`plain text`))
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

		It("preserves empty non-JSON response body as an empty string in the envelope", func() {
			payload := newToolResponsePayload(200, "req-1", "text/plain", []byte{})
			data, err := payload.marshalEnvelope("", "")

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(MatchJSON(`{
				"status_code": 200,
				"request_id": "req-1",
				"trace_id": "",
				"x_request_id": "",
				"response_body": ""
			}`))
		})

		It("returns an error for invalid non-empty bodies declared as JSON", func() {
			payload := newToolResponsePayload(200, "req-1", "application/json", []byte(`{"bad"`))
			data, err := payload.marshalEnvelope("", "")

			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("invalid JSON response body"))
			Expect(data).To(BeNil())
		})
	})

	Describe("marshalRawResponse", func() {
		It("returns raw JSON body unchanged for valid JSON responses", func() {
			payload := newToolResponsePayload(
				200,
				"req-1",
				"application/json",
				[]byte(`{"items":[1]}`),
			)
			data, err := payload.marshalRawResponse()

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(MatchJSON(`{"items":[1]}`))
		})

		It("returns non-JSON response body as a JSON string", func() {
			body := []byte("plain \"quoted\"\nline")
			payload := newToolResponsePayload(200, "req-1", "text/plain; charset=utf-8", body)
			data, err := payload.marshalRawResponse()

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(Equal(`"plain \"quoted\"\nline"`))
		})

		It("preserves empty non-JSON response body as an empty JSON string", func() {
			payload := newToolResponsePayload(200, "req-1", "text/plain", []byte{})
			data, err := payload.marshalRawResponse()

			Expect(err).NotTo(HaveOccurred())
			Expect(string(data)).To(Equal(`""`))
		})

		It("returns an error for invalid non-empty bodies declared as JSON", func() {
			payload := newToolResponsePayload(200, "req-1", "application/json", []byte(`{"bad"`))
			data, err := payload.marshalRawResponse()

			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("invalid JSON response body"))
			Expect(data).To(BeNil())
		})
	})
})
