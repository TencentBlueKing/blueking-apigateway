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
	"errors"
	"io"
	"strconv"
	"strings"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("readResponseBody", func() {
	DescribeTable("reads the complete response body regardless of the Content-Length hint",
		func(contentLength, body string) {
			result, err := readResponseBody(strings.NewReader(body), contentLength)

			Expect(err).NotTo(HaveOccurred())
			Expect(result).To(Equal([]byte(body)))
		},
		Entry("with an exact length", "13", "complete-body"),
		Entry("without a length", "", "complete-body"),
		Entry("with an invalid length", "not-a-number", "complete-body"),
		Entry("with a zero length", "0", "complete-body"),
		Entry("with a negative length", "-1", "complete-body"),
		Entry("with a length above the preallocation limit",
			strconv.Itoa(maxResponseBodyPreallocateSize+1), "complete-body"),
		Entry("with an underestimated length", "3", "complete-body"),
		Entry("with an overestimated length", "1024", "complete-body"),
	)

	It("returns bytes read before a reader error and preserves the error", func() {
		readErr := errors.New("response read failed")
		reader := &errorResponseReader{
			body: []byte("partial-body"),
			err:  readErr,
		}

		result, err := readResponseBody(reader, strconv.Itoa(len(reader.body)))

		Expect(result).To(Equal([]byte("partial-body")))
		Expect(err).To(MatchError(readErr))
	})
})

type errorResponseReader struct {
	body []byte
	err  error
}

func (r *errorResponseReader) Read(p []byte) (int, error) {
	if len(r.body) == 0 {
		return 0, r.err
	}

	n := copy(p, r.body)
	r.body = r.body[n:]
	if len(r.body) == 0 {
		return n, r.err
	}
	return n, nil
}

var _ io.Reader = (*errorResponseReader)(nil)
