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

package entity

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

var _ = Describe("Format", func() {
	Describe("mapKV2Node", func() {
		Context("Normal case - with port", func() {
			It("should correctly parse address and port", func() {
				node, err := mapKV2Node("127.0.0.1:8080", 10)
				Expect(err).NotTo(HaveOccurred())
				Expect(node).To(Equal(&Node{Host: "127.0.0.1", Port: 8080, Weight: 10}))
			})
		})

		Context("Normal case - IPv6 address", func() {
			It("should correctly parse IPv6 address and port", func() {
				node, err := mapKV2Node("[2001:db8::1]:8080", 20)
				Expect(err).NotTo(HaveOccurred())
				Expect(node).To(Equal(&Node{Host: "[2001:db8::1]", Port: 8080, Weight: 20}))
			})
		})

		Context("Normal case - missing port", func() {
			It("should use default port 0", func() {
				node, err := mapKV2Node("127.0.0.1", 30)
				Expect(err).NotTo(HaveOccurred())
				Expect(node).To(Equal(&Node{Host: "127.0.0.1", Port: 0, Weight: 30}))
			})
		})

		Context("Error case - invalid port", func() {
			It("should return an error", func() {
				node, err := mapKV2Node("127.0.0.1:xxx", 40)
				Expect(err).To(HaveOccurred())
				Expect(node).To(BeNil())
			})
		})

		Context("Error case - invalid address", func() {
			It("should return an error", func() {
				node, err := mapKV2Node("invalid:address", 40)
				Expect(err).To(HaveOccurred())
				Expect(node).To(BeNil())
			})
		})

		Context("Error case - invalid host port format", func() {
			It("should return an error when host:port format is invalid", func() {
				node, err := mapKV2Node("host:port:extra", 50)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(Equal("invalid upstream node"))
				Expect(node).To(BeNil())
			})
		})
	})

	Describe("NodesFormat", func() {
		Context("map[string]float64 type", func() {
			It("should correctly convert to Node list", func() {
				input := map[string]float64{
					"127.0.0.1:8080": 10,
					"192.168.1.1":    20,
				}
				expected := []*Node{
					{Host: "127.0.0.1", Port: 8080, Weight: 10},
					{Host: "192.168.1.1", Port: 0, Weight: 20},
				}
				result := NodesFormat(input)
				Expect(result).To(ConsistOf(expected))
			})
		})

		Context("map[string]interface{} type", func() {
			It("should correctly convert to Node list", func() {
				input := map[string]any{
					"127.0.0.1:8080": float64(10),
					"192.168.1.1":    float64(20),
				}
				expected := []*Node{
					{Host: "127.0.0.1", Port: 8080, Weight: 10},
					{Host: "192.168.1.1", Port: 0, Weight: 20},
				}
				result := NodesFormat(input)
				Expect(result).To(ConsistOf(expected))
			})
		})

		Context("[]*Node type", func() {
			It("should return the original data", func() {
				input := []*Node{
					{Host: "127.0.0.1", Port: 8080, Weight: 10},
					{Host: "192.168.1.1", Port: 0, Weight: 20},
				}
				result := NodesFormat(input)
				Expect(result).To(Equal(input))
			})
		})

		Context("[]interface{} type", func() {
			It("should correctly convert to Node list", func() {
				input := []any{
					map[string]any{
						"host":     "127.0.0.1",
						"port":     float64(8080),
						"weight":   float64(10),
						"priority": float64(0),
					},
					map[string]any{
						"host":   "192.168.1.1",
						"port":   float64(0),
						"weight": float64(20),
						"metadata": map[string]any{
							"key": "value",
						},
					},
				}
				expected := []*Node{
					{Host: "127.0.0.1", Port: 8080, Weight: 10, Priority: 0},
					{
						Host:     "192.168.1.1",
						Port:     0,
						Weight:   20,
						Metadata: map[string]any{"key": "value"},
					},
				}
				result := NodesFormat(input)
				Expect(result).To(Equal(expected))
			})
		})

		Context("Other types", func() {
			It("should return the original data", func() {
				input := "invalid_type"
				result := NodesFormat(input)
				Expect(result).To(Equal(input))
			})
		})
	})
})
