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

package util

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestReplacePlaceHolder(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		params   map[string]string
		expected string
	}{
		{
			name:  "simple replacement",
			input: "Hello, {name}!",
			params: map[string]string{
				"name": "World",
			},
			expected: "Hello, World!",
		},
		{
			name:  "multiple replacements",
			input: "{greeting}, {name}! Welcome to {place}.",
			params: map[string]string{
				"greeting": "Hello",
				"name":     "Alice",
				"place":    "Wonderland",
			},
			expected: "Hello, Alice! Welcome to Wonderland.",
		},
		{
			name:  "placeholder with spaces",
			input: "Hello, { name }!",
			params: map[string]string{
				"name": "World",
			},
			expected: "Hello, World!",
		},
		{
			name:  "missing param keeps placeholder",
			input: "Hello, {name}!",
			params: map[string]string{
				"other": "value",
			},
			expected: "Hello, {name}!",
		},
		{
			name:     "empty params",
			input:    "Hello, {name}!",
			params:   map[string]string{},
			expected: "Hello, {name}!",
		},
		{
			name:  "no placeholders",
			input: "Hello, World!",
			params: map[string]string{
				"name": "Alice",
			},
			expected: "Hello, World!",
		},
		{
			name:  "url template",
			input: "https://api.example.com/{api_name}/{stage}/resource",
			params: map[string]string{
				"api_name": "my-gateway",
				"stage":    "prod",
			},
			expected: "https://api.example.com/my-gateway/prod/resource",
		},
		{
			name:  "empty replacement value",
			input: "Hello, {name}!",
			params: map[string]string{
				"name": "",
			},
			expected: "Hello, !",
		},
		{
			name:  "special characters in replacement",
			input: "Path: {path}",
			params: map[string]string{
				"path": "/api/v1/users?id=123",
			},
			expected: "Path: /api/v1/users?id=123",
		},
		{
			name:  "partial match",
			input: "{api_name} and {api_name_v2}",
			params: map[string]string{
				"api_name":    "gateway1",
				"api_name_v2": "gateway2",
			},
			expected: "gateway1 and gateway2",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ReplacePlaceHolder(tt.input, tt.params)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestReplacePlaceHolder_NilParams(t *testing.T) {
	input := "Hello, {name}!"
	result := ReplacePlaceHolder(input, nil)
	assert.Equal(t, "Hello, {name}!", result)
}
