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
	"reflect"
	"sync"

	"mcp_proxy/pkg/config"
	"mcp_proxy/pkg/util"
)

// payloadLogCopies owns complete sanitized copies for the two log destinations.
// Initialize once per payload; identical rules share a copy. Wire bytes remain separate.
type payloadLogCopies struct {
	once      sync.Once
	api       *util.LogSanitizer
	audit     *util.LogSanitizer
	sameRules bool
	apiText   string
	auditText string
	auditBody string
}

func (c *payloadLogCopies) initialize(build func(*util.LogSanitizer) string) {
	c.once.Do(func() {
		var apiCfg, auditCfg config.DesensitizationConfig
		if config.G != nil {
			apiCfg = config.G.Logger.API.Desensitization
			auditCfg = config.G.Logger.Audit.Desensitization
		}
		c.api = util.NewLogSanitizer(apiCfg)
		c.audit = c.api
		c.sameRules = reflect.DeepEqual(apiCfg, auditCfg)
		if !c.sameRules {
			c.audit = util.NewLogSanitizer(auditCfg)
		}
		c.apiText = build(c.api)
		c.auditText = c.apiText
		if !c.sameRules {
			c.auditText = build(c.audit)
		}
	})
}

func safeLogPreview(text string, limit int, suffix string) string {
	if text == util.HiddenLogBody {
		return text
	}
	if limit >= 0 && len(text) > limit {
		return text[:limit] + suffix
	}
	return text
}

func sanitizedBodyMember(text, key string) string {
	if text == util.HiddenLogBody {
		return text
	}
	var members map[string]json.RawMessage
	if json.Unmarshal([]byte(text), &members) != nil {
		return util.HiddenLogBody
	}
	if body, exists := members[key]; exists {
		return string(body)
	}
	return "null"
}
