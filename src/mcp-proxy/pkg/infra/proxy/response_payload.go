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
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"mcp_proxy/pkg/util"
)

const truncatedSuffix = "...(truncated)"

// toolResponsePayload captures the upstream response of a tool call as raw bytes plus a small
// amount of metadata. Wire rendering preserves the raw bytes. Log rendering separately owns
// bounded sanitized copies, so credential masking never changes client payloads.
//
// Two presentation methods are layered on top:
//   - marshalEnvelope / marshalRawResponse: produce the wire bytes returned to MCP clients.
//   - EnvelopePreview: produces a bounded, JSON-safe preview used by audit and API logs.
type toolResponsePayload struct {
	statusCode        int
	upstreamRequestID string
	contentType       string
	rawBody           []byte
	isDeclaredJSON    bool
	logCopies         payloadLogCopies
}

func newToolResponsePayload(
	statusCode int,
	upstreamRequestID string,
	contentType string,
	rawBody []byte,
) *toolResponsePayload {
	isDeclaredJSON := isJSONContentType(contentType)
	return &toolResponsePayload{
		statusCode:        statusCode,
		upstreamRequestID: upstreamRequestID,
		contentType:       contentType,
		rawBody:           rawBody,
		isDeclaredJSON:    isDeclaredJSON,
	}
}

func isJSONContentType(contentType string) bool {
	if contentType == "" {
		return false
	}
	mediaType := strings.ToLower(strings.TrimSpace(strings.Split(contentType, ";")[0]))
	return mediaType == "application/json" || strings.HasSuffix(mediaType, "+json")
}

func isNoContentStatus(statusCode int) bool {
	return statusCode == http.StatusNoContent ||
		statusCode == http.StatusResetContent ||
		statusCode == http.StatusNotModified
}

func (p *toolResponsePayload) validateDeclaredJSONBody() error {
	if p == nil || !p.isDeclaredJSON {
		return nil
	}
	if len(p.rawBody) == 0 {
		if p.rawBody != nil && !isNoContentStatus(p.statusCode) {
			return p.invalidDeclaredJSONBodyError(fmt.Errorf("empty body"))
		}
		return nil
	}
	if json.Valid(p.rawBody) {
		return nil
	}
	return p.invalidDeclaredJSONBodyError(nil)
}

func (p *toolResponsePayload) invalidDeclaredJSONBodyError(cause error) error {
	if cause == nil {
		return fmt.Errorf("invalid JSON response body for Content-Type %q", p.contentType)
	}
	return fmt.Errorf("invalid JSON response body for Content-Type %q: %w", p.contentType, cause)
}

// bodyAsJSONValue returns a valid JSON value for the upstream body. Declared JSON is preserved
// as raw bytes; non-JSON bodies are encoded as JSON strings to match the MCP text-content contract.
func (p *toolResponsePayload) bodyAsJSONValue() (json.RawMessage, error) {
	if p == nil {
		return json.RawMessage("null"), nil
	}
	if err := p.validateDeclaredJSONBody(); err != nil {
		return nil, err
	}
	if len(p.rawBody) == 0 {
		if p.rawBody != nil && !p.isDeclaredJSON {
			return json.RawMessage(`""`), nil
		}
		return json.RawMessage("null"), nil
	}
	if p.isDeclaredJSON {
		return json.RawMessage(p.rawBody), nil
	}
	body, err := json.Marshal(string(p.rawBody))
	if err != nil {
		return nil, err
	}
	return body, nil
}

// EnvelopePreview returns an API log envelope with only its sanitized body truncated.
func (p *toolResponsePayload) EnvelopePreview(traceID, xRequestID string, limit int) string {
	p.initializeLogCopies()
	return p.logEnvelope(p.logCopies.api, p.logCopies.apiText, traceID, xRequestID, limit)
}

