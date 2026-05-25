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

// Package envx 提供环境变量相关工具
package envx

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cast"
)

// Get 读取环境变量，支持默认值
func Get(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}

// GetBoolean 读取bool类型环境变量，支持默认值
func GetBoolean(key string, fallback bool) bool {
	if value, ok := os.LookupEnv(key); ok {
		return cast.ToBool(value)
	}
	return fallback
}

// GetFloat64 读取float64类型环境变量，支持默认值
func GetFloat64(key string, fallback float64) float64 {
	if value, ok := os.LookupEnv(key); ok {
		return cast.ToFloat64(value)
	}
	return fallback
}

// MustGet 读取环境变量，若不存在则 panic
func MustGet(key string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}

	panic(fmt.Sprintf("required environment variable %s unset", key))
}

// GetDuration 读取时间类型环境变量，支持默认值
func GetDuration(key, fallback string) time.Duration {
	timeValue, _ := time.ParseDuration(Get(key, fallback))
	return timeValue
}
