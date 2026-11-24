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

// Package logging provides bounded credential-safe JSON loggers.
package logging

import (
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/util"
)

// Desensitize sanitizes both bound and per-entry fields without mutating caller fields.
type Desensitize struct {
	core      zapcore.Core
	sanitizer *util.LogSanitizer
}

// With sanitizes fields before the underlying core stores them.
func (r *Desensitize) With(fields []zapcore.Field) zapcore.Core {
	return &Desensitize{core: r.core.With(r.fields(fields)), sanitizer: r.sanitizer}
}

// Check registers this core only when its underlying core accepts the entry.
func (r *Desensitize) Check(entry zapcore.Entry, ce *zapcore.CheckedEntry) *zapcore.CheckedEntry {
	if r.core.Check(entry, nil) != nil {
		return ce.AddCore(entry, r)
	}
	return ce
}

// Write emits only sanitized copies of structured fields.
func (r *Desensitize) Write(entry zapcore.Entry, fields []zapcore.Field) error {
	return r.core.Write(entry, r.fields(fields))
}

func (r *Desensitize) fields(fields []zapcore.Field) []zapcore.Field {
	out := make([]zapcore.Field, 0, len(fields))
	for _, field := range fields {
		if field.Type == zapcore.SkipType {
			continue
		}
		if field.Type == zapcore.NamespaceType {
			out = append(out, field)
			continue
		}
		var value any
		switch field.Type {
		case zapcore.StringType:
			value = field.String
		case zapcore.ErrorType:
			value = util.CredentialMask
		case zapcore.ObjectMarshalerType, zapcore.InlineMarshalerType, zapcore.ArrayMarshalerType,
			zapcore.StringerType:
			// Marshal into a disposable map, then sanitize the resulting field graph.
			encoded := zapcore.NewMapObjectEncoder()
			field.AddTo(encoded)
			if field.Type == zapcore.InlineMarshalerType {
				safe := r.sanitizer.Sanitize("", encoded.Fields)
				if values, ok := safe.(map[string]any); ok {
					for key, item := range values {
						out = append(out, zap.Any(key, item))
					}
				} else {
					out = append(out, zap.String("body", util.HiddenLogBody))
				}
				continue
			}
			value = encoded.Fields[field.Key]
		default:
			encoded := zapcore.NewMapObjectEncoder()
			field.AddTo(encoded)
			value = encoded.Fields[field.Key]
		}
		out = append(out, zap.Any(field.Key, r.sanitizer.Sanitize(field.Key, value)))
	}
	return out
}

// Sync flushes the underlying logger.
func (r *Desensitize) Sync() error { return r.core.Sync() }

// Enabled delegates the level filter to the underlying core.
func (r *Desensitize) Enabled(level zapcore.Level) bool { return r.core.Enabled(level) }

// WithDesensitize retains additive legacy JSON-path rules with default credential protection.
func WithDesensitize(paths map[string][]string) zap.Option {
	cfg := config.DesensitizationConfig{Enabled: true}
	for key, path := range paths {
		cfg.Fields = append(cfg.Fields, config.DesensitizationFiled{Key: key, JsonPath: path})
	}
	return withLogSanitizer(util.NewLogSanitizer(cfg))
}

func withLogSanitizer(s *util.LogSanitizer) zap.Option {
	return zap.WrapCore(func(core zapcore.Core) zapcore.Core { return &Desensitize{core: core, sanitizer: s} })
}

// APILogSanitizer returns the configured API logger rules for sanitization before preview truncation.
func APILogSanitizer() *util.LogSanitizer {
	if config.G == nil {
		return util.NewLogSanitizer(config.DesensitizationConfig{})
	}
	return util.NewLogSanitizer(config.G.Logger.API.Desensitization)
}

// AuditLogSanitizer returns the configured audit logger rules for sanitization before preview truncation.
func AuditLogSanitizer() *util.LogSanitizer {
	if config.G == nil {
		return util.NewLogSanitizer(config.DesensitizationConfig{})
	}
	return util.NewLogSanitizer(config.G.Logger.Audit.Desensitization)
}
