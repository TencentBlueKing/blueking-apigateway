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

package logging

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"go.uber.org/zap"

	"mcp_proxy/pkg/config"
)

func TestParseZapLogLevel(t *testing.T) {
	tests := []struct {
		name        string
		level       string
		expected    interface{}
		expectError bool
	}{
		{
			name:        "panic level",
			level:       "panic",
			expected:    zap.PanicLevel,
			expectError: false,
		},
		{
			name:        "fatal level",
			level:       "fatal",
			expected:    zap.FatalLevel,
			expectError: false,
		},
		{
			name:        "error level",
			level:       "error",
			expected:    zap.ErrorLevel,
			expectError: false,
		},
		{
			name:        "warn level",
			level:       "warn",
			expected:    zap.WarnLevel,
			expectError: false,
		},
		{
			name:        "warning level",
			level:       "warning",
			expected:    zap.WarnLevel,
			expectError: false,
		},
		{
			name:        "info level",
			level:       "info",
			expected:    zap.InfoLevel,
			expectError: false,
		},
		{
			name:        "debug level",
			level:       "debug",
			expected:    zap.DebugLevel,
			expectError: false,
		},
		{
			name:        "uppercase INFO",
			level:       "INFO",
			expected:    zap.InfoLevel,
			expectError: false,
		},
		{
			name:        "mixed case Error",
			level:       "Error",
			expected:    zap.ErrorLevel,
			expectError: false,
		},
		{
			name:        "invalid level",
			level:       "invalid",
			expected:    nil,
			expectError: true,
		},
		{
			name:        "empty level",
			level:       "",
			expected:    nil,
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			level, err := parseZapLogLevel(tt.level)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.expected, level)
			}
		})
	}
}

func TestNewZapJSONLogger_Basic(t *testing.T) {
	cfg := &config.LogConfig{
		Level:    "info",
		Writer:   "os",
		Settings: map[string]string{"name": "stdout"},
		Buffered: false,
	}

	logger := newZapJSONLogger(cfg, nil)
	assert.NotNil(t, logger)
}

func TestNewZapJSONLogger_Buffered(t *testing.T) {
	cfg := &config.LogConfig{
		Level:    "debug",
		Writer:   "os",
		Settings: map[string]string{"name": "stdout"},
		Buffered: true,
	}

	logger := newZapJSONLogger(cfg, nil)
	assert.NotNil(t, logger)
}

func TestNewZapJSONLogger_InvalidLevel(t *testing.T) {
	cfg := &config.LogConfig{
		Level:    "invalid",
		Writer:   "os",
		Settings: map[string]string{"name": "stdout"},
		Buffered: false,
	}

	// Should not panic, should use default level
	logger := newZapJSONLogger(cfg, nil)
	assert.NotNil(t, logger)
}

func TestNewZapJSONLogger_WithDesensitization(t *testing.T) {
	cfg := &config.LogConfig{
		Level:    "info",
		Writer:   "os",
		Settings: map[string]string{"name": "stdout"},
		Buffered: false,
		Desensitization: config.DesensitizationConfig{
			Enabled: true,
			Fields: []config.DesensitizationFiled{
				{Key: "password", JsonPath: []string{"$.password"}},
				{Key: "token", JsonPath: []string{"$.token"}},
			},
		},
	}

	logger := newZapJSONLogger(cfg, nil)
	assert.NotNil(t, logger)
}

func TestNewZapJSONLogger_DefaultWriter(t *testing.T) {
	cfg := &config.LogConfig{
		Level:    "info",
		Writer:   "unknown",
		Settings: map[string]string{},
		Buffered: false,
	}

	// Should fallback to stdout
	logger := newZapJSONLogger(cfg, nil)
	assert.NotNil(t, logger)
}

func TestNewZapJSONLogger_StderrWriter(t *testing.T) {
	cfg := &config.LogConfig{
		Level:    "info",
		Writer:   "os",
		Settings: map[string]string{"name": "stderr"},
		Buffered: false,
	}

	logger := newZapJSONLogger(cfg, nil)
	assert.NotNil(t, logger)
}

func TestNewZapJSONLogger_AllLogLevels(t *testing.T) {
	levels := []string{"panic", "fatal", "error", "warn", "info", "debug"}

	for _, level := range levels {
		t.Run(level, func(t *testing.T) {
			cfg := &config.LogConfig{
				Level:    level,
				Writer:   "os",
				Settings: map[string]string{"name": "stdout"},
				Buffered: false,
			}

			logger := newZapJSONLogger(cfg, nil)
			assert.NotNil(t, logger)
		})
	}
}
