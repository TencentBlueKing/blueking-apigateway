/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

package schema

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"

	"operator/pkg/constant"
)

func TestGetResourceSchema(t *testing.T) {
	tests := []struct {
		name       string
		version    constant.APISIXVersion
		shouldFail bool
	}{
		{
			name:       "APISIX 3.13 - Existing Resource",
			version:    constant.APISIXVersion313,
			shouldFail: false,
		},
		{
			name:       "APISIX 3.16 - Existing Resource",
			version:    constant.APISIXVersion316,
			shouldFail: false,
		},
		{
			name:       "Invalid Version",
			version:    "invalid_version",
			shouldFail: true,
		},
	}

	for _, tt := range tests {
		for _, resource := range constant.ResourceTypeList {
			testName := fmt.Sprintf("%s/%s", tt.name, resource.String())
			t.Run(testName, func(t *testing.T) {
				result := GetResourceSchema(tt.version, resource.String())
				if tt.shouldFail {
					assert.Nil(t, result)
				} else {
					assert.NotNil(t, result)
				}
			})
		}
	}
}

func TestGetPluginSchema(t *testing.T) {
	tests := []struct {
		name       string
		pluginName string
		schemaType string
		shouldFail bool
	}{
		{
			name:       "Plugin Schema",
			pluginName: "key-auth",
			schemaType: "",
			shouldFail: false,
		},
		{
			name:       "Consumer Schema",
			pluginName: "basic-auth",
			schemaType: "consumer",
			shouldFail: false,
		},
		{
			name:       "Metadata Schema",
			pluginName: "authz-casbin",
			schemaType: "metadata",
			shouldFail: false,
		},
		{
			name:       "Stream Schema",
			pluginName: "mqtt-proxy",
			schemaType: "stream",
			shouldFail: false,
		},
		{
			name:       "Non-existing Plugin",
			pluginName: "non_existing",
			schemaType: "",
			shouldFail: true,
		},
	}

	// 查询所有版本的 schema
	for version := range schemaVersionMap {
		for _, tt := range tests {
			testName := fmt.Sprintf("%s/%s", string(version), tt.name)
			t.Run(testName, func(t *testing.T) {
				result := GetPluginSchema(version, tt.pluginName, tt.schemaType)
				if tt.shouldFail {
					assert.Nil(t, result)
				} else {
					assert.NotNil(t, result)
				}
			})
		}
	}
}

func TestGetDashboardBKPluginSchemas(t *testing.T) {
	pluginNames := []string{
		"bk-access-token-source",
		"bk-cors",
		"bk-header-rewrite",
		"bk-ip-restriction",
		"bk-mock",
		"bk-rate-limit",
		"bk-request-body-limit",
		"bk-user-restriction",
		"bk-verified-user-exempted-apps",
		"bk-traffic-label",
	}

	for version := range schemaVersionMap {
		for _, pluginName := range pluginNames {
			testName := fmt.Sprintf("%s/%s", string(version), pluginName)
			t.Run(testName, func(t *testing.T) {
				assert.NotNil(t, GetPluginSchema(version, pluginName, ""))
			})
		}
	}
}
