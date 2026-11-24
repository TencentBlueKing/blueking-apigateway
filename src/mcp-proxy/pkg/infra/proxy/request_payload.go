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
	"bytes"
	"encoding/json"
	"sync"

	"mcp_proxy/pkg/util"
)

// toolRequestPayload owns the canonical JSON bytes for one tools/call request.
// The bytes are reused for request decoding, logs, and metrics instead of marshaling
// CallToolParamsRaw.Arguments independently at each observation point.
type toolRequestPayload struct {
	rawArguments     []byte
	argumentsPresent bool
	logCopies        payloadLogCopies
	bodyPreviewOnce  sync.Once
}

func newToolRequestPayload(arguments json.RawMessage) (*toolRequestPayload, error) {
	rawArguments, err := json.Marshal(arguments)
	if err != nil {
		return nil, err
	}
	return &toolRequestPayload{
		rawArguments:     rawArguments,
		argumentsPresent: arguments != nil,
	}, nil
}

func (p *toolRequestPayload) decodeHandlerRequest() (*HandlerRequest, error) {
	var handlerRequest HandlerRequest
	decoder := json.NewDecoder(bytes.NewReader(p.rawArguments))
	decoder.UseNumber()
	if err := decoder.Decode(&handlerRequest); err != nil {
		return nil, err
	}
	return &handlerRequest, nil
}

func (p *toolRequestPayload) auditPreview(limit int) string {
	p.initializeLogCopies()
	return safeLogPreview(p.logCopies.auditText, limit, truncatedSuffix)
}

func (p *toolRequestPayload) bodyAuditPreview(limit int) string {
	p.initializeLogCopies()
	p.bodyPreviewOnce.Do(func() {
		body := sanitizedBodyMember(p.logCopies.auditText, "body_param")
		p.logCopies.auditBody = p.logCopies.audit.JSON("body", []byte(body))
	})
	return safeLogPreview(p.logCopies.auditBody, limit, truncatedSuffix)
}

func (p *toolRequestPayload) initializeLogCopies() {
	p.logCopies.initialize(func(s *util.LogSanitizer) string { return s.JSON("params", p.rawArguments) })
}

func (p *toolRequestPayload) auditSize() int64 {
	return int64(len(p.rawArguments))
}

func (p *toolRequestPayload) metricSize() int64 {
	if !p.argumentsPresent {
		return 0
	}
	return int64(len(p.rawArguments))
}

func (p *toolRequestPayload) apiLogPreview(limit int) (string, int64) {
	if !p.argumentsPresent {
		return "", 0
	}
	p.initializeLogCopies()
	return safeLogPreview(p.logCopies.apiText, limit, ""), int64(len(p.rawArguments))
}
