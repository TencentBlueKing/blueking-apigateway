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

// Package utils ...
package utils

import "slices"

// StringInSlice see if a string is in a string slice
func StringInSlice(target string, strs []string) bool {
	return slices.Contains(strs, target)
}

// TruncateBytes ...
func TruncateBytes(content []byte, length int) []byte {
	// If the length of the content is greater than the specified length,
	// return a slice of the content up to the specified length
	if len(content) > length {
		return content[:length]
	}
	// Otherwise, return the content as is
	return content
}

// TruncateBytesToString ...
func TruncateBytesToString(content []byte, length int) string {
	// Call the TruncateBytes function with the byte slice and integer as parameters
	s := TruncateBytes(content, length)
	// Convert the byte slice to a string and return it
	return string(s)
}
