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

package proxy

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("Helper Functions", func() {
	Describe("buildToolResponseEnvelope", func() {
		It("should include all fields when body is provided", func() {
			envelope := buildToolResponseEnvelope(200, "req-1", "trace-1", "body-content")

			Expect(envelope[toolResponseStatusCodeField]).To(Equal(200))
			Expect(envelope[toolResponseRequestIDField]).To(Equal("req-1"))
			Expect(envelope[toolResponseTraceIDField]).To(Equal("trace-1"))
			Expect(envelope[toolResponseBodyField]).To(Equal("body-content"))
		})

		It("should include response_body as nil when body is nil", func() {
			envelope := buildToolResponseEnvelope(204, "req-1", "trace-1", nil)

			Expect(envelope).To(HaveLen(4))
			Expect(envelope).To(HaveKey(toolResponseBodyField))
			Expect(envelope[toolResponseBodyField]).To(BeNil())
		})

		It("should handle zero status code", func() {
			envelope := buildToolResponseEnvelope(0, "", "", nil)

			Expect(envelope[toolResponseStatusCodeField]).To(Equal(0))
			Expect(envelope[toolResponseRequestIDField]).To(Equal(""))
			Expect(envelope[toolResponseTraceIDField]).To(Equal(""))
		})
	})

	Describe("buildToolInputSchema", func() {
		It("should return default schema for nil ParamSchema", func() {
			toolConfig := &ToolConfig{
				Name: "test-tool",
			}
			schema := buildToolInputSchema(toolConfig, "test-server")
			Expect(schema).To(HaveKeyWithValue("type", "object"))
			Expect(schema).To(HaveKey("properties"))
		})
	})
})
