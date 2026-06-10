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
	"strings"
)

const truncatedSuffix = "...(truncated)"

type toolResponsePayload struct {
	statusCode        int
	upstreamRequestID string
	contentType       string
	rawBody           []byte
	isJSON            bool
	truncatedPreview  string
}

func newToolResponsePayload(
	statusCode int,
	upstreamRequestID string,
	contentType string,
	rawBody []byte,
	previewLimit int,
) *toolResponsePayload {
	payload := &toolResponsePayload{
		statusCode:        statusCode,
		upstreamRequestID: upstreamRequestID,
		contentType:       contentType,
		rawBody:           rawBody,
		isJSON:            isJSONContentType(contentType) && json.Valid(rawBody),
	}
	payload.truncatedPreview = truncateBytesForLog(rawBody, previewLimit)
	return payload
}

func isJSONContentType(contentType string) bool {
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

func (p *toolResponsePayload) responseBodyRawMessage() json.RawMessage {
	if p == nil || len(p.rawBody) == 0 {
		return json.RawMessage("null")
	}
	if p.isJSON {
		return json.RawMessage(p.rawBody)
	}
	body, err := json.Marshal(string(p.rawBody))
	if err != nil {
		return json.RawMessage("null")
	}
	return body
}

func (p *toolResponsePayload) marshalEnvelope(traceID, xRequestID string) ([]byte, error) {
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
		ResponseBody: p.responseBodyRawMessage(),
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
	return p.responseBodyRawMessage(), nil
}
