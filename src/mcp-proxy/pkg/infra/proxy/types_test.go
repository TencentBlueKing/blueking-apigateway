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
					HeaderParam: map[string]any{"Content-Type": "application/json"},
					QueryParam:  map[string]any{"limit": 10, "offset": 0},
					PathParam:   map[string]any{"id": "123"},
					BodyParam:   map[string]any{"name": "test"},
				}

				data, err := json.Marshal(request)
				Expect(err).NotTo(HaveOccurred())
				Expect(data).NotTo(BeEmpty())

				var result proxy.HandlerRequest
				err = json.Unmarshal(data, &result)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.HeaderParam["Content-Type"]).To(Equal("application/json"))
				Expect(result.QueryParam["limit"]).To(Equal(float64(10)))
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
					QueryParam: map[string]any{"search": "test"},
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
				Expect(request.QueryParam["page"]).To(Equal(float64(1)))
				Expect(request.PathParam["userId"]).To(Equal("abc123"))
				Expect(request.BodyParam.(map[string]any)["data"]).To(Equal("test"))
			})
		})
	})
})
