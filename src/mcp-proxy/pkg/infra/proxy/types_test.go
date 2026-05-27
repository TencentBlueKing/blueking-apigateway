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

package proxy_test

import (
	"encoding/json"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/infra/proxy"
)

var _ = Describe("Types", func() {
	Describe("HandlerRequest", func() {
		Describe("JSON Marshal", func() {
			It("should marshal and unmarshal correctly", func() {
				request := proxy.HandlerRequest{
					HeaderParam: proxy.StringParamMap{"Content-Type": "application/json"},
					QueryParam:  proxy.StringParamMap{"limit": "10", "offset": "0"},
					PathParam:   proxy.StringParamMap{"id": "123"},
					BodyParam:   map[string]any{"name": "test"},
				}

				data, err := json.Marshal(request)
				Expect(err).NotTo(HaveOccurred())
				Expect(data).NotTo(BeEmpty())

				var result proxy.HandlerRequest
				err = json.Unmarshal(data, &result)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.HeaderParam["Content-Type"]).To(Equal("application/json"))
				Expect(result.QueryParam["limit"]).To(Equal("10"))
				Expect(result.PathParam["id"]).To(Equal("123"))
				Expect(result.BodyParam.(map[string]any)["name"]).To(Equal("test"))
			})

			It("should handle empty fields", func() {
				request := proxy.HandlerRequest{}
				data, err := json.Marshal(request)
				Expect(err).NotTo(HaveOccurred())
				Expect(string(data)).To(Equal("{}"))
			})

			It("should handle partial fields", func() {
				request := proxy.HandlerRequest{
					QueryParam: proxy.StringParamMap{"search": "test"},
				}

				data, err := json.Marshal(request)
				Expect(err).NotTo(HaveOccurred())

				var result map[string]any
				err = json.Unmarshal(data, &result)
				Expect(err).NotTo(HaveOccurred())
				Expect(result).To(HaveKey("query_param"))
				Expect(result).NotTo(HaveKey("header_param"))
				Expect(result).NotTo(HaveKey("path_param"))
				Expect(result).NotTo(HaveKey("body_param"))
			})

			It("should handle complex body param", func() {
				request := proxy.HandlerRequest{
					BodyParam: map[string]any{
						"user": map[string]any{
							"name":  "John",
							"email": "john@example.com",
							"roles": []string{"admin", "user"},
						},
					},
				}

				data, err := json.Marshal(request)
				Expect(err).NotTo(HaveOccurred())

				var result proxy.HandlerRequest
				err = json.Unmarshal(data, &result)
				Expect(err).NotTo(HaveOccurred())

				body := result.BodyParam.(map[string]any)
				user := body["user"].(map[string]any)
				Expect(user["name"]).To(Equal("John"))
				Expect(user["email"]).To(Equal("john@example.com"))
			})

			It("should unmarshal from JSON string", func() {
				jsonStr := `{
					"header_param": {"Authorization": "Bearer token"},
					"query_param": {"page": 1},
					"path_param": {"userId": "abc123"},
					"body_param": {"data": "test"}
				}`

				var request proxy.HandlerRequest
				err := json.Unmarshal([]byte(jsonStr), &request)
				Expect(err).NotTo(HaveOccurred())

				Expect(request.HeaderParam["Authorization"]).To(Equal("Bearer token"))
				Expect(request.QueryParam["page"]).To(Equal("1"))
				Expect(request.PathParam["userId"]).To(Equal("abc123"))
				Expect(request.BodyParam.(map[string]any)["data"]).To(Equal("test"))
			})
		})
	})

	Describe("StringParamMap", func() {
		Describe("UnmarshalJSON", func() {
			It("should convert large integers to decimal strings without scientific notation", func() {
				jsonStr := `{"bk_biz_id": 2005000002, "trace_id": 9007199254740992}`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m["bk_biz_id"]).To(Equal("2005000002"))
				Expect(m["trace_id"]).To(Equal("9007199254740992"))
			})

			It("should preserve decimal numbers", func() {
				jsonStr := `{"ratio": 3.14, "rate": 0.001}`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m["ratio"]).To(Equal("3.14"))
				Expect(m["rate"]).To(Equal("0.001"))
			})

			It("should handle string values as-is", func() {
				jsonStr := `{"name": "hello", "empty": ""}`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m["name"]).To(Equal("hello"))
				Expect(m["empty"]).To(Equal(""))
			})

			It("should handle boolean values", func() {
				jsonStr := `{"verbose": true, "quiet": false}`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m["verbose"]).To(Equal("true"))
				Expect(m["quiet"]).To(Equal("false"))
			})

			It("should handle null input", func() {
				jsonStr := `null`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m).To(BeNil())
			})

			It("should handle zero and negative numbers", func() {
				jsonStr := `{"zero": 0, "negative": -100, "neg_float": -1.5}`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m["zero"]).To(Equal("0"))
				Expect(m["negative"]).To(Equal("-100"))
				Expect(m["neg_float"]).To(Equal("-1.5"))
			})

			It("should handle mixed value types", func() {
				jsonStr := `{"id": 2005000002, "name": "test", "active": true, "score": 99.5}`
				var m proxy.StringParamMap
				err := json.Unmarshal([]byte(jsonStr), &m)
				Expect(err).NotTo(HaveOccurred())
				Expect(m["id"]).To(Equal("2005000002"))
				Expect(m["name"]).To(Equal("test"))
				Expect(m["active"]).To(Equal("true"))
				Expect(m["score"]).To(Equal("99.5"))
			})
		})
	})
})
