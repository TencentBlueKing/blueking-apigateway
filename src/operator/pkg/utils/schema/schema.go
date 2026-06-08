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

package schema

import (
	_ "embed"
	"strings"

	"github.com/tidwall/gjson"

	"operator/pkg/constant"
)

// IsInnerPlugin 检查插件是否为内置插件
func IsInnerPlugin(pluginName string) bool {
	return strings.HasPrefix(pluginName, "bk-")
}

//go:embed 3.13/schema.json
var rawSchemaV313 []byte

var schemaVersionMap = map[constant.APISIXVersion]gjson.Result{
	constant.APISIXVersion313: gjson.ParseBytes(rawSchemaV313),
}

// GetResourceSchema 获取资源的schema
func GetResourceSchema(version constant.APISIXVersion, name string) any {
	return schemaVersionMap[version].Get("main." + name).Value()
}

// GetMetadataPluginSchema 获取 metadata 插件类型的 schema
func GetMetadataPluginSchema(version constant.APISIXVersion, path string) any {
	// 查找 apisix 插件
	ret := schemaVersionMap[version].Get(path).Value()
	if ret != nil {
		return ret
	}
	return ret
}

// GetPluginSchema 获取插件的schema
func GetPluginSchema(version constant.APISIXVersion, name, schemaType string) any {
	var ret any
	if schemaType == "consumer" || schemaType == "consumer_schema" {
		// 需匹配常规插件和 consumer 插件，当未查询到时，继续匹配后面常规插件
		ret = schemaVersionMap[version].Get("plugins." + name + ".consumer_schema").Value()
	}
	if schemaType == "metadata" || schemaType == "metadata_schema" {
		// 只需匹配 metadata 类型的插件，根据 "plugins."+name+".metadata_schema" 路径查询 schema，可直接返回结果，无需再匹配常规插件
		return GetMetadataPluginSchema(version, "plugins."+name+".metadata_schema")
	}
	if schemaType == "stream" || schemaType == "stream_schema" {
		// 只需要匹配 stream 类型的插件，由于该类型所有插件已在 schema.json 中存在，可直接返回结果，无需再匹配常规插件
		return schemaVersionMap[version].Get("stream_plugins." + name + ".schema").Value()
	}
	// 常规插件匹配
	if ret == nil {
		ret = schemaVersionMap[version].Get("plugins." + name + ".schema").Value()
	}
	if ret != nil {
		return ret
	}

	return ret
}
