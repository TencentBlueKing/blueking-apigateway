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

// Package biz ...
package biz

import (
	"encoding/json"
	"errors"
	"fmt"

	"operator/pkg/config"
	"operator/pkg/core/store"
	"operator/pkg/entity"
)

// GetApisixResourceCount 获取 apisix 指定环境的资源数量
func GetApisixResourceCount(
	store *store.ApisixEtcdStore,
	gatewayName string,
	stageName string,
) (int64, error) {
	stageKey := config.GenStagePrimaryKey(gatewayName, stageName)
	apisixResources := store.Get(stageKey)
	return int64(len(apisixResources.Routes)), nil
}

// ListApisixResources 获取 apisix 指定环境的资源列表
func ListApisixResources(
	store *store.ApisixEtcdStore,
	gatewayName string,
	stageName string,
) map[string]*entity.ApisixStageResource {
	configMap := make(map[string]*entity.ApisixStageResource)
	stageKey := config.GenStagePrimaryKey(gatewayName, stageName)
	apisixResources := store.Get(stageKey)
	configMap[stageKey] = apisixResources
	return configMap
}

// GetApisixResource 获取 apisix 指定环境下的资源信息
func GetApisixResource(
	store *store.ApisixEtcdStore,
	gatewayName string,
	stageName string,
	resourceName string,
	resourceID int64,
) (map[string]*entity.ApisixStageResource, error) {
	configMap := make(map[string]*entity.ApisixStageResource)
	stageKey := config.GenStagePrimaryKey(gatewayName, stageName)
	apisixResources := store.Get(stageKey)

	// by resourceName
	if resourceName != "" {
		resourceNameKey := GenApisixResourceNameKey(gatewayName, stageName, resourceName)
		for _, route := range apisixResources.Routes {
			if route.Name == resourceNameKey {
				configMap[stageKey] = &entity.ApisixStageResource{
					Routes: map[string]*entity.Route{route.ID: route},
				}
				return configMap, nil
			}
		}
		return nil, fmt.Errorf("get apisix resource_name failed: %s not found", resourceNameKey)
	}

	// by resourceID
	resourceIDKey := GenResourceIDKey(gatewayName, stageName, resourceID)
	route := apisixResources.Routes[resourceIDKey]
	if route == nil {
		return nil, fmt.Errorf("get apisix resource_id failed: %s not found", resourceIDKey)
	}
	configMap[stageKey] = &entity.ApisixStageResource{
		Routes: map[string]*entity.Route{resourceIDKey: route},
	}
	return configMap, nil
}

// GetApisixStageCurrentVersionInfo 获取 apisix 指定环境的发布版本信息
func GetApisixStageCurrentVersionInfo(
	store *store.ApisixEtcdStore,
	gatewayName string,
	stageName string,
) (map[string]any, error) {
	stageKey := config.GenStagePrimaryKey(gatewayName, stageName)
	apisixResources := store.Get(stageKey)

	resourceIDKey := GenResourceIDKey(gatewayName, stageName, config.ReleaseVersionResourceID)
	route := apisixResources.Routes[resourceIDKey]
	if route == nil {
		return nil, errors.New("current-version not found")
	}

	for _, plugin := range route.Plugins {
		pluginData, ok := plugin.(map[string]any)
		if !ok {
			continue
		}
		responseExampleAny, exists := pluginData["response_example"]
		if !exists {
			continue
		}
		responseExample, ok := responseExampleAny.(string)
		if !ok {
			continue
		}
		if responseExample == "" {
			continue
		}
		versionInfo := make(map[string]any)
		err := json.Unmarshal([]byte(responseExample), &versionInfo)
		if err != nil {
			return nil, errors.New("current-version unmarshal error: " + err.Error())
		}

		return versionInfo, nil
	}

	return nil, errors.New("current-version not found")
}
