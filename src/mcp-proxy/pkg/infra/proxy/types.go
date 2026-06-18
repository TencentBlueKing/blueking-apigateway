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

package proxy

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"strconv"
)

const maxExactFloatInteger = 1<<53 - 1

func stringifyRequestParamValue(value any) string {
	switch value := value.(type) {
	case json.Number:
		return value.String()
	case float64:
		if value == math.Trunc(value) && value >= -maxExactFloatInteger && value <= maxExactFloatInteger {
			return strconv.FormatInt(int64(value), 10)
		}
		return strconv.FormatFloat(value, 'f', -1, 64)
	case float32:
		return strconv.FormatFloat(float64(value), 'f', -1, 32)
	case string:
		return value
	default:
		return fmt.Sprintf("%v", value)
	}
}

// StringParamMap stores HTTP header/query/path parameters as strings.
type StringParamMap map[string]string

// UnmarshalJSON decodes JSON values into strings, preserving numeric precision.
func (m *StringParamMap) UnmarshalJSON(data []byte) error {
	if string(data) == "null" {
		*m = nil
		return nil
	}

	var values map[string]any
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.UseNumber()
	if err := decoder.Decode(&values); err != nil {
		return err
	}

	result := make(StringParamMap, len(values))
	for key, value := range values {
		result[key] = stringifyRequestParamValue(value)
	}
	*m = result
	return nil
}

// QueryParam stores HTTP query parameters as multiple string values per key.
type QueryParam map[string][]string

// UnmarshalJSON decodes JSON query values into strings, preserving numeric precision and arrays.
func (m *QueryParam) UnmarshalJSON(data []byte) error {
	if string(data) == "null" {
		*m = nil
		return nil
	}

	var values map[string]any
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.UseNumber()
	if err := decoder.Decode(&values); err != nil {
		return err
	}

	result := make(QueryParam, len(values))
	for key, value := range values {
		if items, ok := value.([]any); ok {
			if len(items) == 0 {
				continue
			}

			queryValues := make([]string, 0, len(items))
			for _, item := range items {
				queryValues = append(queryValues, stringifyRequestParamValue(item))
			}
			result[key] = queryValues
			continue
		}

		result[key] = []string{stringifyRequestParamValue(value)}
	}
	*m = result
	return nil
}

// HandlerRequest ...
type HandlerRequest struct {
	HeaderParam StringParamMap `json:"header_param,omitempty"`
	QueryParam  QueryParam     `json:"query_param,omitempty"`
	PathParam   StringParamMap `json:"path_param,omitempty"`
	BodyParam   any            `json:"body_param,omitempty"`
}
