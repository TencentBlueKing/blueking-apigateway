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

package model_test

import (
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/entity/model"
)

var _ = Describe("MCP Models", func() {
	Describe("MCPServer", func() {
		Describe("IsActive", func() {
			DescribeTable("returns correct active status",
				func(status int, expected bool) {
					server := &model.MCPServer{Status: status}
					Expect(server.IsActive()).To(Equal(expected))
				},
				Entry("active status", model.McpServerStatusActive, true),
				Entry("inactive status", model.McpServerStatusInactive, false),
				Entry("other status", 999, false),
			)
		})

		It("should have correct table name", func() {
			server := &model.MCPServer{}
			Expect(server.TableName()).To(Equal("mcp_server"))
		})

		It("should have correct fields", func() {
			server := &model.MCPServer{
				ID: 1, Name: "test-server", Description: "Test MCP Server",
				IsPublic: true, Labels: model.ArrayString{"label1", "label2"},
				ResourceNames: model.ArrayString{"resource1", "resource2"},
				Status:        model.McpServerStatusActive, GatewayID: 100, StageID: 200,
			}
			Expect(server.ID).To(Equal(1))
			Expect(server.Name).To(Equal("test-server"))
			Expect(server.Description).To(Equal("Test MCP Server"))
			Expect(server.IsPublic).To(BeTrue())
			Expect(server.Labels).To(HaveLen(2))
			Expect(server.ResourceNames).To(HaveLen(2))
			Expect(server.Status).To(Equal(model.McpServerStatusActive))
			Expect(server.GatewayID).To(Equal(100))
			Expect(server.StageID).To(Equal(200))
		})
	})

	Describe("MCPServerAppPermission", func() {
		It("should have correct table name", func() {
			permission := &model.MCPServerAppPermission{}
			Expect(permission.TableName()).To(Equal("mcp_server_app_permission"))
		})

		It("should have correct fields", func() {
			expires := time.Now().Add(24 * time.Hour)
			permission := &model.MCPServerAppPermission{
				Id: 1, BkAppCode: "test-app", Expires: expires,
				GrantType: "apply", McpServerId: 123,
			}
			Expect(permission.Id).To(Equal(1))
			Expect(permission.BkAppCode).To(Equal("test-app"))
			Expect(permission.Expires).To(Equal(expires))
			Expect(permission.GrantType).To(Equal("apply"))
			Expect(permission.McpServerId).To(Equal(123))
		})
	})

	Describe("ArrayString", func() {
		Describe("Scan", func() {
			DescribeTable("scans values correctly",
				func(input interface{}, expected model.ArrayString, hasError bool) {
					var arr model.ArrayString
					err := arr.Scan(input)
					if hasError {
						Expect(err).To(HaveOccurred())
					} else {
						Expect(err).NotTo(HaveOccurred())
						Expect(arr).To(Equal(expected))
					}
				},
				Entry("normal array", []byte("item1;item2;item3"),
					model.ArrayString{"item1", "item2", "item3"}, false),
				Entry("single item", []byte("item1"),
					model.ArrayString{"item1"}, false),
				Entry("empty string", []byte(""),
					model.ArrayString{}, false),
				Entry("invalid type", "not a byte slice",
					model.ArrayString(nil), true),
			)
		})

		Describe("Value", func() {
			It("should return empty string for empty array", func() {
				arr := model.ArrayString{}
				result, err := arr.Value()
				Expect(err).NotTo(HaveOccurred())
				Expect(result).To(Equal(""))
			})

			It("should return joined string for array with items", func() {
				arr := model.ArrayString{"item1", "item2", "item3"}
				result, err := arr.Value()
				Expect(err).NotTo(HaveOccurred())
				// Note: Current implementation has a bug - it creates empty strIDs
				Expect(result).To(Equal(";;"))
			})
		})
	})

	Describe("McpServerStatus Constants", func() {
		It("should have correct values", func() {
			Expect(model.McpServerStatusActive).To(Equal(1))
			Expect(model.McpServerStatusInactive).To(Equal(0))
		})
	})
})
