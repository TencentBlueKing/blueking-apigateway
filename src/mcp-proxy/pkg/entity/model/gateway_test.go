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
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/entity/model"
)

var _ = Describe("Gateway Models", func() {
	Describe("Gateway", func() {
		It("should have correct table name", func() {
			gateway := model.Gateway{}
			Expect(gateway.TableName()).To(Equal("core_api"))
		})

		It("should have correct fields", func() {
			gateway := model.Gateway{ID: 1, Name: "test-gateway"}
			Expect(gateway.ID).To(Equal(1))
			Expect(gateway.Name).To(Equal("test-gateway"))
		})
	})

	Describe("Stage", func() {
		It("should have correct table name", func() {
			stage := model.Stage{}
			Expect(stage.TableName()).To(Equal("core_stage"))
		})

		It("should have correct fields", func() {
			stage := model.Stage{ID: 1, Name: "prod"}
			Expect(stage.ID).To(Equal(1))
			Expect(stage.Name).To(Equal("prod"))
		})
	})

	Describe("JWT", func() {
		It("should have correct table name", func() {
			jwt := model.JWT{}
			Expect(jwt.TableName()).To(Equal("core_jwt"))
		})

		It("should have correct fields", func() {
			jwt := model.JWT{
				GatewayID:           1,
				PrivateKey:          "private-key-content",
				PublicKey:           "public-key-content",
				EncryptedPrivateKey: "encrypted-private-key",
			}
			Expect(jwt.GatewayID).To(Equal(1))
			Expect(jwt.PrivateKey).To(Equal("private-key-content"))
			Expect(jwt.PublicKey).To(Equal("public-key-content"))
			Expect(jwt.EncryptedPrivateKey).To(Equal("encrypted-private-key"))
		})
	})

	Describe("Release", func() {
		It("should have correct table name", func() {
			release := model.Release{}
			Expect(release.TableName()).To(Equal("core_release"))
		})

		It("should have correct fields", func() {
			release := model.Release{
				ID: 1, GatewayID: 100, ResourceVersionID: 200, StageID: 300,
			}
			Expect(release.ID).To(Equal(1))
			Expect(release.GatewayID).To(Equal(100))
			Expect(release.ResourceVersionID).To(Equal(200))
			Expect(release.StageID).To(Equal(300))
		})
	})

	Describe("ReleasedResource", func() {
		It("should have correct table name", func() {
			resource := model.ReleasedResource{}
			Expect(resource.TableName()).To(Equal("core_released_resource"))
		})

		It("should have correct fields", func() {
			resource := model.ReleasedResource{
				ID: 1, ResourceVersionID: 100, ResourceID: 200,
				ResourceName: "get_users", ResourceMethod: "GET",
				ResourcePath: "/users", GatewayID: 300, Data: `{"key": "value"}`,
			}
			Expect(resource.ID).To(Equal(1))
			Expect(resource.ResourceVersionID).To(Equal(100))
			Expect(resource.ResourceID).To(Equal(200))
			Expect(resource.ResourceName).To(Equal("get_users"))
			Expect(resource.ResourceMethod).To(Equal("GET"))
			Expect(resource.ResourcePath).To(Equal("/users"))
			Expect(resource.GatewayID).To(Equal(300))
			Expect(resource.Data).To(Equal(`{"key": "value"}`))
		})
	})

	Describe("Resource", func() {
		It("should have correct table name", func() {
			resource := model.Resource{}
			Expect(resource.TableName()).To(Equal("core_resource"))
		})

		It("should have correct fields", func() {
			resource := model.Resource{
				ID: 1, Name: "get_users", Description: "Get all users",
				Method: "GET", Path: "/users", ProxyID: 100,
				IsPublic: true, GatewayID: 200, MatchSubpath: false,
				AllowApplyPermission: true, DescriptionEn: "Get all users (EN)",
				EnableWebsocket: false,
			}
			Expect(resource.ID).To(Equal(1))
			Expect(resource.Name).To(Equal("get_users"))
			Expect(resource.Description).To(Equal("Get all users"))
			Expect(resource.Method).To(Equal("GET"))
			Expect(resource.Path).To(Equal("/users"))
			Expect(resource.ProxyID).To(Equal(100))
			Expect(resource.IsPublic).To(BeTrue())
			Expect(resource.GatewayID).To(Equal(200))
			Expect(resource.MatchSubpath).To(BeFalse())
			Expect(resource.AllowApplyPermission).To(BeTrue())
			Expect(resource.DescriptionEn).To(Equal("Get all users (EN)"))
			Expect(resource.EnableWebsocket).To(BeFalse())
		})
	})

	Describe("ResourceVersion", func() {
		It("should have correct table name", func() {
			version := model.ResourceVersion{}
			Expect(version.TableName()).To(Equal("core_resource_version"))
		})

		It("should have correct fields", func() {
			version := model.ResourceVersion{
				ID: 1, Data: `{"resources": []}`, GatewayID: 100,
				Version: "v1.0.0", SchemaVersion: "1.0",
			}
			Expect(version.ID).To(Equal(1))
			Expect(version.Data).To(Equal(`{"resources": []}`))
			Expect(version.GatewayID).To(Equal(int64(100)))
			Expect(version.Version).To(Equal("v1.0.0"))
			Expect(version.SchemaVersion).To(Equal("1.0"))
		})
	})

	Describe("OpenapiGatewayResourceVersionSpec", func() {
		It("should have correct table name", func() {
			spec := model.OpenapiGatewayResourceVersionSpec{}
			Expect(spec.TableName()).To(Equal("openapi_gateway_resource_version_spec"))
		})

		It("should have correct fields", func() {
			spec := model.OpenapiGatewayResourceVersionSpec{
				ID: 1, Schema: `{"openapi": "3.0.0"}`,
				GatewayID: 100, ResourceVersionID: 200,
			}
			Expect(spec.ID).To(Equal(1))
			Expect(spec.Schema).To(Equal(`{"openapi": "3.0.0"}`))
			Expect(spec.GatewayID).To(Equal(100))
			Expect(spec.ResourceVersionID).To(Equal(200))
		})
	})
})
