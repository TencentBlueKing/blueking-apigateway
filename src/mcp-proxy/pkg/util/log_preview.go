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

package util

import (
	"encoding/json"
	"strings"
	"unicode/utf8"
)

// JSONLogPreview reduces a sanitized JSON copy while retaining valid structure.
// Every output still passes through the regular credential sanitizer at write/display time.
func JSONLogPreview(text string, limit int) string {
	if text == HiddenLogBody || limit <= 0 || len(text) <= limit {
		return text
	}
	if len(text) > maxLogInputBytes {
		return HiddenLogBody
	}
	var value any
	decoder := json.NewDecoder(strings.NewReader(text))
	decoder.UseNumber()
	if !json.Valid([]byte(text)) || decoder.Decode(&value) != nil {
		return HiddenLogBody
	}
	for width := limit; width > 0; width /= 2 {
		projected := reduceLogJSON(value, width, 0)
		out, err := json.Marshal(projected)
		if err == nil && len(out) <= limit {
			return string(out)
		}
	}
	// Very small limits or large member names cannot carry a useful projection.
	return HiddenLogBody
}

func reduceLogJSON(value any, width, depth int) any {
	if depth > maxLogDepth {
		return HiddenLogBody
	}
	switch v := value.(type) {
	case map[string]any:
		out := make(map[string]any, len(v))
		for key, item := range v {
			out[key] = reduceLogJSON(item, width, depth+1)
		}
		return out
	case []any:
		count := min(len(v), max(1, width/16))
		out := make([]any, 0, count+1)
		for _, item := range v[:count] {
			out = append(out, reduceLogJSON(item, width, depth+1))
		}
		if count < len(v) {
			out = append(out, "...(truncated)")
		}
		return out
	case string:
		if v == HiddenLogBody || v == CredentialMask || len(v) <= width {
			return v
		}
		// Embedded JSON strings must remain valid JSON after shortening as well.
		var embedded any
		decoder := json.NewDecoder(strings.NewReader(v))
		decoder.UseNumber()
		if json.Valid([]byte(v)) && decoder.Decode(&embedded) == nil {
			out, err := json.Marshal(reduceLogJSON(embedded, width, depth+1))
			if err == nil {
				return string(out)
			}
		}
		end := min(len(v), width)
		for end > 0 && !utf8.RuneStart(v[end]) {
			end--
		}
		return v[:end] + "...(truncated)"
	default:
		return value
	}
}