func (p *toolResponsePayload) auditEnvelopePreview(traceID, xRequestID string, limit int) string {
	p.initializeLogCopies()
	return p.logEnvelope(p.logCopies.audit, p.logCopies.auditText, traceID, xRequestID, limit)
}

func (p *toolResponsePayload) initializeLogCopies() {
	p.logCopies.initialize(func(s *util.LogSanitizer) string {
		if len(p.rawBody) == 0 {
			if p.rawBody != nil && !p.isDeclaredJSON {
				return `""`
			}
			return "null"
		}
		return s.JSON("response_body", p.rawBody)
	})
}

func (p *toolResponsePayload) logEnvelope(
	s *util.LogSanitizer,
	safeBody, traceID, xRequestID string,
	limit int,
) string {
	var body any = json.RawMessage(safeBody)
	if safeBody == util.HiddenLogBody {
		body = safeBody
	}

	envelope := struct {
		StatusCode   int    `json:"status_code"`
		RequestID    string `json:"request_id"`
		TraceID      string `json:"trace_id"`
		XRequestID   string `json:"x_request_id"`
		ResponseBody any    `json:"response_body"`
	}{p.statusCode, p.upstreamRequestID, traceID, xRequestID, body}
	out, err := json.Marshal(envelope)
	if err != nil {
		return util.HiddenLogBody
	}
	// Apply response-envelope JSON paths before truncating its body member.
	return previewLogEnvelope(s.JSON("response", out), limit)
}

func previewLogEnvelope(text string, limit int) string {
	if text == util.HiddenLogBody {
		return text
	}
	var envelope map[string]json.RawMessage
	if json.Unmarshal([]byte(text), &envelope) != nil {
		return util.HiddenLogBody
	}
	body := envelope["response_body"]
	if limit > 0 && len(body) > limit && string(body) != `"`+util.HiddenLogBody+`"` {
		var err error
		preview := util.JSONLogPreview(string(body), limit)
		var projected any = json.RawMessage(preview)
		if preview == util.HiddenLogBody {
			projected = preview
		}
		envelope["response_body"], err = json.Marshal(projected)
		if err != nil {
			return util.HiddenLogBody
		}
	}
	out, err := json.Marshal(envelope)
	if err != nil {
		return util.HiddenLogBody
	}
	return string(out)
}

func (p *toolResponsePayload) marshalEnvelope(traceID, xRequestID string) ([]byte, error) {
	responseBody, err := p.bodyAsJSONValue()
	if err != nil {
		return nil, err
	}
	envelope := struct {
		StatusCode   int             `json:"status_code"`
		RequestID    string          `json:"request_id"`
		TraceID      string          `json:"trace_id"`
		XRequestID   string          `json:"x_request_id"`
		ResponseBody json.RawMessage `json:"response_body"`
	}{
		StatusCode:   p.statusCode,
		RequestID:    p.upstreamRequestID,
		TraceID:      traceID,
		XRequestID:   xRequestID,
		ResponseBody: responseBody,
	}
	out, err := json.Marshal(envelope)
	if err != nil {
		if p != nil && len(p.rawBody) > 0 && p.isDeclaredJSON {
			return nil, p.invalidDeclaredJSONBodyError(err)
		}
		return nil, err
	}
	return out, nil
}

// marshalRawResponse returns the complete MCP tool response for raw_response_enabled mode.
// It does not wrap the upstream body in the normal envelope, so callers receive only the raw API
// response shape: declared JSON is returned unchanged, non-JSON bytes are encoded as a JSON
// string, explicit empty non-JSON bytes become "", and an absent body becomes null.
//
// This differs from marshalEnvelope: marshalRawResponse produces the entire response bytes returned
// to the MCP client, while marshalEnvelope embeds the value as its response_body field.
func (p *toolResponsePayload) marshalRawResponse() ([]byte, error) {
	body, err := p.bodyAsJSONValue()
	if err != nil {
		return nil, err
	}
	return []byte(body), nil
}
