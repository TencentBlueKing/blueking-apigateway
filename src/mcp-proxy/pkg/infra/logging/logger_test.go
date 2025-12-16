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

package logging_test

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Logger", func() {
	Describe("ParseZapLogLevel", func() {
		DescribeTable("parses log levels correctly",
			func(level string, expected zapcore.Level, expectError bool) {
				result, err := logging.ParseZapLogLevel(level)
				if expectError {
					Expect(err).To(HaveOccurred())
				} else {
					Expect(err).NotTo(HaveOccurred())
					Expect(result).To(Equal(expected))
				}
			},
			Entry("panic level", "panic", zap.PanicLevel, false),
			Entry("fatal level", "fatal", zap.FatalLevel, false),
			Entry("error level", "error", zap.ErrorLevel, false),
			Entry("warn level", "warn", zap.WarnLevel, false),
			Entry("warning level", "warning", zap.WarnLevel, false),
			Entry("info level", "info", zap.InfoLevel, false),
			Entry("debug level", "debug", zap.DebugLevel, false),
			Entry("uppercase INFO", "INFO", zap.InfoLevel, false),
			Entry("mixed case Error", "Error", zap.ErrorLevel, false),
			Entry("invalid level", "invalid", zapcore.Level(0), true),
			Entry("empty level", "", zapcore.Level(0), true),
		)
	})

	Describe("NewZapJSONLogger", func() {
		It("should create basic logger", func() {
			cfg := &config.LogConfig{
				Level: "info", Writer: "os",
				Settings: map[string]string{"name": "stdout"},
				Buffered: false,
			}
			logger := logging.NewZapJSONLogger(cfg, nil)
			Expect(logger).NotTo(BeNil())
		})

		It("should create buffered logger", func() {
			cfg := &config.LogConfig{
				Level: "debug", Writer: "os",
				Settings: map[string]string{"name": "stdout"},
				Buffered: true,
			}
			logger := logging.NewZapJSONLogger(cfg, nil)
			Expect(logger).NotTo(BeNil())
		})

		It("should handle invalid level", func() {
			cfg := &config.LogConfig{
				Level: "invalid", Writer: "os",
				Settings: map[string]string{"name": "stdout"},
				Buffered: false,
			}
			logger := logging.NewZapJSONLogger(cfg, nil)
			Expect(logger).NotTo(BeNil())
		})

		It("should create logger with desensitization", func() {
			cfg := &config.LogConfig{
				Level: "info", Writer: "os",
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
			logger := logging.NewZapJSONLogger(cfg, nil)
			Expect(logger).NotTo(BeNil())
		})

		It("should fallback to stdout for unknown writer", func() {
			cfg := &config.LogConfig{
				Level: "info", Writer: "unknown",
				Settings: map[string]string{},
				Buffered: false,
			}
			logger := logging.NewZapJSONLogger(cfg, nil)
			Expect(logger).NotTo(BeNil())
		})

		It("should create logger with stderr writer", func() {
			cfg := &config.LogConfig{
				Level: "info", Writer: "os",
				Settings: map[string]string{"name": "stderr"},
				Buffered: false,
			}
			logger := logging.NewZapJSONLogger(cfg, nil)
			Expect(logger).NotTo(BeNil())
		})

		DescribeTable("creates logger for all log levels",
			func(level string) {
				cfg := &config.LogConfig{
					Level: level, Writer: "os",
					Settings: map[string]string{"name": "stdout"},
					Buffered: false,
				}
				logger := logging.NewZapJSONLogger(cfg, nil)
				Expect(logger).NotTo(BeNil())
			},
			Entry("panic", "panic"),
			Entry("fatal", "fatal"),
			Entry("error", "error"),
			Entry("warn", "warn"),
			Entry("info", "info"),
			Entry("debug", "debug"),
		)
	})
})
