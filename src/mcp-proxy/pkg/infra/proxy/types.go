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
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"strconv"
)

// maxSafeFloat64Integer is the largest consecutive integer exactly representable
// by IEEE 754 double-precision (2^53 - 1). Values beyond this threshold may lose
// precision when stored as float64, so we avoid int64 conversion for them.
const maxSafeFloat64Integer = 1<<53 - 1

// stringifyRequestParamValue converts a decoded JSON value to its string representation
// suitable for HTTP header/query/path parameters. It preserves numeric precision by:
//   - json.Number: returned directly via String() (primary path when UseNumber is enabled)
//   - float64/float32: fallback for values not decoded via UseNumber; formats integers
//     without decimal point and floats without scientific notation
//   - string: passed through unchanged
//   - other types (bool, nil, etc.): formatted via fmt.Sprintf
func stringifyRequestParamValue(value any) string {
	switch value := value.(type) {
	case json.Number:
		return value.String()
	case float64:
		if value == math.Trunc(value) && value >= -maxSafeFloat64Integer && value <= maxSafeFloat64Integer {
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
// It uses a custom UnmarshalJSON with json.Decoder.UseNumber() to prevent
// large integers (e.g., 2005000002) from being formatted in scientific notation.
type StringParamMap map[string]string

// UnmarshalJSON decodes JSON object values into strings, preserving numeric precision.
// Numbers are decoded as json.Number (not float64) to avoid precision loss,
// then converted to their exact string representation.
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

// HandlerRequest represents the structured arguments for an MCP tool call.
// HeaderParam, QueryParam, and PathParam are decoded as StringParamMap — all values
// are converted to strings at unmarshal time to ensure correct HTTP parameter formatting.
// BodyParam retains standard json.Unmarshal behavior (numbers as float64) since it is
// serialized as JSON body and does not require string conversion.
type HandlerRequest struct {
	HeaderParam StringParamMap `json:"header_param,omitempty"`
	QueryParam  StringParamMap `json:"query_param,omitempty"`
	PathParam   StringParamMap `json:"path_param,omitempty"`
	BodyParam   any            `json:"body_param,omitempty"`
}
