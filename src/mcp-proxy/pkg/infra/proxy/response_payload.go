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
	isJSON            bool
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
		isJSON:            isDeclaredJSON && json.Valid(rawBody),
	}
}

// IsSuccess reports whether the upstream returned a 2xx status code.
func (p *toolResponsePayload) IsSuccess() bool {
	return p.statusCode >= 200 && p.statusCode <= 299
}

// PickLimit returns successLimit when the upstream succeeded (2xx) and errorLimit otherwise.
// Used by log call sites to give failed calls a larger truncation budget for troubleshooting.
func (p *toolResponsePayload) PickLimit(successLimit, errorLimit int) int {
	if p.IsSuccess() {
		return successLimit
	}
	return errorLimit
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
	if p == nil || len(p.rawBody) == 0 || !p.isDeclaredJSON || p.isJSON {
		return nil
	}
	return fmt.Errorf("invalid JSON response body for Content-Type %q", p.contentType)
}

// responseBodyRawMessage returns a json.RawMessage suitable for embedding into the envelope
// sent to MCP clients. Unlike previewBodyAsRawMessage, this method does NOT truncate the body
// — it preserves full fidelity for the client. Used only by marshalEnvelope / marshalRawResponse.
func (p *toolResponsePayload) responseBodyRawMessage() (json.RawMessage, error) {
	if p == nil || len(p.rawBody) == 0 {
		return json.RawMessage("null"), nil
	}
	if err := p.validateDeclaredJSONBody(); err != nil {
		return nil, err
	}
	if p.isJSON {
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
		return json.RawMessage("null")
	}

	canEmbedRawJSON := p.isJSON && (limit <= 0 || len(p.rawBody) <= limit)
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
	return json.Marshal(envelope)
}

func (p *toolResponsePayload) marshalRawResponse() ([]byte, error) {
	if p == nil || len(p.rawBody) == 0 {
		return []byte("null"), nil
	}
	if p.isJSON {
		return p.rawBody, nil
	}
	return p.responseBodyRawMessage()
}
