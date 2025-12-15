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

package proxy

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestHandlerRequest_JSONMarshal(t *testing.T) {
	request := HandlerRequest{
		HeaderParam: map[string]any{
			"Content-Type": "application/json",
		},
		QueryParam: map[string]any{
			"limit":  10,
			"offset": 0,
		},
		PathParam: map[string]any{
			"id": "123",
		},
		BodyParam: map[string]any{
			"name": "test",
		},
	}

	data, err := json.Marshal(request)
	assert.NoError(t, err)
	assert.NotEmpty(t, data)

	// Unmarshal back
	var result HandlerRequest
	err = json.Unmarshal(data, &result)
	assert.NoError(t, err)
	assert.Equal(t, "application/json", result.HeaderParam["Content-Type"])
	assert.Equal(t, float64(10), result.QueryParam["limit"])
	assert.Equal(t, "123", result.PathParam["id"])
	assert.Equal(t, "test", result.BodyParam.(map[string]any)["name"])
}

func TestHandlerRequest_EmptyFields(t *testing.T) {
	request := HandlerRequest{}

	data, err := json.Marshal(request)
	assert.NoError(t, err)

	// Should be empty JSON object
	assert.Equal(t, "{}", string(data))
}

func TestHandlerRequest_PartialFields(t *testing.T) {
	request := HandlerRequest{
		QueryParam: map[string]any{
			"search": "test",
		},
	}

	data, err := json.Marshal(request)
	assert.NoError(t, err)

	var result map[string]any
	err = json.Unmarshal(data, &result)
	assert.NoError(t, err)

	// Only query_param should be present
	assert.Contains(t, result, "query_param")
	assert.NotContains(t, result, "header_param")
	assert.NotContains(t, result, "path_param")
	assert.NotContains(t, result, "body_param")
}

func TestHandlerRequest_ComplexBodyParam(t *testing.T) {
	request := HandlerRequest{
		BodyParam: map[string]any{
			"user": map[string]any{
				"name":  "John",
				"email": "john@example.com",
				"roles": []string{"admin", "user"},
			},
		},
	}

	data, err := json.Marshal(request)
	assert.NoError(t, err)

	var result HandlerRequest
	err = json.Unmarshal(data, &result)
	assert.NoError(t, err)

	body := result.BodyParam.(map[string]any)
	user := body["user"].(map[string]any)
	assert.Equal(t, "John", user["name"])
	assert.Equal(t, "john@example.com", user["email"])
}

func TestHandlerRequest_UnmarshalFromJSON(t *testing.T) {
	jsonStr := `{
		"header_param": {"Authorization": "Bearer token"},
		"query_param": {"page": 1},
		"path_param": {"userId": "abc123"},
		"body_param": {"data": "test"}
	}`

	var request HandlerRequest
	err := json.Unmarshal([]byte(jsonStr), &request)
	assert.NoError(t, err)

	assert.Equal(t, "Bearer token", request.HeaderParam["Authorization"])
	assert.Equal(t, float64(1), request.QueryParam["page"])
	assert.Equal(t, "abc123", request.PathParam["userId"])
	assert.Equal(t, "test", request.BodyParam.(map[string]any)["data"])
}
