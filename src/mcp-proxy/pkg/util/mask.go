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
	"encoding/json"
	"fmt"

	"mcp_proxy/pkg/constant"
)

// SensitiveHeaderKeys lists header keys whose values must be masked in logs.
var SensitiveHeaderKeys = map[string]struct{}{
	constant.BkApiAuthorizationHeaderKey: {},
	constant.BkGatewayJWTHeaderKey:       {},
}

// TruncateJSON 将任意对象序列化为 JSON 并截断到指定长度。
// 当 json.Marshal 失败时，回退为 fmt.Sprintf 转成 string 后再截断。
func TruncateJSON(v any, maxLen int) string {
	if v == nil {
		return ""
	}
	b, err := json.Marshal(v)
	var s string
	if err != nil {
		s = fmt.Sprintf("%v", v)
	} else {
		s = string(b)
	}
	if len(s) > maxLen {
		return s[:maxLen] + "...(truncated)"
	}
	return s
}

// MaskSensitiveHeaders returns a copy of headerInfo with sensitive values masked.
func MaskSensitiveHeaders(headerInfo map[string]string) map[string]string {
	masked := make(map[string]string, len(headerInfo))
	for k, v := range headerInfo {
		if _, ok := SensitiveHeaderKeys[k]; ok {
			if len(v) > 6 {
				masked[k] = v[:3] + "***" + v[len(v)-3:]
			} else {
				masked[k] = "***"
			}
		} else {
			masked[k] = v
		}
	}
	return masked
}
