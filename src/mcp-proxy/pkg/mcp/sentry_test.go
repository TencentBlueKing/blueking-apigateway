/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

package mcp_test

import (
	"errors"
	"fmt"

	"github.com/modelcontextprotocol/go-sdk/jsonrpc"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	mcppkg "mcp_proxy/pkg/mcp"
)

var _ = Describe("shouldReportToSentry", func() {
	It("should return false for nil error", func() {
		Expect(mcppkg.ShouldReportToSentryForTest(nil)).To(BeFalse())
	})

	It("should return true for generic error", func() {
		err := errors.New("some internal error")
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeTrue())
	})

	It("should return false for parse_error (-32700)", func() {
		err := &jsonrpc.Error{Code: -32700, Message: "parse error"}
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeFalse())
	})

	It("should return false for invalid_request (-32600)", func() {
		err := &jsonrpc.Error{Code: -32600, Message: "invalid request"}
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeFalse())
	})

	It("should return false for method_not_found (-32601)", func() {
		err := &jsonrpc.Error{Code: jsonrpc.CodeMethodNotFound, Message: "method not found"}
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeFalse())
	})

	It("should return false for invalid_params (-32602)", func() {
		err := &jsonrpc.Error{Code: -32602, Message: "invalid params"}
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeFalse())
	})

	It("should return true for internal_error (-32603)", func() {
		err := &jsonrpc.Error{Code: -32603, Message: "internal error"}
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeTrue())
	})

	It("should return true for unknown jsonrpc error codes", func() {
		err := &jsonrpc.Error{Code: -32000, Message: "server error"}
		Expect(mcppkg.ShouldReportToSentryForTest(err)).To(BeTrue())
	})

	It("should return false for wrapped client error", func() {
		innerErr := &jsonrpc.Error{Code: -32600, Message: "invalid request"}
		wrappedErr := fmt.Errorf("handler failed: %w", innerErr)
		Expect(mcppkg.ShouldReportToSentryForTest(wrappedErr)).To(BeFalse())
	})

	It("should return true for wrapped server error", func() {
		innerErr := &jsonrpc.Error{Code: -32603, Message: "internal error"}
		wrappedErr := fmt.Errorf("handler failed: %w", innerErr)
		Expect(mcppkg.ShouldReportToSentryForTest(wrappedErr)).To(BeTrue())
	})
})
