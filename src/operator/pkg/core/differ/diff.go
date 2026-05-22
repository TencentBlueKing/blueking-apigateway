/*
 *  TencentBlueKing is pleased to support the open source community by making
 *  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 *  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
 *  Licensed under the MIT License (the "License"); you may not use this file except
 *  in compliance with the License. You may obtain a copy of the License at
 *
 *      http://opensource.org/licenses/MIT
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under
 *  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 *  either express or implied. See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 *   We undertake not to change the open source license (MIT license) applicable
 *   to the current version of the project delivered to anyone in the future.
 */

// Package differ ...
package differ

import (
	"maps"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	json "github.com/json-iterator/go"

	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/metric"
)

type ConfigDiffer struct{}

// NewConfigDiffer creates and returns a new instance of ConfigDiffer
// It serves as a constructor function for the ConfigDiffer struct
func NewConfigDiffer() *ConfigDiffer {
	// Return a new instance of ConfigDiffer
	return &ConfigDiffer{}
}

// transformMap: A separate comparison transformer is needed for map types, as the value is an interface type
// and there are type inconsistencies with different serialization methods.
// e.g.: value may exist as map[any]any, map[string]any, or map[interface]any.
func transformMap(mapType map[string]any) map[string]any {
	mapTypeJson, _ := json.Marshal(mapType)
	var newMap map[string]any
	_ = json.Unmarshal(mapTypeJson, &newMap)
	return newMap
}

// ignoreCreateTimeAndUpdateTimeCmpOpt: 忽略typ 创建、更新时间
var ignoreCreateTimeAndUpdateTimeCmpOptFunc = func(typ any) cmp.Option {
	return cmpopts.IgnoreFields(typ, "CreateTime", "UpdateTime")
}

// normalizeNodesValue: Normalize Nodes field values through JSON serialization/deserialization
// This handles type inconsistencies like map[string]any vs map[any]any, and int vs float64
func normalizeNodesValue(v any) any {
	if v == nil {
		return nil
	}
	// Serialize to JSON and deserialize back to normalize types
	jsonBytes, err := json.Marshal(v)
	if err != nil {
		return v
	}
	var normalized any
	if err := json.Unmarshal(jsonBytes, &normalized); err != nil {
		return v
	}
	return normalized
}

// normalizeRouteNodes: Normalize Nodes field in Route's Upstream
func normalizeRouteNodes(route *entity.Route) *entity.Route {
	if route == nil || route.Upstream == nil {
		return route
	}
	// Create a copy to avoid modifying the original
	normalized := *route
	normalized.Upstream = &entity.UpstreamDef{}
	*normalized.Upstream = *route.Upstream
	normalized.Upstream.Nodes = normalizeNodesValue(route.Upstream.Nodes)
	return &normalized
}

// normalizeServiceNodes: Normalize Nodes field in Service's Upstream
func normalizeServiceNodes(service *entity.Service) *entity.Service {
	if service == nil || service.Upstream == nil {
		return service
	}
	// Create a copy to avoid modifying the original
	normalized := *service
	if service.Upstream != nil {
		normalized.Upstream = &entity.UpstreamDef{}
		*normalized.Upstream = *service.Upstream
		normalized.Upstream.Nodes = normalizeNodesValue(service.Upstream.Nodes)
	}
	return &normalized
}

// ignoreApisixMetadata: ignore some members of apisixMetadata
var ignoreApisixMetadataCmpOpt = cmpopts.IgnoreFields(entity.ResourceMetadata{},
	"Labels", "Ctx", "RetryCount", "APIVersion", "Kind", "ApisixVersion", "Op",
)

// CmpReporter ...
type CmpReporter struct {
	Gateway      string
	Stage        string
	ResourceType string
	CmpReported  bool
	DiffReported bool
}

// PushStep ...
func (r *CmpReporter) PushStep(ps cmp.PathStep) {
}

// PopStep ...
func (r *CmpReporter) PopStep() {
}

// Report ...
func (r *CmpReporter) Report(rs cmp.Result) {
	// report sync cmp metric
	if !r.CmpReported {
		metric.ReportSyncCmpMetric(
			r.Gateway,
			r.Stage,
			r.ResourceType,
		)
		r.CmpReported = true
	}

	// report sync cmp diff  metric
	if !rs.Equal() && !r.DiffReported {
		metric.ReportSyncCmpDiffMetric(
			r.Gateway,
			r.Stage,
			r.ResourceType,
		)
		r.DiffReported = true
	}
}

// Diff 对比两个 ApisixStageResource，返回需要 put 和 delete 的资源
func (d *ConfigDiffer) Diff(
	old, new *entity.ApisixStageResource,
) (put, toDelete *entity.ApisixStageResource) {
	if old == nil {
		return new, nil
	}
	if new == nil {
		return nil, old
	}
	put = &entity.ApisixStageResource{}
	toDelete = &entity.ApisixStageResource{}
	put.Routes, toDelete.Routes = d.DiffRoutes(old.Routes, new.Routes)
	put.Services, toDelete.Services = d.DiffServices(old.Services, new.Services)
	put.SSLs, toDelete.SSLs = d.DiffSSLs(old.SSLs, new.SSLs)
	return put, toDelete
}

