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

package database_test

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/config"
)

var _ = Describe("Database", func() {
	Describe("DSN with TLS", func() {
		DescribeTable("generates correct DSN",
			func(database config.Database, expected string) {
				Expect(database.DSN()).To(Equal(expected))
			},
			Entry("database without TLS",
				config.Database{
					User: "root", Password: "password", Host: "localhost",
					Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: false},
				},
				"root:password@tcp(localhost:3306)/testdb?parseTime=true",
			),
			Entry("database with TLS enabled",
				config.Database{
					User: "root", Password: "password", Host: "localhost",
					Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: true},
				},
				"root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=custom",
			),
			Entry("database with full TLS configuration",
				config.Database{
					User: "root", Password: "password", Host: "localhost",
					Port: 3306, Name: "testdb",
					TLS: config.TLS{
						Enabled: true, CertCaFile: "/path/to/ca.pem",
						CertFile: "/path/to/cert.pem", CertKeyFile: "/path/to/key.pem",
						InsecureSkipVerify: true,
					},
				},
				"root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=custom",
			),
		)
	})

	Describe("NewClient with TLS Config", func() {
		DescribeTable("validates DSN generation",
			func(database config.Database, expectTLS bool) {
				dsn := database.DSN()
				Expect(dsn).NotTo(BeEmpty())

				if expectTLS {
					Expect(dsn).To(ContainSubstring("&tls=custom"))
				} else {
					Expect(dsn).NotTo(ContainSubstring("&tls="))
				}
			},
			Entry("valid database config without TLS",
				config.Database{
					User: "root", Password: "password", Host: "localhost",
					Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: false},
				}, false,
			),
			Entry("valid database config with TLS",
				config.Database{
					User: "root", Password: "password", Host: "localhost",
					Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: true},
				}, true,
			),
		)
	})

	Describe("Database Config Validation", func() {
		DescribeTable("validates database configuration",
			func(database config.Database, expectError bool) {
				err := database.ValidateDatabase()
				if expectError {
					Expect(err).To(HaveOccurred())
				} else {
					Expect(err).NotTo(HaveOccurred())
				}
			},
			Entry("valid config without TLS",
				config.Database{
					ID: "test", Host: "localhost", Port: 3306, User: "root",
					Name: "testdb", TLS: config.TLS{Enabled: false},
				}, false,
			),
			Entry("valid config with TLS but no cert files",
				config.Database{
					ID: "test", Host: "localhost", Port: 3306, User: "root",
					Name: "testdb", TLS: config.TLS{Enabled: true},
				}, false,
			),
			Entry("invalid config with TLS and non-existent cert files",
				config.Database{
					ID: "test", Host: "localhost", Port: 3306, User: "root",
					Name: "testdb",
					TLS:  config.TLS{Enabled: true, CertCaFile: "/non/existent/ca.pem"},
				}, true,
			),
		)
	})
})
