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

package util

import (
	"encoding/json"
	"fmt"
	"net/url"
	"reflect"
	"strconv"
	"strings"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/tidwall/gjson"
	"github.com/tidwall/sjson"

	"mcp_proxy/pkg/config"
)

const (
	// CredentialMask replaces an entire nonempty credential value in logs.
	CredentialMask = "***"
	// HiddenLogBody replaces a body that cannot be reliably sanitized.
	HiddenLogBody    = "正文已屏蔽：截断或格式未知，无法可靠脱敏"
	maxLogInputBytes = 1 << 20
	maxLogDepth      = 32
	maxLogDecodes    = 4
	maxLogNodes      = 10000
)

// These match Dashboard access-log exact and partial defaults, plus HTTP credentials.
var defaultSensitiveKeys = strings.Fields(`skey openkey auth_token access_token bk_token bk_ticket
 oa_ticket app_secret signature bk_nonce bk_timestamp bk_app_secret bk_signature token
 authorization proxy-authorization x-bkapi-authorization x-bkapi-jwt cookie set-cookie
 refresh_token client_secret inner_jwt`)
var partialSensitiveKeys = strings.Fields(`password secret passwd api_key apikey credentials mysql_pwd stripetoken`)

// LogSanitizer applies credential and legacy path rules only to disposable log copies.
type LogSanitizer struct {
	keys  map[string]struct{}
	paths map[string][]string
}

// NewLogSanitizer constructs additive rules; defaults cannot be disabled.
func NewLogSanitizer(cfg config.DesensitizationConfig) *LogSanitizer {
	s := &LogSanitizer{keys: make(map[string]struct{}), paths: make(map[string][]string)}
	for _, group := range [][]string{defaultSensitiveKeys, cfg.SensitiveKeys, cfg.SensitiveHeaders} {
		for _, key := range group {
			s.keys[strings.ToLower(key)] = struct{}{}
		}
	}
	if cfg.Enabled {
		for _, field := range cfg.Fields {
			key := strings.ToLower(field.Key)
			s.paths[key] = append(s.paths[key], field.JsonPath...)
		}
	}
	return s
}

// Sensitive identifies an exact configured/default key or a default partial key.
func (s *LogSanitizer) Sensitive(key string) bool {
	key = strings.ToLower(key)
	if _, ok := s.keys[key]; ok {
		return true
	}
	for _, part := range partialSensitiveKeys {
		if strings.Contains(key, part) {
			return true
		}
	}
	return false
}

type logBudget struct{ nodes, bytes int }

func newLogBudget() *logBudget { return &logBudget{maxLogNodes, maxLogInputBytes} }
func (b *logBudget) take(size, depth int) bool {
	b.nodes--
	b.bytes -= size
	return depth <= maxLogDepth && b.nodes >= 0 && b.bytes >= 0
}

func emptyLogValue(v reflect.Value) bool {
	for v.IsValid() && (v.Kind() == reflect.Interface || v.Kind() == reflect.Pointer) {
		if v.IsNil() {
			return true
		}
		v = v.Elem()
	}
	if !v.IsValid() {
		return true
	}
	switch v.Kind() {
	case reflect.String, reflect.Map, reflect.Slice, reflect.Array:
		return v.Len() == 0
	}
	return false
}

// Sanitize returns a bounded copy, preserving null/empty values and HTTP paths.
func (s *LogSanitizer) Sanitize(key string, value any) any {
	result, ok := s.field(key, reflect.ValueOf(value), 0, 0, newLogBudget())
	if !ok {
		return HiddenLogBody
	}
	return result
}

// JSON sanitizes complete serialized input before a caller applies its preview limit.
func (s *LogSanitizer) JSON(key string, raw []byte) string {
	if len(raw) > maxLogInputBytes {
		return HiddenLogBody
	}
	result := s.Sanitize(key, string(raw))
	if text, ok := result.(string); ok {
		return text
	}
	out, err := json.Marshal(result)
	if err != nil {
		return HiddenLogBody
	}
	return string(out)
}

// Preview sanitizes first, then truncates only the resulting log copy.
func (s *LogSanitizer) Preview(key string, raw []byte, limit int, suffix string) string {
	text := s.JSON(key, raw)
	if text == HiddenLogBody {
		return text
	}
	if limit >= 0 && len(text) > limit {
		return text[:limit] + suffix
	}
	return text
}

func bodyLogKey(key string) bool {
	switch strings.ToLower(key) {
	case "body", "body_param", "request_body", "response_body":
		return true
	}
	return false
}

func payloadLogKey(key string) bool {
	switch strings.ToLower(key) {
	case "params", "arguments", "request", "response", "result", "query", "query_param",
		"header", "headers", "header_param", "path_param":
		return true
	}
	return bodyLogKey(key)
}

