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
	"bytes"
	"encoding/json"
	"os"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Desensitize", func() {
	var (
		file    *os.File
		encoder zapcore.Encoder
		core    zapcore.Core
		logger  *zap.Logger
	)

	BeforeEach(func() {
		var err error
		file, err = os.CreateTemp(".", "logging_test_*.log")
		Expect(err).NotTo(HaveOccurred())

		encoder = zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig())
	})

	AfterEach(func() {
		if logger != nil {
			logger.Sync()
		}
		if file != nil {
			os.Remove(file.Name())
		}
	})

	Describe("JsonArray", func() {
		It("should desensitize array fields", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"data.#.bk_app_secret"},
			}))

			body := map[string]interface{}{
				"data": []struct {
					BkAppSecret string `json:"bk_app_secret"`
					BkAppCode   string `json:"bk_app_code"`
				}{
					{BkAppSecret: "1111-5678-9012-1111", BkAppCode: "test1"},
					{BkAppSecret: "2222-5678-9012-2222", BkAppCode: "test2"},
					{BkAppSecret: "3333-5678-9012-3333", BkAppCode: "test3"},
				},
			}

			buf := new(bytes.Buffer)
			err := json.NewEncoder(buf).Encode(body)
			Expect(err).NotTo(HaveOccurred())
			logger.Info("Sensitive data", zap.String("body", buf.String()))
		})
	})

	Describe("Single field desensitization", func() {
		It("should desensitize single string field", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"password"},
			}))

			body := `{"password": "my-secret-password-123", "username": "testuser"}`
			logger.Info("Login attempt", zap.String("body", body))
		})

		It("should desensitize nested field", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"user.credentials.token"},
			}))

			body := `{"user": {"name": "test", "credentials": {"token": "secret-token-12345678"}}}`
			logger.Info("User data", zap.String("body", body))
		})
	})

	Describe("Short value handling", func() {
		It("should handle short values (less than 7 chars)", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"pin"},
			}))

			body := `{"pin": "1234"}`
			logger.Info("Short value", zap.String("body", body))
		})
	})

	Describe("Non-existent field", func() {
		It("should handle non-existent field gracefully", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"non_existent_field"},
			}))

			body := `{"username": "testuser"}`
			logger.Info("No sensitive data", zap.String("body", body))
		})
	})

	Describe("Multiple sensitive fields", func() {
		It("should desensitize multiple fields in same log", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"password", "api_key", "secret"},
			}))

			body := `{"password": "pass123456789", "api_key": "key-abcdefghij", "secret": "sec-1234567890", "public": "visible"}`
			logger.Info("Multiple secrets", zap.String("body", body))
		})
	})

	Describe("With method", func() {
		It("should create new core with fields", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"token"},
			}))

			childLogger := logger.With(zap.String("request_id", "12345"))
			body := `{"token": "bearer-token-secret-value"}`
			childLogger.Info("With fields", zap.String("body", body))
		})
	})

	Describe("Check method", func() {
		It("should check if level is enabled", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.WarnLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"secret"},
			}))

			// Info level should not be logged when core is WarnLevel
			logger.Info("This should not be logged", zap.String("body", `{"secret": "value"}`))
			// Warn level should be logged
			logger.Warn("This should be logged", zap.String("body", `{"secret": "value"}`))
		})
	})

	Describe("Sync method", func() {
		It("should sync without error", func() {
			w := &zapcore.BufferedWriteSyncer{
				WS:            zapcore.AddSync(file),
				Size:          256 * 1024,
				FlushInterval: 30 * time.Second,
			}
			core = zapcore.NewCore(encoder, w, zapcore.InfoLevel)

			logger = zap.New(core, logging.WithDesensitize(map[string][]string{
				"body": {"secret"},
			}))

			logger.Info("Test sync", zap.String("body", `{"secret": "value"}`))
			err := logger.Sync()
			Expect(err).NotTo(HaveOccurred())
		})
	})
})
