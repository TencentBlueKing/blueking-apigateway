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

package config_test

import (
	"os"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/spf13/viper"

	"mcp_proxy/pkg/config"
)

var _ = Describe("Config", func() {
	Describe("Database", func() {
		Describe("DSN", func() {
			DescribeTable("generates correct DSN",
				func(database config.Database, expected string) {
					Expect(database.DSN()).To(Equal(expected))
				},
				Entry("basic connection without TLS",
					config.Database{
						User:     "root",
						Password: "password",
						Host:     "localhost",
						Port:     3306,
						Name:     "testdb",
						TLS:      config.TLS{Enabled: false},
					},
					"root:password@tcp(localhost:3306)/testdb?parseTime=true",
				),
				Entry("connection with special characters in password",
					config.Database{
						User:     "ssl_root",
						Password: "qaz_WSX++",
						Host:     "localhost",
						Port:     3306,
						Name:     "testdb",
						TLS:      config.TLS{Enabled: false},
					},
					"ssl_root:qaz_WSX++@tcp(localhost:3306)/testdb?parseTime=true",
				),
				Entry("connection with TLS enabled",
					config.Database{
						User:     "root",
						Password: "password",
						Host:     "localhost",
						Port:     3306,
						Name:     "testdb",
						TLS:      config.TLS{Enabled: true},
					},
					"root:password@tcp(localhost:3306)/testdb?parseTime=true&tls=custom",
				),
				Entry(
					"real world example with special characters and TLS",
					config.Database{
						User:     "ssl_root",
						Password: "qaz_WSX++",
						Host:     "mysql-default.service.consul.",
						Port:     3306,
						Name:     "bk_apigateway",
						TLS: config.TLS{
							Enabled:     true,
							CertCaFile:  "/opt/blueking/apigw-db/certs/ca.pem",
							CertFile:    "/opt/blueking/apigw-db/certs/client-cert.pem",
							CertKeyFile: "/opt/blueking/apigw-db/certs/client-key.pem",
						},
					},
					"ssl_root:qaz_WSX++@tcp(mysql-default.service.consul.:3306)/bk_apigateway?parseTime=true&tls=custom",
				),
			)
		})

		Describe("TLSCfgName", func() {
			It("should return custom for all cases", func() {
				database := config.Database{TLS: config.TLS{Enabled: false}}
				Expect(database.TLSCfgName()).To(Equal("custom"))

				database = config.Database{TLS: config.TLS{Enabled: true}}
				Expect(database.TLSCfgName()).To(Equal("custom"))
			})
		})

		Describe("ValidateDatabase", func() {
			It("should pass for valid config without TLS", func() {
				db := config.Database{
					ID:   "test",
					Host: "localhost",
					Port: 3306,
					User: "root",
					Name: "testdb",
					TLS:  config.TLS{Enabled: false},
				}
				Expect(db.ValidateDatabase()).To(Succeed())
			})

			It("should fail for invalid TLS config with non-existent files", func() {
				db := config.Database{
					ID:   "test",
					Host: "localhost",
					Port: 3306,
					User: "root",
					Name: "testdb",
					TLS: config.TLS{
						Enabled:    true,
						CertCaFile: "/non/existent/ca.pem",
					},
				}
				Expect(db.ValidateDatabase()).To(HaveOccurred())
			})
		})

		Describe("TLS Integration", func() {
			DescribeTable("handles TLS configuration correctly",
				func(database config.Database, expectTLS bool) {
					dsn := database.DSN()
					Expect(dsn).NotTo(BeEmpty())

					if expectTLS {
						Expect(dsn).To(ContainSubstring("&tls=custom"))
					} else {
						Expect(dsn).NotTo(ContainSubstring("&tls="))
					}

					Expect(database.TLSCfgName()).To(Equal("custom"))
				},
				Entry("TLS disabled - no TLS in DSN",
					config.Database{
						User: "root", Password: "password", Host: "localhost",
						Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: false},
					}, false,
				),
				Entry("TLS enabled - should include tls=custom in DSN",
					config.Database{
						User: "root", Password: "password", Host: "localhost",
						Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: true},
					}, true,
				),
			)
		})

		Describe("URL Encoding", func() {
			DescribeTable("handles special characters in credentials",
				func(user, password, expected string) {
					database := config.Database{
						User: user, Password: password, Host: "localhost",
						Port: 3306, Name: "testdb", TLS: config.TLS{Enabled: false},
					}
					Expect(database.DSN()).To(Equal(expected))
				},
				Entry("simple credentials", "root", "password",
					"root:password@tcp(localhost:3306)/testdb?parseTime=true"),
				Entry("password with plus signs", "ssl_root", "qaz_WSX++",
					"ssl_root:qaz_WSX++@tcp(localhost:3306)/testdb?parseTime=true"),
				Entry("password with special characters", "user@domain", "p@ssw0rd!@#$%^&*()",
					"user@domain:p@ssw0rd!@#$%^&*()@tcp(localhost:3306)/testdb?parseTime=true"),
				Entry("password with spaces", "testuser", "my password with spaces",
					"testuser:my password with spaces@tcp(localhost:3306)/testdb?parseTime=true"),
				Entry("password with slashes", "admin", "pass/word/with/slashes",
					"admin:pass/word/with/slashes@tcp(localhost:3306)/testdb?parseTime=true"),
			)
		})

		Context("with real files", func() {
			var tempDir string
			var caFile, certFile, keyFile string

			BeforeEach(func() {
				tempDir = GinkgoT().TempDir()
				caFile = tempDir + "/ca.pem"
				certFile = tempDir + "/cert.pem"
				keyFile = tempDir + "/key.pem"

				for _, f := range []string{caFile, certFile, keyFile} {
					file, err := os.Create(f)
					Expect(err).NotTo(HaveOccurred())
					_, err = file.WriteString("test content")
					Expect(err).NotTo(HaveOccurred())
					file.Close()
				}
			})

			It("should handle TLS with existing certificate files", func() {
				database := config.Database{
					User: "ssl_root", Password: "qaz_WSX++",
					Host: "mysql-default.service.consul.", Port: 3306, Name: "bk_apigateway",
					TLS: config.TLS{
						Enabled: true, CertCaFile: caFile,
						CertFile: certFile, CertKeyFile: keyFile,
					},
				}

				dsn := database.DSN()
				Expect(dsn).NotTo(BeEmpty())
				Expect(dsn).To(ContainSubstring("&tls=custom"))
				Expect(database.TLSCfgName()).To(Equal("custom"))
				Expect(database.ValidateDatabase()).To(Succeed())
			})
		})
	})

	Describe("TLS", func() {
		Describe("ValidateTLS", func() {
			It("should pass when TLS is disabled", func() {
				tls := config.TLS{Enabled: false}
				Expect(tls.ValidateTLS()).To(Succeed())
			})

			It("should fail with non-existent CA file", func() {
				tls := config.TLS{Enabled: true, CertCaFile: "/non/existent/ca.pem"}
				Expect(tls.ValidateTLS()).To(HaveOccurred())
			})

			It("should fail with non-existent cert file", func() {
				tls := config.TLS{Enabled: true, CertFile: "/non/existent/cert.pem"}
				Expect(tls.ValidateTLS()).To(HaveOccurred())
			})

			It("should fail with non-existent key file", func() {
				tls := config.TLS{Enabled: true, CertKeyFile: "/non/existent/key.pem"}
				Expect(tls.ValidateTLS()).To(HaveOccurred())
			})

			It("should pass with empty cert files when TLS enabled", func() {
				tls := config.TLS{Enabled: true}
				Expect(tls.ValidateTLS()).To(Succeed())
			})

			Context("with existing files", func() {
				var tempDir string
				var caFile, certFile, keyFile string

				BeforeEach(func() {
					tempDir = GinkgoT().TempDir()
					caFile = tempDir + "/ca.pem"
					certFile = tempDir + "/cert.pem"
					keyFile = tempDir + "/key.pem"

					for _, f := range []string{caFile, certFile, keyFile} {
						file, err := os.Create(f)
						Expect(err).NotTo(HaveOccurred())
						_, err = file.WriteString("test content")
						Expect(err).NotTo(HaveOccurred())
						file.Close()
					}
				})

				It("should pass with existing files", func() {
					tls := config.TLS{
						Enabled: true, CertCaFile: caFile,
						CertFile: certFile, CertKeyFile: keyFile,
					}
					Expect(tls.ValidateTLS()).To(Succeed())
				})
			})
		})
	})

	Describe("Tracing", func() {
		Describe("GinAPIEnabled", func() {
			DescribeTable(
				"returns correct value",
				func(tracing config.Tracing, expected bool) {
					Expect(tracing.GinAPIEnabled()).To(Equal(expected))
				},
				Entry("both enabled", config.Tracing{Enable: true, Instrument: config.Instrument{GinAPI: true}}, true),
				Entry(
					"tracing disabled",
					config.Tracing{Enable: false, Instrument: config.Instrument{GinAPI: true}},
					false,
				),
				Entry(
					"gin api disabled",
					config.Tracing{Enable: true, Instrument: config.Instrument{GinAPI: false}},
					false,
				),
				Entry(
					"both disabled",
					config.Tracing{Enable: false, Instrument: config.Instrument{GinAPI: false}},
					false,
				),
			)
		})

		Describe("DBAPIEnabled", func() {
			DescribeTable(
				"returns correct value",
				func(tracing config.Tracing, expected bool) {
					Expect(tracing.DBAPIEnabled()).To(Equal(expected))
				},
				Entry("both enabled", config.Tracing{Enable: true, Instrument: config.Instrument{DbAPI: true}}, true),
				Entry(
					"tracing disabled",
					config.Tracing{Enable: false, Instrument: config.Instrument{DbAPI: true}},
					false,
				),
				Entry(
					"db api disabled",
					config.Tracing{Enable: true, Instrument: config.Instrument{DbAPI: false}},
					false,
				),
				Entry(
					"both disabled",
					config.Tracing{Enable: false, Instrument: config.Instrument{DbAPI: false}},
					false,
				),
			)
		})
	})

	Describe("Load", func() {
		It("should fail with empty database", func() {
			v := viper.New()
			v.Set("databases", []config.Database{})

			_, err := config.Load(v)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("database cannot be empty"))
		})

		It("should load valid config", func() {
			v := viper.New()
			v.Set("databases", []map[string]interface{}{
				{
					"id": "default", "host": "localhost", "port": 3306,
					"user": "root", "password": "password", "name": "testdb",
				},
			})

			cfg, err := config.Load(v)
			Expect(err).NotTo(HaveOccurred())
			Expect(cfg).NotTo(BeNil())
			Expect(cfg.Databases).To(HaveLen(1))
			Expect(cfg.Databases[0].ID).To(Equal("default"))

			// Check default values
			Expect(cfg.McpServer.Interval).NotTo(BeZero())
			Expect(cfg.McpServer.MessageUrlFormat).NotTo(BeEmpty())
			Expect(cfg.McpServer.MessageApplicationUrlFormat).NotTo(BeEmpty())
			Expect(cfg.McpServer.InnerJwtExpireTime).NotTo(BeZero())
		})

		It("should fail with invalid TLS config", func() {
			v := viper.New()
			v.Set("databases", []map[string]interface{}{
				{
					"id": "default", "host": "localhost", "port": 3306,
					"user": "root", "password": "password", "name": "testdb",
					"tls": map[string]interface{}{"enabled": true, "certcafile": "/non/existent/ca.pem"},
				},
			})

			_, err := config.Load(v)
			Expect(err).To(HaveOccurred())
		})

		It("should set global config", func() {
			v := viper.New()
			v.Set("databases", []map[string]interface{}{
				{
					"id": "default", "host": "localhost", "port": 3306,
					"user": "root", "password": "password", "name": "testdb",
				},
			})

			cfg, err := config.Load(v)
			Expect(err).NotTo(HaveOccurred())
			Expect(cfg).NotTo(BeNil())
			Expect(config.G).To(Equal(cfg))
		})

		It("should create database map", func() {
			v := viper.New()
			v.Set("databases", []map[string]interface{}{
				{
					"id": "primary", "host": "localhost", "port": 3306,
					"user": "root", "password": "password", "name": "testdb1",
				},
				{
					"id": "secondary", "host": "localhost", "port": 3307,
					"user": "root", "password": "password", "name": "testdb2",
				},
			})

			cfg, err := config.Load(v)
			Expect(err).NotTo(HaveOccurred())
			Expect(cfg).NotTo(BeNil())
			Expect(cfg.DatabaseMap).To(HaveLen(2))
			Expect(cfg.DatabaseMap).To(HaveKey("primary"))
			Expect(cfg.DatabaseMap).To(HaveKey("secondary"))
		})
	})

	Describe("Struct Fields", func() {
		It("Server should have correct fields", func() {
			server := config.Server{
				Host: "0.0.0.0", Port: 8080, GraceTimeout: 30,
				ReadTimeout: 10, WriteTimeout: 10, IdleTimeout: 60,
			}
			Expect(server.Host).To(Equal("0.0.0.0"))
			Expect(server.Port).To(Equal(8080))
			Expect(server.GraceTimeout).To(Equal(int64(30)))
		})

		It("LogConfig should have correct fields", func() {
			logConfig := config.LogConfig{
				Level: "info", Writer: "os",
				Settings: map[string]string{"name": "stdout"},
				Buffered: true,
				Desensitization: config.DesensitizationConfig{
					Enabled: true,
					Fields:  []config.DesensitizationFiled{{Key: "password", JsonPath: []string{"$.password"}}},
				},
			}
			Expect(logConfig.Level).To(Equal("info"))
			Expect(logConfig.Writer).To(Equal("os"))
			Expect(logConfig.Buffered).To(BeTrue())
			Expect(logConfig.Desensitization.Enabled).To(BeTrue())
			Expect(logConfig.Desensitization.Fields).To(HaveLen(1))
		})

		It("Sentry should have correct fields", func() {
			sentry := config.Sentry{DSN: "https://example@sentry.io/123", ReportLogLevel: 2}
			Expect(sentry.DSN).To(Equal("https://example@sentry.io/123"))
			Expect(sentry.ReportLogLevel).To(Equal(2))
		})

		It("McpServer should have correct fields", func() {
			mcpServer := config.McpServer{
				Interval: 60, BkApiUrlTmpl: "https://api.example.com",
				MessageUrlFormat: "/mcp/%s/message", MessageApplicationUrlFormat: "/mcp/%s/app/message",
				InnerJwtExpireTime: 300, EncryptKey: "test-key", CryptoNonce: "test-nonce",
			}
			Expect(mcpServer.BkApiUrlTmpl).To(Equal("https://api.example.com"))
			Expect(mcpServer.MessageUrlFormat).To(Equal("/mcp/%s/message"))
		})

		It("Pprof should have correct fields", func() {
			pprof := config.Pprof{Username: "admin", Password: "secret"}
			Expect(pprof.Username).To(Equal("admin"))
			Expect(pprof.Password).To(Equal("secret"))
		})
	})
})