func (s *LogSanitizer) field(key string, v reflect.Value, depth, decodes int, b *logBudget) (any, bool) {
	if s.Sensitive(key) {
		if emptyLogValue(v) {
			return s.walk(v, depth, decodes, b)
		}
		return CredentialMask, b.take(len(key), depth)
	}
	if strings.EqualFold(key, "error") || strings.HasSuffix(key, "Error") || strings.EqualFold(key, "panic") {
		if emptyLogValue(v) {
			return s.walk(v, depth, decodes, b)
		}
		return CredentialMask, true
	}
	if bodyLogKey(key) {
		saved := *b
		result, ok := s.payload(key, v, depth, decodes, b)
		// A bad embedded body never destroys its surrounding response envelope.
		if !ok {
			*b = saved
			return HiddenLogBody, b.take(len(HiddenLogBody), min(depth, maxLogDepth))
		}
		return result, true
	}
	if payloadLogKey(key) || len(s.paths[strings.ToLower(key)]) > 0 {
		return s.payload(key, v, depth, decodes, b)
	}
	if strings.EqualFold(key, "path") {
		if v.IsValid() && v.Kind() == reflect.String && strings.HasPrefix(v.String(), "/") {
			return v.String(), b.take(len(v.String()), depth)
		}
		return s.payload(key, v, depth, decodes, b)
	}
	return s.walk(v, depth, decodes, b)
}

func unwrapLogValue(v reflect.Value) reflect.Value {
	for v.IsValid() && (v.Kind() == reflect.Interface || v.Kind() == reflect.Pointer) {
		if v.IsNil() {
			return reflect.Value{}
		}
		v = v.Elem()
	}
	return v
}

func (s *LogSanitizer) walk(v reflect.Value, depth, decodes int, b *logBudget) (any, bool) {
	v = unwrapLogValue(v)
	if !b.take(0, depth) {
		return nil, false
	}
	if !v.IsValid() {
		return nil, true
	}
	if v.Type() == reflect.TypeFor[json.Number]() {
		return v.Interface(), b.take(v.Len(), depth)
	}
	switch v.Kind() {
	case reflect.Map:
		if v.IsNil() {
			return nil, true
		}
		if v.Type().Key().Kind() != reflect.String || v.Len() > b.nodes {
			return nil, false
		}
		out := make(map[string]any, v.Len())
		it := v.MapRange()
		for it.Next() {
			key := it.Key().String()
			if !b.take(len(key), depth) {
				return nil, false
			}
			fieldKey := key
			if key == "text" && isTextLogContent(v) {
				fieldKey = "body"
			}
			item, ok := s.field(fieldKey, unwrapLogValue(it.Value()), depth+1, decodes, b)
			if !ok {
				return nil, false
			}
			out[key] = item
		}
		return out, true
	case reflect.Slice, reflect.Array:
		if v.Kind() == reflect.Slice && v.IsNil() {
			return nil, true
		}
		if v.Type() == reflect.TypeFor[json.RawMessage]() {
			return s.payload("body", v, depth, decodes, b)
		}
		if v.Len() > b.nodes {
			return nil, false
		}
		out := make([]any, v.Len())
		for i := range out {
			item, ok := s.walk(v.Index(i), depth+1, decodes, b)
			if !ok {
				return nil, false
			}
			out[i] = item
		}
		return out, true
	case reflect.Struct:
		return s.walkStruct(v, depth, decodes, b)
	case reflect.String:
		text := v.String()
		// Structured values embedded in header/query/path strings also need recursion.
		trimmed := strings.TrimSpace(text)
		if strings.HasPrefix(trimmed, "{") || strings.HasPrefix(trimmed, "[") {
			return s.payload("body", v, depth, decodes, b)
		}
		return text, b.take(len(text), depth)
	case reflect.Bool:
		return v.Bool(), true
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return v.Int(), true
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		return v.Uint(), true
	case reflect.Float32, reflect.Float64:
		return v.Float(), true
	}
	return nil, false
}

func (s *LogSanitizer) walkStruct(v reflect.Value, depth, decodes int, b *logBudget) (any, bool) {
	if content, ok := reflect.TypeAssert[mcp.TextContent](v); ok {
		fields := map[string]any{"type": "text", "text": content.Text}
		if content.Meta != nil {
			fields["_meta"] = content.Meta
		}
		if content.Annotations != nil {
			fields["annotations"] = content.Annotations
		}
		return s.walk(reflect.ValueOf(fields), depth, decodes, b)
	}
	out := make(map[string]any)
	for i := range v.NumField() {
		f := v.Type().Field(i)
		if !f.IsExported() {
			continue
		}
		tag := strings.Split(f.Tag.Get("json"), ",")
		key := tag[0]
		if key == "-" {
			continue
		}
		if key == "" {
			key = f.Name
		}
		if len(tag) > 1 && strings.Contains(f.Tag.Get("json"), "omitempty") && v.Field(i).IsZero() {
			continue
		}
		fieldKey := key
		item, ok := s.field(fieldKey, unwrapLogValue(v.Field(i)), depth+1, decodes, b)
		if !ok {
			return nil, false
		}
		out[key] = item
	}
	return out, true
}

