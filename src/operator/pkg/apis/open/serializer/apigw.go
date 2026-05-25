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

// Package serializer ...
package serializer

import "operator/pkg/entity"

// ApigwListInfo apigw 资源列表
type ApigwListInfo map[string]*StageScopedApisixResources

// ResourceInfo resource
type ResourceInfo struct {
	ID   int64  `json:"resource_id"`
	Name string `json:"resource_name"`
}

// ApigwListRequest apigw list api req
type ApigwListRequest struct {
	GatewayName string       `json:"gateway_name,omitempty"`
	StageName   string       `json:"stage_name,omitempty"`
	Resource    ResourceInfo `json:"resource,omitempty"`
}

// ApigwListResourceCountResponse apigw 资源数量
type ApigwListResourceCountResponse struct {
	Count int64 `json:"count"`
}

// ApigwListCurrentVersionInfoResponse apigw 环境发布版本信息
type ApigwListCurrentVersionInfoResponse *entity.ReleaseInfo
