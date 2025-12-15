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
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGetWriter_OSType(t *testing.T) {
	tests := []struct {
		name        string
		settings    map[string]string
		expectError bool
	}{
		{
			name:        "stdout",
			settings:    map[string]string{"name": "stdout"},
			expectError: false,
		},
		{
			name:        "stderr",
			settings:    map[string]string{"name": "stderr"},
			expectError: false,
		},
		{
			name:        "unknown defaults to stdout",
			settings:    map[string]string{"name": "unknown"},
			expectError: false,
		},
		{
			name:        "empty name defaults to stdout",
			settings:    map[string]string{},
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			writer, err := getWriter("os", tt.settings)
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, writer)
			}
		})
	}
}

func TestGetWriter_UnknownType(t *testing.T) {
	// Unknown type should fallback to stdout
	writer, err := getWriter("unknown", map[string]string{})
	assert.NoError(t, err)
	assert.NotNil(t, writer)
	assert.Equal(t, os.Stdout, writer)
}

func TestGetOSWriter(t *testing.T) {
	tests := []struct {
		name     string
		settings map[string]string
		expected interface{}
	}{
		{
			name:     "stdout",
			settings: map[string]string{"name": "stdout"},
			expected: os.Stdout,
		},
		{
			name:     "stderr",
			settings: map[string]string{"name": "stderr"},
			expected: os.Stderr,
		},
		{
			name:     "default to stdout",
			settings: map[string]string{"name": "other"},
			expected: os.Stdout,
		},
		{
			name:     "empty settings",
			settings: map[string]string{},
			expected: os.Stdout,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			writer, err := getOSWriter(tt.settings)
			assert.NoError(t, err)
			assert.Equal(t, tt.expected, writer)
		})
	}
}

func TestGetFileWriter_MissingPath(t *testing.T) {
	settings := map[string]string{
		"name": "test.log",
	}

	_, err := getFileWriter(settings)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "path should not be empty")
}

func TestGetFileWriter_NonExistentPath(t *testing.T) {
	settings := map[string]string{
		"path": "/non/existent/path",
		"name": "test.log",
	}

	_, err := getFileWriter(settings)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not exists")
}

func TestGetFileWriter_InvalidBackups(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path":    tempDir,
		"name":    "test.log",
		"backups": "invalid",
	}

	_, err := getFileWriter(settings)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "backups should be integer")
}

func TestGetFileWriter_InvalidSize(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path": tempDir,
		"name": "test.log",
		"size": "invalid",
	}

	_, err := getFileWriter(settings)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "size should be integer")
}

func TestGetFileWriter_InvalidAge(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path": tempDir,
		"name": "test.log",
		"age":  "invalid",
	}

	_, err := getFileWriter(settings)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "age should be integer")
}

func TestGetFileWriter_Success(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path":    tempDir,
		"name":    "test.log",
		"backups": "5",
		"size":    "100",
		"age":     "30",
	}

	writer, err := getFileWriter(settings)
	assert.NoError(t, err)
	assert.NotNil(t, writer)
}

func TestGetFileWriter_DefaultValues(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path": tempDir,
		"name": "test.log",
	}

	writer, err := getFileWriter(settings)
	assert.NoError(t, err)
	assert.NotNil(t, writer)
}

func TestGetFileWriter_PathWithTrailingSlash(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path": tempDir + "/",
		"name": "test.log",
	}

	writer, err := getFileWriter(settings)
	assert.NoError(t, err)
	assert.NotNil(t, writer)
}

func TestGetWriter_FileType(t *testing.T) {
	tempDir := t.TempDir()
	settings := map[string]string{
		"path": tempDir,
		"name": "test.log",
	}

	writer, err := getWriter("file", settings)
	assert.NoError(t, err)
	assert.NotNil(t, writer)
}
