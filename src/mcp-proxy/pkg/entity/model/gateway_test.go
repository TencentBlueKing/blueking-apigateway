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

package model

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGateway_TableName(t *testing.T) {
	gateway := Gateway{}
	assert.Equal(t, "core_api", gateway.TableName())
}

func TestGateway_Fields(t *testing.T) {
	gateway := Gateway{
		ID:   1,
		Name: "test-gateway",
	}

	assert.Equal(t, 1, gateway.ID)
	assert.Equal(t, "test-gateway", gateway.Name)
}

func TestStage_TableName(t *testing.T) {
	stage := Stage{}
	assert.Equal(t, "core_stage", stage.TableName())
}

func TestStage_Fields(t *testing.T) {
	stage := Stage{
		ID:   1,
		Name: "prod",
	}

	assert.Equal(t, 1, stage.ID)
	assert.Equal(t, "prod", stage.Name)
}

func TestJWT_TableName(t *testing.T) {
	jwt := JWT{}
	assert.Equal(t, "core_jwt", jwt.TableName())
}

func TestJWT_Fields(t *testing.T) {
	jwt := JWT{
		GatewayID:           1,
		PrivateKey:          "private-key-content",
		PublicKey:           "public-key-content",
		EncryptedPrivateKey: "encrypted-private-key",
	}

	assert.Equal(t, 1, jwt.GatewayID)
	assert.Equal(t, "private-key-content", jwt.PrivateKey)
	assert.Equal(t, "public-key-content", jwt.PublicKey)
	assert.Equal(t, "encrypted-private-key", jwt.EncryptedPrivateKey)
}

func TestRelease_TableName(t *testing.T) {
	release := Release{}
	assert.Equal(t, "core_release", release.TableName())
}

func TestRelease_Fields(t *testing.T) {
	release := Release{
		ID:                1,
		GatewayID:         100,
		ResourceVersionID: 200,
		StageID:           300,
	}

	assert.Equal(t, 1, release.ID)
	assert.Equal(t, 100, release.GatewayID)
	assert.Equal(t, 200, release.ResourceVersionID)
	assert.Equal(t, 300, release.StageID)
}

func TestReleasedResource_TableName(t *testing.T) {
	resource := ReleasedResource{}
	assert.Equal(t, "core_released_resource", resource.TableName())
}

func TestReleasedResource_Fields(t *testing.T) {
	resource := ReleasedResource{
		ID:                1,
		ResourceVersionID: 100,
		ResourceID:        200,
		ResourceName:      "get_users",
		ResourceMethod:    "GET",
		ResourcePath:      "/users",
		GatewayID:         300,
		Data:              `{"key": "value"}`,
	}

	assert.Equal(t, 1, resource.ID)
	assert.Equal(t, 100, resource.ResourceVersionID)
	assert.Equal(t, 200, resource.ResourceID)
	assert.Equal(t, "get_users", resource.ResourceName)
	assert.Equal(t, "GET", resource.ResourceMethod)
	assert.Equal(t, "/users", resource.ResourcePath)
	assert.Equal(t, 300, resource.GatewayID)
	assert.Equal(t, `{"key": "value"}`, resource.Data)
}

func TestResource_TableName(t *testing.T) {
	resource := Resource{}
	assert.Equal(t, "core_resource", resource.TableName())
}

func TestResource_Fields(t *testing.T) {
	resource := Resource{
		ID:                   1,
		Name:                 "get_users",
		Description:          "Get all users",
		Method:               "GET",
		Path:                 "/users",
		ProxyID:              100,
		IsPublic:             true,
		GatewayID:            200,
		MatchSubpath:         false,
		AllowApplyPermission: true,
		DescriptionEn:        "Get all users (EN)",
		EnableWebsocket:      false,
	}

	assert.Equal(t, 1, resource.ID)
	assert.Equal(t, "get_users", resource.Name)
	assert.Equal(t, "Get all users", resource.Description)
	assert.Equal(t, "GET", resource.Method)
	assert.Equal(t, "/users", resource.Path)
	assert.Equal(t, 100, resource.ProxyID)
	assert.True(t, resource.IsPublic)
	assert.Equal(t, 200, resource.GatewayID)
	assert.False(t, resource.MatchSubpath)
	assert.True(t, resource.AllowApplyPermission)
	assert.Equal(t, "Get all users (EN)", resource.DescriptionEn)
	assert.False(t, resource.EnableWebsocket)
}

func TestResourceVersion_TableName(t *testing.T) {
	version := ResourceVersion{}
	assert.Equal(t, "core_resource_version", version.TableName())
}

func TestResourceVersion_Fields(t *testing.T) {
	version := ResourceVersion{
		ID:            1,
		Data:          `{"resources": []}`,
		GatewayID:     100,
		Version:       "v1.0.0",
		SchemaVersion: "1.0",
	}

	assert.Equal(t, 1, version.ID)
	assert.Equal(t, `{"resources": []}`, version.Data)
	assert.Equal(t, int64(100), version.GatewayID)
	assert.Equal(t, "v1.0.0", version.Version)
	assert.Equal(t, "1.0", version.SchemaVersion)
}

func TestOpenapiGatewayResourceVersionSpec_TableName(t *testing.T) {
	spec := OpenapiGatewayResourceVersionSpec{}
	assert.Equal(t, "openapi_gateway_resource_version_spec", spec.TableName())
}

func TestOpenapiGatewayResourceVersionSpec_Fields(t *testing.T) {
	spec := OpenapiGatewayResourceVersionSpec{
		ID:                1,
		Schema:            `{"openapi": "3.0.0"}`,
		GatewayID:         100,
		ResourceVersionID: 200,
	}

	assert.Equal(t, 1, spec.ID)
	assert.Equal(t, `{"openapi": "3.0.0"}`, spec.Schema)
	assert.Equal(t, 100, spec.GatewayID)
	assert.Equal(t, 200, spec.ResourceVersionID)
}
