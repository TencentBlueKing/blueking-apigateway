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

func TestValidateAIServiceAndRouteForAPISIX316(t *testing.T) {
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

	require.NoError(t, ValidateApisixJsonSchema("3.16", constant.Service, service))
	require.NoError(t, ValidateApisixJsonSchema("3.16", constant.Route, route))
}
