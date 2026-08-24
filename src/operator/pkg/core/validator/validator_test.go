/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package validator

import (
	"testing"

	"github.com/stretchr/testify/require"

	"operator/pkg/constant"
)

func TestValidateAIServiceAndRoute(t *testing.T) {
	service := []byte(`{
		"id":"gateway.prod.1-10",
		"name":"gateway.prod.model-service",
		"plugins":{
			"ai-proxy":{
				"provider":"openai-compatible",
				"auth":{"header":{"Authorization":"Bearer test"}},
				"options":{"model":"gpt-4.1-mini","temperature":0.2},
				"override":{"endpoint":"https://models.example.com/v1/chat/completions"},
				"timeout":45000,
				"ssl_verify":true,
				"logging":{"summaries":true,"payloads":false}
			}
		}
	}`)
	route := []byte(`{
		"id":"gateway.prod.11",
		"name":"gateway.prod.chat-completions",
		"uris":["/api/gateway/prod/v1/chat/completions"],
		"methods":["POST"],
		"plugins":{"bk-resource-context":{}},
		"service_id":"gateway.prod.1-10"
	}`)

	for _, version := range []string{"3.16", "3.18"} {
		t.Run(version, func(t *testing.T) {
			require.NoError(t, ValidateApisixJsonSchema(version, constant.Service, service))
			require.NoError(t, ValidateApisixJsonSchema(version, constant.Route, route))
		})
	}
}

func TestValidatePluginMetadataAppliesSchemaDefaults(t *testing.T) {
	tests := []struct {
		name      string
		config    string
		wantError string
	}{
		{
			name: "missing policy uses local default",
			config: `{
				"id":"bk-concurrency-limit",
				"conn":2000,
				"burst":1000,
				"default_conn_delay":1,
				"key_type":"var",
				"key":"bk_concurrency_limit_key",
				"allow_degradation":true
			}`,
		},
		{
			name: "explicit redis still requires host",
			config: `{
				"id":"bk-concurrency-limit",
				"conn":2000,
				"burst":1000,
				"default_conn_delay":1,
				"key_type":"var",
				"key":"bk_concurrency_limit_key",
				"allow_degradation":true,
				"policy":"redis"
			}`,
			wantError: "redis_host is required",
		},
		{
			name: "explicit redis with host",
			config: `{
				"id":"bk-concurrency-limit",
				"conn":2000,
				"burst":1000,
				"default_conn_delay":1,
				"key_type":"var",
				"key":"bk_concurrency_limit_key",
				"allow_degradation":true,
				"policy":"redis",
				"redis_host":"redis.example.com"
			}`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateApisixJsonSchema("3.18", constant.PluginMetadata, []byte(tt.config))
			if tt.wantError != "" {
				require.Error(t, err)
				require.Contains(t, err.Error(), tt.wantError)
				return
			}
			require.NoError(t, err)
		})
	}
}