// DiffGlobal 对比全局资源配置
func (d *ConfigDiffer) DiffGlobal(
	old, new *entity.ApisixGlobalResource,
) (put, toDelete *entity.ApisixGlobalResource) {
	if old == nil {
		return new, nil
	}
	if new == nil {
		return nil, old
	}
	put = &entity.ApisixGlobalResource{}
	toDelete = &entity.ApisixGlobalResource{}
	put.PluginMetadata, toDelete.PluginMetadata = d.DiffPluginMetadatas(old.PluginMetadata, new.PluginMetadata)
	return put, toDelete
}

// DiffRoutes 对比两个 Route map，返回需要 put 和 delete 的 Route
func (d *ConfigDiffer) DiffRoutes(
	old map[string]*entity.Route,
	new map[string]*entity.Route,
) (putList, deleteList map[string]*entity.Route) {
	oldResMap := make(map[string]*entity.Route)
	putList = make(map[string]*entity.Route)
	deleteList = make(map[string]*entity.Route)
	maps.Copy(oldResMap, old)
	for key, newRes := range new {
		oldRes, ok := oldResMap[key]
		if !ok {
			putList[key] = newRes
			continue
		}

		// Normalize Nodes fields before comparison
		normalizedOld := normalizeRouteNodes(oldRes)
		normalizedNew := normalizeRouteNodes(newRes)
		if !cmp.Equal(
			normalizedOld,
			normalizedNew,
			cmp.Transformer("transformerMap", transformMap),
			ignoreApisixMetadataCmpOpt,
			cmp.Reporter(&CmpReporter{
				Gateway:      newRes.GetReleaseInfo().GetGatewayName(),
				Stage:        newRes.GetReleaseInfo().GetStageName(),
				ResourceType: constant.ApisixResourceTypeRoutes,
			}),
			ignoreCreateTimeAndUpdateTimeCmpOptFunc(entity.Route{}),
		) {
			putList[key] = newRes
		}
		delete(oldResMap, key)
	}
	maps.Copy(deleteList, oldResMap)
	return putList, deleteList
}

// DiffServices 对比两个 Service map，返回需要 put 和 delete 的 Service
func (d *ConfigDiffer) DiffServices(
	old map[string]*entity.Service,
	new map[string]*entity.Service,
) (putList, deleteList map[string]*entity.Service) {
	oldResMap := make(map[string]*entity.Service)
	putList = make(map[string]*entity.Service)
	deleteList = make(map[string]*entity.Service)
	maps.Copy(oldResMap, old)
	for key, newRes := range new {
		oldRes, ok := oldResMap[key]
		if !ok {
			putList[key] = newRes
			continue
		}
		// Normalize Nodes fields before comparison
		normalizedOld := normalizeServiceNodes(oldRes)
		normalizedNew := normalizeServiceNodes(newRes)
		if !cmp.Equal(
			normalizedOld,
			normalizedNew,
			cmp.Transformer("transformerMap", transformMap),
			ignoreApisixMetadataCmpOpt,
			cmp.Reporter(&CmpReporter{
				Gateway:      newRes.GetReleaseInfo().GetGatewayName(),
				Stage:        newRes.GetReleaseInfo().GetStageName(),
				ResourceType: constant.ApisixResourceTypeServices,
			}),
			ignoreCreateTimeAndUpdateTimeCmpOptFunc(entity.Service{}),
		) {
			putList[key] = newRes
		}
		delete(oldResMap, key)
	}
	maps.Copy(deleteList, oldResMap)
	return putList, deleteList
}

// DiffPluginMetadatas 对比两个 PluginMetadata map，返回需要 put 和 delete 的 PluginMetadata
func (d *ConfigDiffer) DiffPluginMetadatas(
	old map[string]*entity.PluginMetadata,
	new map[string]*entity.PluginMetadata,
) (putList, deleteList map[string]*entity.PluginMetadata) {
	oldResMap := make(map[string]*entity.PluginMetadata)
	putList = make(map[string]*entity.PluginMetadata)
	deleteList = make(map[string]*entity.PluginMetadata)
	maps.Copy(oldResMap, old)
	for key, newRes := range new {
		oldRes, ok := oldResMap[key]
		if !ok {
			putList[key] = newRes
			continue
		}
		if !cmp.Equal(
			oldRes.PluginMetadataConf,
			newRes.PluginMetadataConf,
		) {
			putList[key] = newRes
		}
		delete(oldResMap, key)
	}
	maps.Copy(deleteList, oldResMap)
	return putList, deleteList
}

// DiffSSLs 对比两个 SSL map，返回需要 put 和 delete 的 SSL
func (d *ConfigDiffer) DiffSSLs(
	old map[string]*entity.SSL,
	new map[string]*entity.SSL,
) (putList, deleteList map[string]*entity.SSL) {
	oldResMap := make(map[string]*entity.SSL)
	putList = make(map[string]*entity.SSL)
	deleteList = make(map[string]*entity.SSL)
	maps.Copy(oldResMap, old)
	for key, newRes := range new {
		oldRes, ok := oldResMap[key]
		if !ok {
			putList[key] = newRes
			continue
		}
		if !cmp.Equal(oldRes, newRes,
			cmp.Transformer("transformerMap", transformMap),
			cmp.Reporter(&CmpReporter{
				Gateway:      newRes.GetReleaseInfo().GetGatewayName(),
				Stage:        newRes.GetReleaseInfo().GetStageName(),
				ResourceType: constant.ApisixResourceTypeSSL,
			}),
		) {
			putList[key] = newRes
		}
		delete(oldResMap, key)
	}
	maps.Copy(deleteList, oldResMap)
	return putList, deleteList
}
