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
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/infra/proxy"
)

var _ = Describe("Config", func() {
	Describe("ToolConfig", func() {
		Describe("String", func() {
			DescribeTable("formats correctly",
				func(config proxy.ToolConfig, expected string) {
					Expect(config.String()).To(Equal(expected))
				},
				Entry("basic config",
					proxy.ToolConfig{
						Name: "getUsers", Host: "api.example.com",
						BasePath: "/v1", Url: "/users", Method: "GET",
					},
					"tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
				),
				Entry("host with trailing slash",
					proxy.ToolConfig{
						Name: "getUsers", Host: "api.example.com/",
						BasePath: "/v1", Url: "/users", Method: "GET",
					},
					"tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
				),
				Entry("base path with leading and trailing slashes",
					proxy.ToolConfig{
						Name: "getUsers", Host: "api.example.com",
						BasePath: "/v1/", Url: "/users", Method: "GET",
					},
					"tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
				),
				Entry("url without leading slash",
					proxy.ToolConfig{
						Name: "getUsers", Host: "api.example.com",
						BasePath: "/v1", Url: "users", Method: "GET",
					},
					"tool:[name:getUsers,url:api.example.com/v1/users, method:GET]",
				),
				Entry("POST method",
					proxy.ToolConfig{
						Name: "createUser", Host: "api.example.com",
						BasePath: "/v1", Url: "/users", Method: "POST",
					},
					"tool:[name:createUser,url:api.example.com/v1/users, method:POST]",
				),
				Entry("empty base path",
					proxy.ToolConfig{
						Name: "getUsers", Host: "api.example.com",
						BasePath: "", Url: "/users", Method: "GET",
					},
					"tool:[name:getUsers,url:api.example.com/users, method:GET]",
				),
			)
		})
	})

	Describe("MCPServerConfig", func() {
		It("should have correct fields", func() {
			config := proxy.MCPServerConfig{
				Name:              "test-server",
				ResourceVersionID: 123,
				Tools: []*proxy.ToolConfig{
					{
						Name: "tool1", Description: "Test tool 1",
						Method: "GET", Host: "api.example.com",
						BasePath: "/v1", Url: "/test",
					},
				},
			}

			Expect(config.Name).To(Equal("test-server"))
			Expect(config.ResourceVersionID).To(Equal(123))
			Expect(config.Tools).To(HaveLen(1))
			Expect(config.Tools[0].Name).To(Equal("tool1"))
		})
	})

	Describe("PromptConfig", func() {
		It("should have correct fields", func() {
			config := proxy.PromptConfig{
				Name:        "test-prompt",
				Description: "This is a test prompt",
				Content:     "Hello, this is the prompt content",
			}

			Expect(config.Name).To(Equal("test-prompt"))
			Expect(config.Description).To(Equal("This is a test prompt"))
			Expect(config.Content).To(Equal("Hello, this is the prompt content"))
		})

		It("should handle empty fields", func() {
			config := proxy.PromptConfig{}

			Expect(config.Name).To(BeEmpty())
			Expect(config.Description).To(BeEmpty())
			Expect(config.Content).To(BeEmpty())
		})
	})
})
