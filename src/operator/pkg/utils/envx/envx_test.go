/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - 微网关(BlueKing - Micro APIGateway) available.
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
package envx_test

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"

	"operator/pkg/utils/envx"
)

// 不存在的环境变量
func TestGetNotExists(t *testing.T) {
	ret := envx.Get("NOT_EXISTS_ENV_KEY", "ENV_VAL")
	assert.Equal(t, "ENV_VAL", ret)
}

// 测试GetBoolean函数
func TestGetBoolean(t *testing.T) {
	t.Run("true value", func(t *testing.T) {
		t.Setenv("TEST_BOOL_KEY", "true")
		ret := envx.GetBoolean("TEST_BOOL_KEY", false)
		assert.True(t, ret)
	})

	t.Run("false value", func(t *testing.T) {
		t.Setenv("TEST_BOOL_KEY", "false")
		ret := envx.GetBoolean("TEST_BOOL_KEY", true)
		assert.False(t, ret)
	})

	t.Run("default value", func(t *testing.T) {
		ret := envx.GetBoolean("TEST_DEFAULT_BOOL_KEY", true)
		assert.True(t, ret)
	})
}

// 测试GetFloat64函数
func TestGetFloat64(t *testing.T) {
	t.Run("not exists", func(t *testing.T) {
		ret := envx.GetFloat64("NOT_EXISTS_FLOAT_KEY", 3.14)
		assert.Equal(t, 3.14, ret)
	})

	t.Run("valid float", func(t *testing.T) {
		t.Setenv("TEST_FLOAT_KEY", "123.456")
		ret := envx.GetFloat64("TEST_FLOAT_KEY", 0)
		assert.Equal(t, 123.456, ret)
	})

	t.Run("invalid float", func(t *testing.T) {
		t.Setenv("TEST_FLOAT_KEY", "invalid")
		ret := envx.GetFloat64("TEST_FLOAT_KEY", 0)
		assert.Equal(t, 0.0, ret)
	})
}

// 已存在的环境变量
func TestGetExists(t *testing.T) {
	ret := envx.Get("PATH", "")
	assert.NotEqual(t, "", ret)
}

// 不存在的环境变量
func TestMustGetNotExists(t *testing.T) {
	defer func() {
		assert.Equal(t, "required environment variable NOT_EXISTS_ENV_KEY unset", recover())
	}()

	_ = envx.MustGet("NOT_EXISTS_ENV_KEY")
}

// 已存在的环境变量
func TestMustGetExists(t *testing.T) {
	ret := envx.MustGet("PATH")
	assert.NotEqual(t, "", ret)
}

// 测试GetDuration函数
func TestGetDuration(t *testing.T) {
	t.Run("not exists", func(t *testing.T) {
		ret := envx.GetDuration("NOT_EXISTS_DURATION_KEY", "1h")
		assert.Equal(t, time.Hour, ret)
	})

	t.Run("valid duration", func(t *testing.T) {
		t.Setenv("TEST_DURATION_KEY", "30m")
		ret := envx.GetDuration("TEST_DURATION_KEY", "0")
		assert.Equal(t, 30*time.Minute, ret)
	})

	t.Run("invalid duration", func(t *testing.T) {
		t.Setenv("TEST_INVALID_DURATION_KEY", "invalid")
		ret := envx.GetDuration("TEST_INVALID_DURATION_KEY", "1h")
		assert.Equal(t, 0*time.Second, ret)
	})
}
