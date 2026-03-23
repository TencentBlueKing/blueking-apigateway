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
	"strings"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/constant"
)

var _ = Describe("Helper Functions", func() {
	Describe("truncateJSON", func() {
		It("should return empty string for nil input", func() {
			Expect(truncateJSON(nil, 100)).To(Equal(""))
		})

		It("should return full JSON for short input", func() {
			result := truncateJSON(map[string]string{"key": "value"}, 100)
			Expect(result).To(Equal(`{"key":"value"}`))
		})

		It("should truncate long JSON", func() {
			longValue := strings.Repeat("a", 100)
			result := truncateJSON(map[string]string{"key": longValue}, 20)
			Expect(result).To(HaveLen(20 + len("...(truncated)")))
			Expect(result).To(HaveSuffix("...(truncated)"))
		})

		It("should handle non-marshalable input gracefully", func() {
			result := truncateJSON(make(chan int), 100)
			Expect(result).To(ContainSubstring("marshal error"))
		})

		It("should handle exact length input without truncation", func() {
			result := truncateJSON("abc", 5) // "abc" marshals to `"abc"` (5 chars)
			Expect(result).To(Equal(`"abc"`))
			Expect(result).NotTo(ContainSubstring("truncated"))
		})

		It("should handle empty string", func() {
			result := truncateJSON("", 100)
			Expect(result).To(Equal(`""`))
		})

		It("should handle integer input", func() {
			result := truncateJSON(12345, 100)
			Expect(result).To(Equal("12345"))
		})

		It("should handle array input", func() {
			result := truncateJSON([]int{1, 2, 3}, 100)
			Expect(result).To(Equal("[1,2,3]"))
		})
	})

	Describe("maskSensitiveHeaders", func() {
		It("should mask BkApiAuthorization header", func() {
			headers := map[string]string{
				constant.BkApiAuthorizationHeaderKey: "abcdefghijk",
				"Content-Type":                       "application/json",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(masked[constant.BkApiAuthorizationHeaderKey]).To(Equal("abc***ijk"))
			Expect(masked["Content-Type"]).To(Equal("application/json"))
		})

		It("should mask BkGatewayJWT header", func() {
			headers := map[string]string{
				constant.BkGatewayJWTHeaderKey: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(masked[constant.BkGatewayJWTHeaderKey]).To(Equal("eyJ***CJ9"))
		})

		It("should mask short sensitive headers with ***", func() {
			headers := map[string]string{
				constant.BkApiAuthorizationHeaderKey: "short",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(masked[constant.BkApiAuthorizationHeaderKey]).To(Equal("***"))
		})

		It("should handle exactly 6-char sensitive value", func() {
			headers := map[string]string{
				constant.BkApiAuthorizationHeaderKey: "abcdef",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(masked[constant.BkApiAuthorizationHeaderKey]).To(Equal("***"))
		})

		It("should handle 7-char sensitive value", func() {
			headers := map[string]string{
				constant.BkApiAuthorizationHeaderKey: "abcdefg",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(masked[constant.BkApiAuthorizationHeaderKey]).To(Equal("abc***efg"))
		})

		It("should not modify non-sensitive headers", func() {
			headers := map[string]string{
				"Content-Type": "application/json",
				"Accept":       "text/html",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(masked["Content-Type"]).To(Equal("application/json"))
			Expect(masked["Accept"]).To(Equal("text/html"))
		})

		It("should handle empty headers map", func() {
			masked := maskSensitiveHeaders(map[string]string{})
			Expect(masked).To(BeEmpty())
		})

		It("should return a new map (not modify original)", func() {
			headers := map[string]string{
				constant.BkApiAuthorizationHeaderKey: "original_value",
			}
			masked := maskSensitiveHeaders(headers)

			Expect(headers[constant.BkApiAuthorizationHeaderKey]).To(Equal("original_value"))
			Expect(masked[constant.BkApiAuthorizationHeaderKey]).NotTo(Equal("original_value"))
		})
	})

	Describe("hasObjectSchemaType", func() {
		It("should return true for string 'object'", func() {
			Expect(hasObjectSchemaType("object")).To(BeTrue())
		})

		It("should return false for string 'array'", func() {
			Expect(hasObjectSchemaType("array")).To(BeFalse())
		})

		It("should return true for []string containing 'object'", func() {
			Expect(hasObjectSchemaType([]string{"object", "null"})).To(BeTrue())
		})

		It("should return false for []string without 'object'", func() {
			Expect(hasObjectSchemaType([]string{"string", "null"})).To(BeFalse())
		})

		It("should return true for []any containing 'object'", func() {
			Expect(hasObjectSchemaType([]any{"object", "null"})).To(BeTrue())
		})

		It("should return false for []any without 'object'", func() {
			Expect(hasObjectSchemaType([]any{"string", 123})).To(BeFalse())
		})

		It("should return false for nil", func() {
			Expect(hasObjectSchemaType(nil)).To(BeFalse())
		})

		It("should return false for unexpected type (int)", func() {
			Expect(hasObjectSchemaType(42)).To(BeFalse())
		})
	})

	Describe("normalizeToolOutputSchema", func() {
		It("should add 'type' when missing but 'properties' exists", func() {
			schema := map[string]any{
				"properties": map[string]any{"name": map[string]any{"type": "string"}},
			}
			result := normalizeToolOutputSchema(schema)
			Expect(result["type"]).To(Equal("object"))
		})

		It("should add 'properties' when type is 'object' but properties missing", func() {
			schema := map[string]any{
				"type": "object",
			}
			result := normalizeToolOutputSchema(schema)
			Expect(result["properties"]).To(Equal(map[string]any{}))
		})

		It("should not modify schema when both type and properties exist", func() {
			schema := map[string]any{
				"type":       "object",
				"properties": map[string]any{"name": map[string]any{"type": "string"}},
			}
			result := normalizeToolOutputSchema(schema)
			Expect(result["type"]).To(Equal("object"))
			Expect(result["properties"]).NotTo(BeNil())
		})

		It("should not modify array schema", func() {
			schema := map[string]any{
				"type":  "array",
				"items": map[string]any{"type": "string"},
			}
			result := normalizeToolOutputSchema(schema)
			Expect(result["type"]).To(Equal("array"))
			Expect(result).NotTo(HaveKey("properties"))
		})

		It("should handle schema with only type and no properties", func() {
			schema := map[string]any{
				"type": "string",
			}
			result := normalizeToolOutputSchema(schema)
			Expect(result["type"]).To(Equal("string"))
			Expect(result).NotTo(HaveKey("properties"))
		})
	})

	Describe("buildToolResponseEnvelope", func() {
		It("should include all fields when body is provided", func() {
			envelope := buildToolResponseEnvelope(200, "req-1", "trace-1", "body-content")

			Expect(envelope[toolResponseStatusCodeField]).To(Equal(200))
			Expect(envelope[toolResponseRequestIDField]).To(Equal("req-1"))
			Expect(envelope[toolResponseTraceIDField]).To(Equal("trace-1"))
			Expect(envelope[toolResponseBodyField]).To(Equal("body-content"))
		})

		It("should omit response_body when body is nil", func() {
			envelope := buildToolResponseEnvelope(204, "req-1", "trace-1", nil)

			Expect(envelope).To(HaveLen(3))
			Expect(envelope).NotTo(HaveKey(toolResponseBodyField))
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
