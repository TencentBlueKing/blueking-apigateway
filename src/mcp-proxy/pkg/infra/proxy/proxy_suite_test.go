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

package proxy

import (
	"path/filepath"
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
	"mcp_proxy/pkg/metric"
)

var (
	apiLogPath   string
	auditLogPath string
)

var _ = BeforeSuite(func() {
	auditLogDir := GinkgoT().TempDir()
	apiLogPath = filepath.Join(auditLogDir, "api.log")
	auditLogPath = filepath.Join(auditLogDir, "audit.log")

	// Initialize config.G to avoid nil pointer dereference when genToolHandler accesses config fields.
	config.G = &config.Config{
		Logger: config.Logger{
			API: config.LogConfig{
				Level:  "info",
				Writer: "file",
				Settings: map[string]string{
					"name": "api.log",
					"path": auditLogDir,
				},
			},
			Audit: config.LogConfig{
				Level:  "info",
				Writer: "file",
				Settings: map[string]string{
					"name": "audit.log",
					"path": auditLogDir,
				},
			},
		},
	}
	// Initialize logger for tests
	logging.InitLogger(config.G)
	metric.InitMetrics("test_")
})

func TestProxy(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Proxy Suite")
}