func (s *LogSanitizer) payload(key string, v reflect.Value, depth, decodes int, b *logBudget) (any, bool) {
	v = unwrapLogValue(v)
	if !v.IsValid() {
		return nil, true
	}
	var text string
	switch {
	case v.Kind() == reflect.String:
		text = v.String()
	case v.Kind() == reflect.Slice && v.Type().Elem().Kind() == reflect.Uint8:
		if v.Len() > maxLogInputBytes {
			return nil, false
		}
		text = string(v.Bytes())
	default:
		result, ok := s.walk(v, depth, decodes, b)
		if !ok {
			return nil, false
		}
		return s.customPaths(key, result)
	}
	if text == "" || text == CredentialMask || text == HiddenLogBody || text == `""` {
		return text, true
	}
	if len(text) > maxLogInputBytes || decodes >= maxLogDecodes || !b.take(len(text), depth) {
		return nil, false
	}
	var parsed any
	decoder := json.NewDecoder(strings.NewReader(text))
	decoder.UseNumber()
	if !json.Valid([]byte(text)) || decoder.Decode(&parsed) != nil {
		if allowLogForm(key) && looksLikeLogForm(text) {
			return s.form(text, depth, decodes, b)
		}
		return nil, false
	}
	var result any
	var ok bool
	if parsed != nil {
		switch parsed.(type) {
		case map[string]any, []any, string:
		default:
			return nil, false
		}
	}
	if _, isString := parsed.(string); isString {
		result, ok = s.payload(key, reflect.ValueOf(parsed), depth+1, decodes+1, b)
	} else {
		result, ok = s.walk(reflect.ValueOf(parsed), depth+1, decodes+1, b)
	}
	if !ok {
		return nil, false
	}
	result, ok = s.customPaths(key, result)
	if !ok {
		return nil, false
	}
	out, err := json.Marshal(result)
	if err != nil {
		return nil, false
	}
	return string(out), true
}

func allowLogForm(key string) bool {
	switch strings.ToLower(key) {
	case "body", "body_param", "request_body", "params", "query", "query_param":
		return true
	}
	return false
}

func (s *LogSanitizer) form(text string, depth, decodes int, b *logBudget) (any, bool) {
	parts := strings.Split(text, "&")
	if len(parts) > b.nodes {
		return nil, false
	}
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		if part == "" {
			continue
		}
		key, value, found := strings.Cut(part, "=")
		if !found {
			return nil, false
		}
		key, err := url.QueryUnescape(key)
		if err != nil {
			return nil, false
		}
		value, err = url.QueryUnescape(value)
		if err != nil {
			return nil, false
		}
		result, ok := s.field(key, reflect.ValueOf(value), depth+1, decodes, b)
		if !ok {
			return nil, false
		}
		str, ok := result.(string)
		if !ok {
			return nil, false
		}
		out = append(out, url.QueryEscape(key)+"="+url.QueryEscape(str))
	}
	return strings.Join(out, "&"), true
}

func (s *LogSanitizer) customPaths(key string, value any) (any, bool) {
	paths := s.paths[strings.ToLower(key)]
	if len(paths) == 0 {
		return value, true
	}
	raw, err := json.Marshal(value)
	if err != nil {
		return nil, false
	}
	text := string(raw)
	budget := newLogBudget()
	for _, path := range paths {
		path = strings.TrimPrefix(strings.TrimPrefix(path, "$"), ".")
		text, err = maskLogPath(text, path, budget, 0)
		if err != nil {
			return nil, false
		}
	}
	decoder := json.NewDecoder(strings.NewReader(text))
	decoder.UseNumber()
	var out any
	if err := decoder.Decode(&out); err != nil {
		return nil, false
	}
	return out, true
}

func maskLogPath(text, path string, budget *logBudget, depth int) (string, error) {
	if !budget.take(len(text)+len(path), depth) {
		return "", fmt.Errorf("log path processing budget exceeded")
	}
	if before, after, found := strings.Cut(path, "#"); found {
		array := gjson.Get(text, strings.TrimSuffix(before, "."))
		for i := range array.Array() {
			var err error
			text, err = maskLogPath(text, before+strconv.Itoa(i)+after, budget, depth+1)
			if err != nil {
				return "", err
			}
		}
		return text, nil
	}
	result := gjson.Get(text, path)
	if !result.Exists() || result.Type == gjson.Null || result.Raw == `""` || result.Raw == "[]" ||
		result.Raw == "{}" {
		return text, nil
	}
	return sjson.Set(text, path, CredentialMask)
}

func looksLikeLogForm(text string) bool {
	trimmed := strings.TrimSpace(text)
	return strings.Contains(text, "=") && !strings.ContainsAny(text, "\r\n") &&
		!strings.HasPrefix(trimmed, "{") && !strings.HasPrefix(trimmed, "[") && !strings.HasPrefix(trimmed, `"`)
}

func isTextLogContent(v reflect.Value) bool {
	item := unwrapLogValue(v.MapIndex(reflect.ValueOf("type").Convert(v.Type().Key())))
	return item.IsValid() && item.Kind() == reflect.String && item.String() == "text"
}
