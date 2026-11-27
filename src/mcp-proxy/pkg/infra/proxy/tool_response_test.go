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
	"errors"
	"fmt"

	"github.com/go-openapi/runtime"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("marshalToolResponse", func() {
	const upstreamJSON = " \n{\"value\": 1e+09, \"text\": \"<>&\"} \t"
	const envelopeJSON = `{"value":1e+09,"text":"\u003c\u003e\u0026"}`
	const plainText = "plain <>&\n"
	const quotedText = `"plain \u003c\u003e\u0026\n"`

	DescribeTable(
		"preserves response text and APIError payloads",
		func(statusCode int, raw bool, contentType, body, wantBody string, wantAPIError bool) {
			payload := newToolResponsePayload(statusCode, "req-1", contentType, []byte(body))
			text, err := marshalToolResponse(payload, "trace-1", "x-req-1", raw)
			wantText := wantBody
			if !raw {
				wantText = fmt.Sprintf(
					`{"status_code":%d,"request_id":"req-1","trace_id":"trace-1",`+
						`"x_request_id":"x-req-1","response_body":%s}`, statusCode, wantBody)
			}
			if !wantAPIError {
				Expect(err).NotTo(HaveOccurred())
				Expect(text).To(Equal(wantText))
				return
			}
			Expect(text).To(BeEmpty())
			var apiErr *runtime.APIError
			Expect(errors.As(err, &apiErr)).To(BeTrue())
			Expect(apiErr.Code).To(Equal(statusCode))
			Expect(apiErr.OperationName).To(Equal("call tool err"))
			Expect(apiErr.Response).To(Equal(json.RawMessage(wantText)))
		},
		Entry("JSON success envelope", 200, false, "application/json", upstreamJSON, envelopeJSON, false),
		Entry(
			"JSON success raw preserves whitespace",
			200,
			true,
			"application/json",
			upstreamJSON,
			upstreamJSON,
			false,
		),
		Entry("JSON error envelope", 500, false, "application/json", upstreamJSON, envelopeJSON, true),
		Entry(
			"JSON error raw preserves payload",
			500,
			true,
			"application/json",
			upstreamJSON,
			upstreamJSON,
			true,
		),
		Entry("status below 2xx is an API error", 199, false, "application/json", "null", "null", true),
		Entry("last 2xx status is successful", 299, false, "application/json", "null", "null", false),
		Entry("first 3xx status is an API error", 300, false, "application/json", "null", "null", true),
		Entry("text success envelope", 200, false, "text/plain", plainText, quotedText, false),
		Entry("text success raw", 200, true, "text/plain", plainText, quotedText, false),
		Entry("text error envelope", 500, false, "text/plain", plainText, quotedText, true),
		Entry("text error raw", 500, true, "text/plain", plainText, quotedText, true),
	)

	DescribeTable("validates declared JSON before constructing a response or APIError",
		func(statusCode int, raw bool) {
			payload := newToolResponsePayload(statusCode, "req-1", "application/json", []byte(`{"bad"`))
			text, err := marshalToolResponse(payload, "trace-1", "x-req-1", raw)
			Expect(text).To(BeEmpty())
			Expect(err).To(MatchError(`invalid JSON response body for Content-Type "application/json"`))
			var apiErr *runtime.APIError
			Expect(errors.As(err, &apiErr)).To(BeFalse())
		},
		Entry("success envelope", 200, false),
		Entry("success raw", 200, true),
		Entry("error envelope", 500, false),
		Entry("error raw", 500, true),
	)
})
