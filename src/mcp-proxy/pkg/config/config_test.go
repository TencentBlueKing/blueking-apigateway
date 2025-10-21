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
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=true",
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
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=true&tls_ca=/path/to/ca.pem&tls_cert=/path/to/cert.pem&tls_key=/path/to/key.pem",
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
			expected: "root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=true&tls_insecure_skip_verify=true",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.database.DSN()
			assert.Equal(t, tt.expected, result)
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
