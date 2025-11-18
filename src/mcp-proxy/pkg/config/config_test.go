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

package config

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDatabase_DSN(t *testing.T) {
	tests := []struct {
		name     string
		database Database
		expected string
	}{
		{
			name: "basic connection without TLS",
			database: Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled: false,
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name: "connection with special characters in password",
			database: Database{
				User:     "ssl_root",
				Password: "qaz_WSX++",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled: false,
				},
			},
			expected: "ssl_root:qaz_WSX++@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name: "connection with TLS enabled",
			database: Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled: true,
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=custom",
		},
		{
			name: "connection with TLS and CA certificate",
			database: Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled:     true,
					CertCaFile:  "/path/to/ca.pem",
					CertFile:    "/path/to/cert.pem",
					CertKeyFile: "/path/to/key.pem",
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=custom",
		},
		{
			name: "connection with TLS and insecure skip verify",
			database: Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled:            true,
					InsecureSkipVerify: true,
				},
			},
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=custom",
		},
		{
			name: "real world example with special characters and TLS",
			database: Database{
				User:     "ssl_root",
				Password: "qaz_WSX++",
				Host:     "mysql-default.service.consul.",
				Port:     3306,
				Name:     "bk_apigateway",
				TLS: TLS{
					Enabled:     true,
					CertCaFile:  "/opt/blueking/apigw-db/certs/ca.pem",
					CertFile:    "/opt/blueking/apigw-db/certs/client-cert.pem",
					CertKeyFile: "/opt/blueking/apigw-db/certs/client-key.pem",
				},
			},
			expected: "ssl_root:qaz_WSX++@tcp(mysql-default.service.consul.:3306)/bk_apigateway?parseTime=true&tls=custom",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.database.DSN()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDatabase_TLSCfgName(t *testing.T) {
	tests := []struct {
		name     string
		database Database
		expected string
	}{
		{
			name: "TLS disabled - should return custom",
			database: Database{
				TLS: TLS{
					Enabled: false,
				},
			},
			expected: "custom",
		},
		{
			name: "TLS enabled - should return custom",
			database: Database{
				TLS: TLS{
					Enabled: true,
				},
			},
			expected: "custom",
		},
		{
			name: "TLS enabled with certificates - should return custom",
			database: Database{
				TLS: TLS{
					Enabled:     true,
					CertCaFile:  "/path/to/ca.pem",
					CertFile:    "/path/to/cert.pem",
					CertKeyFile: "/path/to/key.pem",
				},
			},
			expected: "custom",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.database.TLSCfgName()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDatabase_TLS_Integration(t *testing.T) {
	tests := []struct {
		name        string
		database    Database
		expectTLS   bool
		expectError bool
	}{
		{
			name: "TLS disabled - no TLS in DSN",
			database: Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled: false,
				},
			},
			expectTLS:   false,
			expectError: false,
		},
		{
			name: "TLS enabled - should include tls=custom in DSN",
			database: Database{
				User:     "root",
				Password: "password",
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled: true,
				},
			},
			expectTLS:   true,
			expectError: false,
		},
		{
			name: "TLS enabled with special characters - should work correctly",
			database: Database{
				User:     "ssl_root",
				Password: "qaz_WSX++",
				Host:     "mysql-default.service.consul.",
				Port:     3306,
				Name:     "bk_apigateway",
				TLS: TLS{
					Enabled: true,
					// 不设置证书文件路径，避免文件不存在错误
				},
			},
			expectTLS:   true,
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// 测试DSN生成
			dsn := tt.database.DSN()
			assert.NotEmpty(t, dsn)

			// 检查TLS配置是否正确
			if tt.expectTLS {
				assert.Contains(t, dsn, "&tls=custom")
			} else {
				assert.NotContains(t, dsn, "&tls=")
			}

			// 测试TLS配置名称
			tlsCfgName := tt.database.TLSCfgName()
			assert.Equal(t, "custom", tlsCfgName)

			// 测试配置验证
			err := tt.database.ValidateDatabase()
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestDatabase_URLEncoding(t *testing.T) {
	tests := []struct {
		name     string
		user     string
		password string
		expected string
	}{
		{
			name:     "simple credentials",
			user:     "root",
			password: "password",
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name:     "password with plus signs",
			user:     "ssl_root",
			password: "qaz_WSX++",
			expected: "ssl_root:qaz_WSX++@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name:     "password with special characters",
			user:     "user@domain",
			password: "p@ssw0rd!@#$%^&*()",
			expected: "user@domain:p@ssw0rd!@#$%^&*()@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name:     "password with spaces",
			user:     "testuser",
			password: "my password with spaces",
			expected: "testuser:my password with spaces@tcp(localhost:3306)/testdb?parseTime=true",
		},
		{
			name:     "password with slashes",
			user:     "admin",
			password: "pass/word/with/slashes",
			expected: "admin:pass/word/with/slashes@tcp(localhost:3306)/testdb?parseTime=true",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			database := Database{
				User:     tt.user,
				Password: tt.password,
				Host:     "localhost",
				Port:     3306,
				Name:     "testdb",
				TLS: TLS{
					Enabled: false,
				},
			}

			result := database.DSN()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestDatabase_TLS_WithRealFiles(t *testing.T) {
	// 创建临时文件用于测试
	tempDir := t.TempDir()
	caFile := tempDir + "/ca.pem"
	certFile := tempDir + "/cert.pem"
	keyFile := tempDir + "/key.pem"

	// 创建临时文件
	createTempFile(t, caFile)
	createTempFile(t, certFile)
	createTempFile(t, keyFile)

	tests := []struct {
		name        string
		database    Database
		expectTLS   bool
		expectError bool
	}{
		{
			name: "TLS enabled with existing certificate files",
			database: Database{
				User:     "ssl_root",
				Password: "qaz_WSX++",
				Host:     "mysql-default.service.consul.",
				Port:     3306,
				Name:     "bk_apigateway",
				TLS: TLS{
					Enabled:     true,
					CertCaFile:  caFile,
					CertFile:    certFile,
					CertKeyFile: keyFile,
				},
			},
			expectTLS:   true,
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// 测试DSN生成
			dsn := tt.database.DSN()
			assert.NotEmpty(t, dsn)

			// 检查TLS配置是否正确
			if tt.expectTLS {
				assert.Contains(t, dsn, "&tls=custom")
			} else {
				assert.NotContains(t, dsn, "&tls=")
			}

			// 测试TLS配置名称
			tlsCfgName := tt.database.TLSCfgName()
			assert.Equal(t, "custom", tlsCfgName)

			// 测试配置验证
			err := tt.database.ValidateDatabase()
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestTLS_ValidateTLS(t *testing.T) {
	tests := []struct {
		name    string
		tls     TLS
		wantErr bool
	}{
		{
			name: "TLS disabled - should pass",
			tls: TLS{
				Enabled: false,
			},
			wantErr: false,
		},
		{
			name: "TLS enabled with non-existent CA file - should fail",
			tls: TLS{
				Enabled:    true,
				CertCaFile: "/non/existent/ca.pem",
			},
			wantErr: true,
		},
		{
			name: "TLS enabled with non-existent cert file - should fail",
			tls: TLS{
				Enabled:  true,
				CertFile: "/non/existent/cert.pem",
			},
			wantErr: true,
		},
		{
			name: "TLS enabled with non-existent key file - should fail",
			tls: TLS{
				Enabled:     true,
				CertKeyFile: "/non/existent/key.pem",
			},
			wantErr: true,
		},
		{
			name: "TLS enabled with empty cert files - should pass",
			tls: TLS{
				Enabled: true,
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.tls.ValidateTLS()
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestTLS_ValidateTLS_WithExistingFiles(t *testing.T) {
	// 创建临时文件用于测试
	tempDir := t.TempDir()
	caFile := tempDir + "/ca.pem"
	certFile := tempDir + "/cert.pem"
	keyFile := tempDir + "/key.pem"

	// 创建临时文件
	createTempFile(t, caFile)
	createTempFile(t, certFile)
	createTempFile(t, keyFile)

	tests := []struct {
		name    string
		tls     TLS
		wantErr bool
	}{
		{
			name: "TLS enabled with existing files - should pass",
			tls: TLS{
				Enabled:     true,
				CertCaFile:  caFile,
				CertFile:    certFile,
				CertKeyFile: keyFile,
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.tls.ValidateTLS()
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestDatabase_ValidateDatabase(t *testing.T) {
	tests := []struct {
		name    string
		db      Database
		wantErr bool
	}{
		{
			name: "valid database config without TLS",
			db: Database{
				ID:   "test",
				Host: "localhost",
				Port: 3306,
				User: "root",
				Name: "testdb",
				TLS: TLS{
					Enabled: false,
				},
			},
			wantErr: false,
		},
		{
			name: "invalid database config with non-existent TLS files",
			db: Database{
				ID:   "test",
				Host: "localhost",
				Port: 3306,
				User: "root",
				Name: "testdb",
				TLS: TLS{
					Enabled:    true,
					CertCaFile: "/non/existent/ca.pem",
				},
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.db.ValidateDatabase()
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

// 辅助函数：创建临时文件
func createTempFile(t *testing.T, filename string) {
	file, err := os.Create(filename)
	if err != nil {
		t.Fatalf("Failed to create temp file %s: %v", filename, err)
	}
	defer file.Close()

	// 写入一些内容
	_, err = file.WriteString("test content")
	if err != nil {
		t.Fatalf("Failed to write to temp file %s: %v", filename, err)
	}
}
