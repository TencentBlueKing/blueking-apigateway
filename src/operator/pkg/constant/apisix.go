/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

package constant

import "time"

// ApigwStageResourcePrefixFormat ...
// example: /{prefix}/{self.api_version}/gateway/{gateway_name}/{stage_name}/route/bk-default.default.-1
const ApigwStageResourcePrefixFormat = "%s/%s/gateway/%s/%s/"

// ApigwGlobalResourcePrefixFormat ...
// example: /{prefix}/{self.api_version}/global/plugin_metadata/bk-concurrency-limit
const ApigwGlobalResourcePrefixFormat = "%s/%s/global/"

// GlobalResourceKey ...
const GlobalResourceKey = "global_resource"

// APISIXResource ...
type APISIXResource string

// Route ...
const (
	Route          APISIXResource = "route"
	Service        APISIXResource = "service"
	Upstream       APISIXResource = "upstream"
	PluginConfig   APISIXResource = "plugin_config"
	PluginMetadata APISIXResource = "plugin_metadata"
	Consumer       APISIXResource = "consumer"
	ConsumerGroup  APISIXResource = "consumer_group"
	GlobalRule     APISIXResource = "global_rule"
	Proto          APISIXResource = "proto"
	SSL            APISIXResource = "ssl"
	StreamRoute    APISIXResource = "stream_route"
	BkRelease      APISIXResource = "_bk_release"
)

var SupportEventResourceTypeMap = map[APISIXResource]bool{
	Route:          true,
	Service:        true,
	PluginMetadata: true,
	BkRelease:      true,
}

var SupportResourceTypeMap = map[APISIXResource]bool{
	Route:          true,
	Service:        true,
	SSL:            true,
	PluginMetadata: true,
	Upstream:       false,
	PluginConfig:   false,
	Consumer:       false,
	ConsumerGroup:  false,
	GlobalRule:     false,
	Proto:          false,
	StreamRoute:    false,
}

// ResourceTypeList ...
var ResourceTypeList = []APISIXResource{
	Route,
	Service,
	Upstream,
	PluginConfig,
	PluginMetadata,
	Consumer,
	ConsumerGroup,
	GlobalRule,
	Proto,
	SSL,
	StreamRoute,
}

// PluginsMustResourceMap 必须要配置插件的资源
var PluginsMustResourceMap = map[APISIXResource]bool{
	PluginConfig:   true,
	PluginMetadata: true,
	ConsumerGroup:  true,
	GlobalRule:     true,
}

// APISIXVersion ...
type APISIXVersion string

// APISIXVersion313 ...
const (
	APISIXVersion313 APISIXVersion = "3.13.X"
)

func (a APISIXResource) String() string {
	return string(a)
}

const (
	// SkippedValueEtcdInitDir indicates the init_dir
	// etcd event will be skipped.
	SkippedValueEtcdInitDir = "init_dir"

	// SkippedValueEtcdEmptyObject indicates the data with an
	// empty JSON value {}, which may be set by APISIX,
	// should be also skipped.
	//
	// Important: at present, {} is considered as invalid,
	// but may be changed in the future.
	SkippedValueEtcdEmptyObject = "{}"

	ApisixResourceTypeRoutes         = "routes"
	ApisixResourceTypeServices       = "services"
	ApisixResourceTypeSSL            = "ssls"
	ApisixResourceTypeProtos         = "protos"
	ApisixResourceTypePluginMetadata = "plugin_metadata"

	SyncSleepSeconds = 5 * time.Second

	// StatusEnable apisix 资源启用状态，不能修改
	StatusEnable = 1
)
