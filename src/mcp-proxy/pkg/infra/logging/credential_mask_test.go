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
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Credential masking log boundary", func() {
	It("preserves hooked output registrations with safe bound and per-entry fields", func() {
		dir := GinkgoT().TempDir()
		events := []recordedLogEvent{}
		level := zap.NewAtomicLevelAt(zap.ErrorLevel)
		hooks := 0
		output := &recordingLogCore{LevelEnabler: level, events: &events}
		logger := logging.NewZapJSONLogger(&config.LogConfig{
			Level: "info", Writer: "file", Settings: map[string]string{"path": dir, "name": "hooks.log"},
		}, []zap.Option{
			zap.WrapCore(func(core zapcore.Core) zapcore.Core {
				return zapcore.NewTee(zapcore.RegisterHooks(output, func(zapcore.Entry) error {
					hooks++
					return nil
				}), core)
			}),
			zap.AddCaller(),
		})
		bound := []zap.Field{
			zap.Any("headers", map[string]any{"Authorization": "credential-bound", "Accept": "application/json"}),
			zap.String("request_id", "req-hook"),
		}
		fields := []zap.Field{
			zap.String("body", `{"token":"credential-entry","name":"demo"}`),
			zap.String("client_secret", "credential-scalar"),
		}
		logger = logger.With(bound...)
		logger.Info("ordinary output", fields...)
		Expect(events).To(BeEmpty())
		Expect(hooks).To(BeZero())
		checked := logger.Check(zap.ErrorLevel, "hooked output")
		Expect(checked).NotTo(BeNil())
		// Acceptance is decided during Check, even if the level changes before Write.
		level.SetLevel(zap.FatalLevel)
		checked.Write(fields...)
		Expect(logger.Sync()).To(Succeed())
		Expect(events).To(HaveLen(1))
		Expect(hooks).To(Equal(1))
		Expect(events[0].entry.Message).To(Equal("hooked output"))
		Expect(events[0].entry.Caller.Defined).To(BeTrue())
		encoded := zapcore.NewMapObjectEncoder()
		for _, field := range events[0].fields {
			field.AddTo(encoded)
		}
		Expect(encoded.Fields).To(HaveKeyWithValue("headers", map[string]any{
			"Authorization": "***", "Accept": "application/json",
		}))
		Expect(encoded.Fields).To(HaveKeyWithValue("request_id", "req-hook"))
		Expect(encoded.Fields).To(HaveKeyWithValue("client_secret", "***"))
		var body map[string]any
		Expect(json.Unmarshal([]byte(encoded.Fields["body"].(string)), &body)).To(Succeed())
		Expect(body).To(Equal(map[string]any{"token": "***", "name": "demo"}))
		out, err := os.ReadFile(filepath.Join(dir, "hooks.log"))
		Expect(err).NotTo(HaveOccurred())
		Expect(string(out)).NotTo(ContainSubstring("credential-"))
		Expect(strings.Count(string(out), `"msg":"ordinary output"`)).To(Equal(1))
		Expect(strings.Count(string(out), `"msg":"hooked output"`)).To(Equal(1))
		Expect(bound[0].Interface).To(Equal(map[string]any{
			"Authorization": "credential-bound", "Accept": "application/json",
		}))
		Expect(fields[0].String).To(ContainSubstring("credential-entry"))
		Expect(fields[1].String).To(Equal("credential-scalar"))
	})

	It("keeps production duration and time encoding for bound and per-entry scalars", func() {
		dir := GinkgoT().TempDir()
		logger := logging.NewZapJSONLogger(&config.LogConfig{
			Level: "info", Writer: "file", Settings: map[string]string{"path": dir, "name": "scalars.log"},
		}, nil)
		when := time.Date(2026, time.November, 24, 12, 34, 56, 123456789, time.FixedZone("offset", 8*60*60))
		early := time.Date(1600, time.January, 2, 3, 4, 5, 0, time.UTC)
		logger.With(zap.Duration("bound_duration", 1500*time.Millisecond), zap.Time("bound_time", when)).Info(
			"scalar encoding",
			zap.Duration("duration", 1500*time.Millisecond),
			zap.Time("time", when),
			zap.Time("early_time", early),
			zap.Duration("secret_duration", 0),
			zap.Time("token", time.Time{}),
			zap.Bool("password", false),
			zap.Int("api_key", 0),
		)
		Expect(logger.Sync()).To(Succeed())
		out, err := os.ReadFile(filepath.Join(dir, "scalars.log"))
		Expect(err).NotTo(HaveOccurred())
		var entry map[string]any
		Expect(json.Unmarshal(out, &entry)).To(Succeed())
		Expect(entry).To(HaveKeyWithValue("duration", 1.5))
		Expect(entry).To(HaveKeyWithValue("bound_duration", 1.5))
		Expect(entry).To(HaveKeyWithValue("time", when.Format(time.RFC3339Nano)))
		Expect(entry).To(HaveKeyWithValue("bound_time", when.Format(time.RFC3339Nano)))
		Expect(entry).To(HaveKeyWithValue("early_time", early.Format(time.RFC3339Nano)))
		for _, key := range []string{"secret_duration", "token", "password", "api_key"} {
			Expect(entry).To(HaveKeyWithValue(key, "***"))
		}
	})

	It("keeps safe scalar field types at the output core", func() {
		events := []recordedLogEvent{}
		logger := zap.New(&recordingLogCore{LevelEnabler: zap.InfoLevel, events: &events},
			logging.WithDesensitize(nil))
		fields := []zap.Field{
			zap.Bool("bool", false), zap.Int8("int8", 8), zap.Int16("int16", 16), zap.Int32("int32", 32),
			zap.Int64("int64", 64), zap.Uint8("uint8", 8), zap.Uint16("uint16", 16), zap.Uint32("uint32", 32),
			zap.Uint64("uint64", 64), zap.Uintptr("uintptr", 1), zap.Float32("float32", 1.5),
			zap.Float64("float64", 1.5), zap.Complex64("complex64", 1+2i), zap.Complex128("complex128", 1+2i),
			zap.Duration("duration", time.Second), zap.Time("time", time.Now()),
			zap.Time("early_time", time.Date(1600, time.January, 1, 0, 0, 0, 0, time.UTC)),
		}
		logger.Info("safe scalars", fields...)
		Expect(events).To(HaveLen(1))
		Expect(events[0].fields).To(Equal(fields))
	})

	It("preserves safe error classifications without arbitrary error messages", func() {
		var out bytes.Buffer
		logger := zap.New(zapcore.NewCore(zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
			zapcore.AddSync(&out), zap.InfoLevel), logging.WithDesensitize(nil))
		logger.With(zap.NamedError("bound_failure", context.DeadlineExceeded)).Error("failure",
			zap.Error(context.Canceled),
			zap.NamedError("failure", errors.New("credential-error")),
			zap.NamedError("token", context.Canceled),
			zap.Bool("isError", true),
		)
		Expect(out.String()).NotTo(ContainSubstring("credential-"))
		var entry map[string]any
		Expect(json.Unmarshal(out.Bytes(), &entry)).To(Succeed())
		for key, category := range map[string]string{
			"bound_failure": "deadline_exceeded", "error": "canceled", "failure": "error_details_hidden",
		} {
			var details map[string]any
			Expect(json.Unmarshal([]byte(entry[key].(string)), &details)).To(Succeed())
			Expect(details).To(Equal(map[string]any{"category": category}))
		}
		Expect(entry).To(HaveKeyWithValue("token", "***"))
		Expect(entry).To(HaveKeyWithValue("isError", true))
	})

	It("does not replace a shared field slice when sanitizing one tee branch", func() {
		safeEvents, originalEvents := []recordedLogEvent{}, []recordedLogEvent{}
		safeLogger := zap.New(&recordingLogCore{LevelEnabler: zap.InfoLevel, events: &safeEvents},
			logging.WithDesensitize(nil))
		logger := zap.New(zapcore.NewTee(safeLogger.Core(),
			&recordingLogCore{LevelEnabler: zap.InfoLevel, events: &originalEvents}))
		fields := []zap.Field{zap.String("token", "credential-shared")}
		logger.Info("shared slice", fields...)
		Expect(safeEvents).To(HaveLen(1))
		Expect(originalEvents).To(HaveLen(1))
		Expect(safeEvents[0].fields).To(Equal([]zap.Field{zap.String("token", "***")}))
		Expect(originalEvents[0].fields).To(Equal(fields))
		Expect(fields[0].String).To(Equal("credential-shared"))
	})

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

