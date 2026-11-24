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
	"fmt"

	"mcp_proxy/pkg/config"
)

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

// MaskSensitiveHeaders returns a copy with entire nonempty credential values masked.
func MaskSensitiveHeaders(headerInfo map[string]string) map[string]string {
	sanitizer := NewLogSanitizer(config.DesensitizationConfig{})
	masked := make(map[string]string, len(headerInfo))
	for key, value := range headerInfo {
		if sanitizer.Sensitive(key) && value != "" {
			masked[key] = CredentialMask
		} else {
			masked[key] = value
		}
	}
	return masked
}
