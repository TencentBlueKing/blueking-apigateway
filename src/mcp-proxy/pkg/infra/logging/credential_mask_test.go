/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * http://opensource.org/licenses/MIT
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

package logging_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Credential masking log boundary", func() {
	It("always protects configured JSON loggers, including objects and bound fields", func() {
		dir := GinkgoT().TempDir()
		logger := logging.NewZapJSONLogger(&config.LogConfig{
			Level: "info", Writer: "file", Settings: map[string]string{"path": dir, "name": "test.log"},
		}, nil)
		input := map[string]any{
			"BK_APP_SECRET": "credential-case", "token": false, "password": 0,
			"empty_secret": "", "null_secret": nil, "secret": []any{"credential-list"},
			"items": []any{1, map[string]any{"api_key": "credential-nested"}},
			"body":  `{"response_body":"{\"refresh_token\":\"credential-string\"}"}`,
		}
		original, err := json.Marshal(input)
		Expect(err).NotTo(HaveOccurred())
		fields := []zap.Field{zap.Any("params", input), zap.Error(errors.New("credential-error"))}
		logger.With(
			zap.Any("header", map[string]any{"aUtHoRiZaTiOn": "credential-header"}),
		).Info(
			"request",
			fields...,
		)
		Expect(logger.Sync()).To(Succeed())
		out, err := os.ReadFile(filepath.Join(dir, "test.log"))
		Expect(err).NotTo(HaveOccurred())
		Expect(string(out)).NotTo(ContainSubstring("credential-"))
		var entry map[string]any
		Expect(json.Unmarshal(out, &entry)).To(Succeed())
		params := entry["params"].(map[string]any)
		Expect(params).To(HaveKeyWithValue("token", "***"))
		Expect(params).To(HaveKeyWithValue("password", "***"))
		Expect(params).To(HaveKeyWithValue("secret", "***"))
		Expect(params).To(HaveKeyWithValue("empty_secret", ""))
		Expect(params).To(HaveKeyWithValue("null_secret", BeNil()))
		after, err := json.Marshal(input)
		Expect(err).NotTo(HaveOccurred())
		Expect(after).To(Equal(original))
		Expect(fields[0].Interface).To(Equal(input))
	})

	It("keeps custom paths additive for object fields and array projections", func() {
		var out bytes.Buffer
		logger := zap.New(zapcore.NewCore(zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
			zapcore.AddSync(&out), zap.InfoLevel), logging.WithDesensitize(map[string][]string{
			"params": {"data.#.private", "$.pin"},
		}))
		logger.Info("request", zap.Any("params", map[string]any{
			"token": "credential-default", "pin": 0,
			"data": []any{map[string]any{"private": "credential-path"}, map[string]any{"private": false}},
		}))
		Expect(out.String()).NotTo(ContainSubstring("credential-"))
		Expect(out.String()).To(ContainSubstring(`"pin":"***"`))
		Expect(out.String()).To(ContainSubstring(`"private":"***"`))
	})

	DescribeTable(
		"hides unreliable nested bodies while retaining envelope identifiers",
		func(body string) {
			var out bytes.Buffer
			logger := zap.New(zapcore.NewCore(zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
				zapcore.AddSync(&out), zap.InfoLevel), logging.WithDesensitize(nil))
			response, err := json.Marshal(map[string]any{
				"status_code": 502, "request_id": "req", "trace_id": "trace", "response_body": body,
			})
			Expect(err).NotTo(HaveOccurred())
			if len(body) > 1<<20 {
				logger.Info("request", zap.Any("response", map[string]any{
					"status_code":   502,
					"request_id":    "req",
					"trace_id":      "trace",
					"response_body": body,
				}))
			} else {
				logger.Info("request", zap.String("response", string(response)))
			}
			Expect(out.String()).NotTo(ContainSubstring("credential-"))
			var entry map[string]any
			Expect(json.Unmarshal(out.Bytes(), &entry)).To(Succeed())
			var envelope map[string]any
			if text, ok := entry["response"].(string); ok {
				Expect(json.Unmarshal([]byte(text), &envelope)).To(Succeed())
			} else {
				envelope = entry["response"].(map[string]any)
			}
			Expect(envelope).To(HaveKeyWithValue("status_code", float64(502)))
			Expect(envelope).To(HaveKeyWithValue("request_id", "req"))
			Expect(envelope).To(HaveKeyWithValue("trace_id", "trace"))
			Expect(envelope).To(HaveKeyWithValue("response_body", "正文已屏蔽：截断或格式未知，无法可靠脱敏"))
		},
		Entry("truncated JSON", `{"token":"credential-truncated`),
		Entry("unknown text", "credential-text"),
		Entry("oversized", strings.Repeat("credential-large", 100000)),
		Entry(
			"depth exhausted",
			strings.Repeat(`{"data":`, 40)+`{"token":"credential-deep"}`+strings.Repeat("}", 40),
		),
	)
})

type failingLogObject struct{}

func (failingLogObject) MarshalLogObject(enc zapcore.ObjectEncoder) error {
	enc.AddString("token", "credential-object")
	return errors.New("credential-marshaler-error")
}

var _ = Describe("Credential masking encoder failures", func() {
	It("protects inline encoding failure diagnostics", func() {
		var out bytes.Buffer
		logger := zap.New(
			zapcore.NewCore(
				zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
				zapcore.AddSync(&out),
				zap.InfoLevel,
			),
			logging.WithDesensitize(nil),
		)
		logger.Info("request", zap.Inline(failingLogObject{}))
		Expect(out.String()).NotTo(ContainSubstring("credential-"))
		Expect(out.String()).To(ContainSubstring(`"Error":"***"`))
	})
})

type nestedFailingLogObject struct{}

func (nestedFailingLogObject) MarshalLogObject(enc zapcore.ObjectEncoder) error {
	zap.Object("details", failingLogObject{}).AddTo(enc)
	return nil
}

var _ = Describe("Credential masking nested encoder failures", func() {
	It("protects nested encoding failure diagnostics", func() {
		var out bytes.Buffer
		logger := zap.New(
			zapcore.NewCore(
				zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
				zapcore.AddSync(&out),
				zap.InfoLevel,
			),
			logging.WithDesensitize(nil),
		)
		logger.Info("request", zap.Object("params", nestedFailingLogObject{}))
		Expect(out.String()).NotTo(ContainSubstring("credential-"))
		Expect(out.String()).To(ContainSubstring(`"detailsError":"***"`))
	})
})