// recordingLogCore models a Sentry-shaped output that stores bound fields and
// registers its own Write during Check; RegisterHooks supplies the separate hook.
type recordingLogCore struct {
	zapcore.LevelEnabler
	events *[]recordedLogEvent
	bound  []zap.Field
}

type recordedLogEvent struct {
	entry  zapcore.Entry
	fields []zap.Field
}

func (c *recordingLogCore) With(fields []zap.Field) zapcore.Core {
	clone := *c
	clone.bound = append(append([]zap.Field(nil), c.bound...), fields...)
	return &clone
}

func (c *recordingLogCore) Check(entry zapcore.Entry, checked *zapcore.CheckedEntry) *zapcore.CheckedEntry {
	if c.Enabled(entry.Level) {
		return checked.AddCore(entry, c)
	}
	return checked
}

func (c *recordingLogCore) Write(entry zapcore.Entry, fields []zap.Field) error {
	*c.events = append(*c.events, recordedLogEvent{
		entry: entry, fields: append(append([]zap.Field(nil), c.bound...), fields...),
	})
	return nil
}

func (*recordingLogCore) Sync() error { return nil }

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

	It("protects nested array encoding diagnostics and preserves business Error fields", func() {
		var out bytes.Buffer
		logger := zap.New(zapcore.NewCore(zapcore.NewJSONEncoder(zap.NewProductionEncoderConfig()),
			zapcore.AddSync(&out), zap.InfoLevel), logging.WithDesensitize(nil))
		value := zapcore.ArrayMarshalerFunc(func(enc zapcore.ArrayEncoder) error {
			return enc.AppendObject(zapcore.ObjectMarshalerFunc(func(enc zapcore.ObjectEncoder) error {
				enc.AddBool("isError", true)
				enc.AddString("validationError", "required")
				zap.Object("details", failingLogObject{}).AddTo(enc)
				zap.Array("rows", zapcore.ArrayMarshalerFunc(func(enc zapcore.ArrayEncoder) error {
					enc.AppendInt(1)
					return errors.New("credential-array-error")
				})).AddTo(enc)
				return nil
			}))
		})
		logger.Info("request", zap.Array("params", value))
		Expect(out.String()).NotTo(ContainSubstring("credential-"))
		Expect(out.String()).To(ContainSubstring(`"detailsError":"***"`))
		Expect(out.String()).To(ContainSubstring(`"rowsError":"***"`))
		Expect(out.String()).To(ContainSubstring(`"isError":true`))
		Expect(out.String()).To(ContainSubstring(`"validationError":"required"`))
	})
})
