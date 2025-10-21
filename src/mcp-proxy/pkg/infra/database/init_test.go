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

package database

import (
	"testing"

	"github.com/stretchr/testify/assert"

	"mcp_proxy/pkg/config"
)

func TestDatabase_DSN_WithTLS(t *testing.T) {
	tests := []struct {
		name     string
		database config.Database
		expected string
	}{
		{
			name: "database without TLS",
			database: config.Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: config.TLS{
					Enabled: false,
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name: "database with TLS enabled",
			database: config.Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: config.TLS{
					Enabled: true,
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=true",
		},
		{
			name: "database with full TLS configuration",
			database: config.Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: config.TLS{
					Enabled:            true,
					CertCaFile:         "/path/to/ca.pem",
					CertFile:           "/path/to/cert.pem",
					CertKeyFile:        "/path/to/key.pem",
					InsecureSkipVerify: true,
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=true&tls_ca=/path/to/ca.pem&tls_cert=/path/to/cert.pem&tls_key=/path/to/key.pem&tls_insecure_skip_verify=true",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.database.DSN()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestNewClient_WithTLSConfig(t *testing.T) {
	// 注意：这个测试需要真实的数据库连接，所以这里只测试配置解析
	// 在实际环境中，应该使用测试数据库或者mock

	tests := []struct {
		name        string
		database    config.Database
		expectError bool
	}{
		{
			name: "valid database config without TLS",
			database: config.Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: config.TLS{
					Enabled: false,
				},
			},
			expectError: false, // 这里会失败因为没有真实数据库，但配置解析是正确的
		},
		{
			name: "valid database config with TLS",
			database: config.Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: config.TLS{
					Enabled: true,
				},
			},
			expectError: false, // 这里会失败因为没有真实数据库，但配置解析是正确的
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// 验证DSN生成是否正确
			dsn := tt.database.DSN()
			assert.NotEmpty(t, dsn)

			// 如果启用了TLS，检查DSN中是否包含TLS参数
			if tt.database.TLS.Enabled {
				assert.Contains(t, dsn, "tls=true")
			} else {
				assert.NotContains(t, dsn, "tls=true")
			}
		})
	}
}

func TestDatabaseConfig_Validation(t *testing.T) {
	tests := []struct {
		name        string
		database    config.Database
		expectError bool
	}{
		{
			name: "valid config without TLS",
			database: config.Database{
				ID:   "test",
				Host: "localhost",
				Port: 3306,
				User: "root",
				Name: "testdb",
				TLS: config.TLS{
					Enabled: false,
				},
			},
			expectError: false,
		},
		{
			name: "valid config with TLS but no cert files",
			database: config.Database{
				ID:   "test",
				Host: "localhost",
				Port: 3306,
				User: "root",
				Name: "testdb",
				TLS: config.TLS{
					Enabled: true,
				},
			},
			expectError: false,
		},
		{
			name: "invalid config with TLS and non-existent cert files",
			database: config.Database{
				ID:   "test",
				Host: "localhost",
				Port: 3306,
				User: "root",
				Name: "testdb",
				TLS: config.TLS{
					Enabled:    true,
					CertCaFile: "/non/existent/ca.pem",
				},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.database.ValidateDatabase()
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}
