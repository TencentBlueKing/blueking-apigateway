/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

package logging

import (
	"fmt"
	"strings"

	"github.com/tidwall/gjson"
	"github.com/tidwall/sjson"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

const mask = "***************"

// Desensitize ...
type Desensitize struct {
	core           zapcore.Core
	sensitiveField map[string][]string
}

// With ...
func (r *Desensitize) With(fields []zapcore.Field) zapcore.Core {
	return &Desensitize{
		core:           r.core.With(fields),
		sensitiveField: r.sensitiveField,
	}
}

// Check ...
func (r *Desensitize) Check(entry zapcore.Entry, ce *zapcore.CheckedEntry) *zapcore.CheckedEntry {
	if r.Enabled(entry.Level) {
		return ce.AddCore(entry, r)
	}
	return ce
}

// Write ...
func (r *Desensitize) Write(entry zapcore.Entry, fields []zapcore.Field) error {
	for i := range fields {
		if jsonPathList, ok := r.sensitiveField[fields[i].Key]; ok {
			for _, jsonPath := range jsonPathList {
				// 进行脱敏处理
				result := gjson.Get(fields[i].String, jsonPath)
				if !result.Exists() {
					continue
				}
				if !result.IsArray() {
					maskValue := getSensitiveFieldMaskValue(result.String())
					fields[i].String, _ = sjson.Set(fields[i].String, jsonPath, maskValue)
					continue
				}
				for index, value := range result.Array() {
					fileValue := value.String()
					maskValue := getSensitiveFieldMaskValue(fileValue)
					indexJsonPath := strings.ReplaceAll(jsonPath, "#", fmt.Sprintf("%d", index))
					fields[i].String, _ = sjson.Set(fields[i].String, indexJsonPath, maskValue)
				}
			}
		}
	}
	return r.core.Write(entry, fields)
}

// Sync ...
func (r *Desensitize) Sync() error {
	return r.core.Sync()
}

// Enabled ...
func (r *Desensitize) Enabled(level zapcore.Level) bool {
	return r.core.Enabled(level)
}

// WithDesensitize ...
func WithDesensitize(paths map[string][]string) zap.Option {
	return zap.WrapCore(func(core zapcore.Core) zapcore.Core {
		return &Desensitize{
			core:           core,
			sensitiveField: paths,
		}
	})
}

func getSensitiveFieldMaskValue(fileValue string) string {
	maskValue := mask
	if len(fileValue) > 6 {
		prefix := fileValue[:3]
		suffix := fileValue[len(fileValue)-3:]
		maskValue = prefix + maskValue + suffix
	}
	return maskValue
}
