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
	"errors"

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

// Check retains all accepted output cores behind a boundary that sanitizes fields.
func (r *Desensitize) Check(entry zapcore.Entry, ce *zapcore.CheckedEntry) *zapcore.CheckedEntry {
	if checked := r.core.Check(entry, nil); checked != nil {
		output := &desensitizedCheckedCore{Desensitize: r, checked: checked}
		ce = ce.AddCore(entry, output)
		output.outer = ce
	}
	return ce
}

// desensitizedCheckedCore owns the registrations for one entry, including hooks
// that register their underlying output separately during Check.
type desensitizedCheckedCore struct {
	*Desensitize
	checked *zapcore.CheckedEntry
	outer   *zapcore.CheckedEntry
}

func (r *desensitizedCheckedCore) Write(entry zapcore.Entry, fields []zapcore.Field) error {
	checked := r.checked
	// The logger adds caller/stack annotations and ErrorOutput after Check.
	checked.Entry = entry
	checked.ErrorOutput = r.outer.ErrorOutput
	// CheckedEntry.Write returns the entry to a pool; do not retain it afterward.
	r.checked, r.outer = nil, nil
	checked.Write(r.fields(fields)...)
	return nil
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
		switch field.Type {
		case zapcore.BoolType, zapcore.Complex128Type, zapcore.Complex64Type, zapcore.DurationType,
			zapcore.Float64Type, zapcore.Float32Type, zapcore.Int64Type, zapcore.Int32Type,
			zapcore.Int16Type, zapcore.Int8Type, zapcore.TimeType, zapcore.TimeFullType,
			zapcore.Uint64Type, zapcore.Uint32Type, zapcore.Uint16Type, zapcore.Uint8Type, zapcore.UintptrType:
			// Scalars cannot contain credential text, but sensitive keys still
			// apply regardless of scalar value.
			if r.sanitizer.Sensitive(field.Key) {
				out = append(out, zap.String(field.Key, util.CredentialMask))
			} else {
				out = append(out, field)
			}
			continue
		}
		var value any
		switch field.Type {
		case zapcore.StringType:
			value = field.String
		case zapcore.ErrorType:
			err, ok := field.Interface.(error)
			value = util.CredentialMask
			if ok {
				value = util.SafeLogError(err)
			}
		case zapcore.ObjectMarshalerType, zapcore.InlineMarshalerType, zapcore.ArrayMarshalerType,
			zapcore.StringerType:
			// Marshal into a disposable map, then sanitize the resulting field graph.
			encoded := zapcore.NewMapObjectEncoder()
			if field.Type == zapcore.InlineMarshalerType {
				value, ok := field.Interface.(zapcore.ObjectMarshaler)
				if !ok {
					out = append(out, zap.String("body", util.HiddenLogBody))
					continue
				}
				field.Interface = safeLogObject(value)
			}
			field.AddTo(safeLogObjectEncoder{ObjectEncoder: encoded})
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

// Mask diagnostic errors where a marshaler fails, before zap turns them into
// ordinary fields such as detailsError. Successful business fields retain their names.
func safeLogObject(value zapcore.ObjectMarshaler) zapcore.ObjectMarshaler {
	return zapcore.ObjectMarshalerFunc(func(enc zapcore.ObjectEncoder) error {
		if err := value.MarshalLogObject(safeLogObjectEncoder{ObjectEncoder: enc}); err != nil {
			return errors.New(util.CredentialMask)
		}
		return nil
	})
}

func safeLogArray(value zapcore.ArrayMarshaler) zapcore.ArrayMarshaler {
	return zapcore.ArrayMarshalerFunc(func(enc zapcore.ArrayEncoder) error {
		if err := value.MarshalLogArray(safeLogArrayEncoder{ArrayEncoder: enc}); err != nil {
			return errors.New(util.CredentialMask)
		}
		return nil
	})
}

type safeLogObjectEncoder struct{ zapcore.ObjectEncoder }

// AddObject masks failures from a nested object marshaler.
func (enc safeLogObjectEncoder) AddObject(key string, value zapcore.ObjectMarshaler) error {
	return enc.ObjectEncoder.AddObject(key, safeLogObject(value))
}

// AddArray masks failures from a nested array marshaler.
func (enc safeLogObjectEncoder) AddArray(key string, value zapcore.ArrayMarshaler) error {
	return enc.ObjectEncoder.AddArray(key, safeLogArray(value))
}

type safeLogArrayEncoder struct{ zapcore.ArrayEncoder }

// AppendObject masks failures from an object nested in an array.
func (enc safeLogArrayEncoder) AppendObject(value zapcore.ObjectMarshaler) error {
	return enc.ArrayEncoder.AppendObject(safeLogObject(value))
}

// AppendArray masks failures from an array nested in an array.
func (enc safeLogArrayEncoder) AppendArray(value zapcore.ArrayMarshaler) error {
	return enc.ArrayEncoder.AppendArray(safeLogArray(value))
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
