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

// Package biz  ...
package biz

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"strings"
)

// GenResourceIDKey 生成资源 ID 查询的 key
func GenResourceIDKey(gatewayName, stageName string, resourceID int64) string {
	// {gateway}.{stage}.{resourceID}
	return fmt.Sprintf("%s.%s.%d", gatewayName, stageName, resourceID)
}

// GenApigwResourceNameKey 生成 apigw 资源名称查询的 key
func GenApigwResourceNameKey(gatewayName, stageName, resourceName string) string {
	// {gateway}.{stage}.{resourceName}
	key := fmt.Sprintf("%s.%s.%s", gatewayName, stageName, resourceName)

	// key 长度大于 100 需要截断
	if len(key) > 100 {
		return key[:100-3] + "..."
	}
	return key
}

func toLowerDashCase(s string) string {
	return strings.ToLower(strings.ReplaceAll(s, "_", "-"))
}

// GenApisixResourceNameKey 生成 apisix 资源名称查询的 key
func GenApisixResourceNameKey(gatewayName, stageName, resourceName string) string {
	key := toLowerDashCase(fmt.Sprintf("%s-%s-%s", gatewayName, stageName, resourceName))

	// key 长度大于 64 需要转换
	if len(key) > 64 {
		hash := md5.Sum([]byte(key[55:]))
		hashStr := hex.EncodeToString(hash[:])[:8]

		key = fmt.Sprintf("%s.%s", key[:55], hashStr)
	}
	return key
}
