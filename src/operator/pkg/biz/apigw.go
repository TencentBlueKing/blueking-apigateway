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
	"context"

	"operator/pkg/config"
	"operator/pkg/constant"
	"operator/pkg/core/committer"
	"operator/pkg/entity"
)

// GetApigwResourcesByStage 根据网关查询资源
func GetApigwResourcesByStage(
	ctx context.Context,
	committer *committer.Committer,
	gatewayName string,
	stageName string,
	isExcludeReleaseVersion bool,
) (*entity.ApisixStageResource, error) {
	si := &entity.ReleaseInfo{
		Ctx: ctx,
		ResourceMetadata: entity.ResourceMetadata{
			APIVersion: "v2",
			Labels: &entity.LabelInfo{
				Gateway: gatewayName,
				Stage:   stageName,
			},
		},
	}
	apisixConf, err := committer.GetStageReleaseNativeApisixConfiguration(ctx, si)
	if err != nil {
		return nil, err
	}
	if isExcludeReleaseVersion {
		// 资源列表中排除 builtin-mock-release-version
		resourceIDKey := GenResourceIDKey(gatewayName, stageName, config.ReleaseVersionResourceID)
		delete(apisixConf.Routes, resourceIDKey)
	}
	return apisixConf, nil
}

// GetApigwResourceCount 获取 apigw 指定环境的资源数量
func GetApigwResourceCount(
	ctx context.Context,
	committer *committer.Committer,
	gatewayName string,
	stageName string,
) (int64, error) {
	si := &entity.ReleaseInfo{
		Ctx: ctx,
		ResourceMetadata: entity.ResourceMetadata{
			APIVersion: "v2",
			Kind:       constant.Route,
			Labels: &entity.LabelInfo{
				Gateway: gatewayName,
				Stage:   stageName,
			},
		},
	}
	count, err := committer.GetResourceCount(ctx, si)
	if err != nil {
		return 0, err
	}
	return count, nil
}

// ListApigwResources 获取 apigw 指定环境的资源列表
func ListApigwResources(
	ctx context.Context,
	committer *committer.Committer,
	gatewayName string,
	stageName string,
) (map[string]*entity.ApisixStageResource, error) {
	configMap := make(map[string]*entity.ApisixStageResource)
	stageKey := config.GenStagePrimaryKey(gatewayName, stageName)
	apisixResources, err := GetApigwResourcesByStage(ctx, committer, gatewayName, stageName, true)
	if err != nil {
		return nil, err
	}
	configMap[stageKey] = apisixResources
	return configMap, nil
}

// GetApigwResource 获取 apigw 指定环境下的资源信息
func GetApigwResource(
	ctx context.Context,
	committer *committer.Committer,
	gatewayName string,
	stageName string,
	resourceName string,
	resourceID int64,
) (map[string]*entity.ApisixStageResource, error) {
	configMap := make(map[string]*entity.ApisixStageResource)
	stageKey := config.GenStagePrimaryKey(gatewayName, stageName)

	// by resourceName
	if resourceName != "" {
		resourceNameKey := GenApigwResourceNameKey(gatewayName, stageName, resourceName)
		apisixResources, err := GetApigwResourcesByStage(ctx, committer, gatewayName, stageName, true)
		if err != nil {
			return nil, err
		}
		for _, route := range apisixResources.Routes {
			if route.Name == resourceNameKey {
				configMap[stageKey] = &entity.ApisixStageResource{
					Routes: map[string]*entity.Route{route.ID: route},
				}
				return configMap, nil
			}
		}
	}

	// by resourceID
	si := &entity.ReleaseInfo{
		Ctx: ctx,
		ResourceMetadata: entity.ResourceMetadata{
			APIVersion: "v2",
			Kind:       constant.Route,
			Labels: &entity.LabelInfo{
				Gateway: gatewayName,
				Stage:   stageName,
			},
		},
	}

	apisixResources, err := committer.GetStageReleaseNativeApisixConfigurationByID(
		ctx, GenResourceIDKey(gatewayName, stageName, resourceID), si,
	)
	if err != nil {
		return nil, err
	}
	configMap[stageKey] = apisixResources
	return configMap, nil
}

// GetApigwStageCurrentVersionInfo 获取 apigw 指定环境的发布版本信息
func GetApigwStageCurrentVersionInfo(
	ctx context.Context,
	committer *committer.Committer,
	gatewayName string,
	stageName string,
) (*entity.ReleaseInfo, error) {
	si := &entity.ReleaseInfo{
		Ctx: ctx,
		ResourceMetadata: entity.ResourceMetadata{
			APIVersion: "v2",
			Labels: &entity.LabelInfo{
				Gateway: gatewayName,
				Stage:   stageName,
			},
		},
	}
	releaseVersionInfo, err := committer.GetStageReleaseVersion(ctx, si)
	if err != nil {
		return nil, err
	}
	return releaseVersionInfo, nil
}
