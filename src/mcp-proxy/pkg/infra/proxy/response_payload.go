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
	"strings"
)

const truncatedSuffix = "...(truncated)"

// toolResponsePayload captures the upstream response of a tool call as raw bytes plus a small
// amount of metadata. It is intentionally allocation-light: the raw body is never decoded into
// a Go object graph, so this type stays O(rawBody) in memory regardless of payload shape.
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
	return strings.Contains(strings.ToLower(contentType), "application/json")
}

func truncateBytesForLog(body []byte, limit int) string {
	if limit <= 0 || len(body) == 0 {
		return ""
	}
	if len(body) <= limit {
		return string(body)
	}
	return string(body[:limit]) + truncatedSuffix
}

func (p *toolResponsePayload) validateDeclaredJSONBody() error {
	if p == nil || len(p.rawBody) == 0 || !p.isDeclaredJSON {
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

// responseBodyRawMessage returns the response_body field value for the normal envelope response.
// It preserves the upstream body without truncation because marshalEnvelope embeds this value into
// a larger JSON object together with status_code, request_id, trace_id, and x_request_id.
//
// This differs from marshalRawResponse: responseBodyRawMessage returns only one JSON field value
// for an envelope, while marshalRawResponse returns the whole MCP tool response when
// raw_response_enabled is on.
func (p *toolResponsePayload) responseBodyRawMessage() (json.RawMessage, error) {
	if p == nil {
		return json.RawMessage("null"), nil
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

// previewBodyAsRawMessage returns a json.RawMessage that is always valid JSON, used as the
// response_body field of EnvelopePreview. Decision table:
//
//	scenario                                | output form              | notes
//	----------------------------------------|--------------------------|---------------------------
//	empty body                              | "null"                   | e.g. 204 No Content
//	valid JSON body that fits within limit  | raw JSON object/array    | matches client envelope
//	valid JSON body that needs truncation   | JSON string (truncated)  | truncation breaks JSON
//	non-JSON body (text/html, text/plain)   | JSON string              | content preserved verbatim
//	invalid declared JSON body             | JSON string              | preview only; wire path returns error
//	binary body (invalid UTF-8)             | JSON string with U+FFFD  | json.Marshal stdlib behavior
//
// Memory: O(min(len(rawBody), limit)) — independent of full rawBody size.
func (p *toolResponsePayload) previewBodyAsRawMessage(limit int) json.RawMessage {
	if len(p.rawBody) == 0 {
		if p.rawBody != nil && !p.isDeclaredJSON {
			return json.RawMessage(`""`)
		}
		return json.RawMessage("null")
	}

	canEmbedRawJSON := p.isDeclaredJSON && (limit <= 0 || len(p.rawBody) <= limit) && json.Valid(p.rawBody)
	if canEmbedRawJSON {
		return json.RawMessage(p.rawBody)
	}

	truncated := truncateBytesForLog(p.rawBody, limit)
	encoded, err := json.Marshal(truncated)
	if err != nil {
		// Unreachable: json.Marshal on a Go string cannot fail.
		return json.RawMessage("null")
	}
	return encoded
}

// EnvelopePreview returns a JSON string preview of the response envelope for log emission.
// The envelope shape matches what is sent to MCP clients (status_code, request_id, trace_id,
// x_request_id, response_body), so log readers can correlate audit entries with what the
// client actually saw. The response_body is bounded by `limit` so large upstream payloads
// do not blow up log storage.
//
// Returns an empty string if envelope marshaling unexpectedly fails.
func (p *toolResponsePayload) EnvelopePreview(traceID, xRequestID string, limit int) string {
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
		ResponseBody: p.previewBodyAsRawMessage(limit),
	}
	out, err := json.Marshal(envelope)
	if err != nil {
		return ""
	}
	return string(out)
}

func (p *toolResponsePayload) marshalEnvelope(traceID, xRequestID string) ([]byte, error) {
	responseBody, err := p.responseBodyRawMessage()
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
// This differs from responseBodyRawMessage: marshalRawResponse produces the entire response bytes
// returned to the MCP client, while responseBodyRawMessage produces only the response_body value
// embedded by marshalEnvelope.
func (p *toolResponsePayload) marshalRawResponse() ([]byte, error) {
	if p == nil {
		return []byte("null"), nil
	}
	if len(p.rawBody) == 0 {
		if p.rawBody != nil && !p.isDeclaredJSON {
			return []byte(`""`), nil
		}
		return []byte("null"), nil
	}
	if err := p.validateDeclaredJSONBody(); err != nil {
		return nil, err
	}
	if p.isDeclaredJSON {
		return p.rawBody, nil
	}
	body, err := json.Marshal(string(p.rawBody))
	if err != nil {
		return nil, err
	}
	return body, nil
}
