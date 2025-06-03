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

package biz

import (
	"context"

	"mcp_proxy/pkg/cacheimpls"
	"mcp_proxy/pkg/entity/model"
	"mcp_proxy/pkg/repo"
)

// GetRelease ...
func GetRelease(ctx context.Context, gatewayID int, stageID int) (*model.Release, error) {
	r := repo.CoreRelease
	return repo.CoreRelease.WithContext(ctx).Where(r.GatewayID.Eq(gatewayID), r.StageID.Eq(stageID)).First()
}

// GetOpenapiGatewayResourceVersionSpec ...
func GetOpenapiGatewayResourceVersionSpec(ctx context.Context, gatewayID int, resourceVersionID int) (
	*model.OpenapiGatewayResourceVersionSpec, error,
) {
	r := repo.OpenapiGatewayResourceVersionSpec
	return repo.OpenapiGatewayResourceVersionSpec.WithContext(ctx).Where(
		r.GatewayID.Eq(gatewayID), r.ResourceVersionID.Eq(resourceVersionID)).First()
}

// GetJWTInfoByGatewayName ...
func GetJWTInfoByGatewayName(ctx context.Context, gatewayName string) (*model.JWT, error) {
	// get gateway
	gateway, err := cacheimpls.GetGatewayByName(ctx, gatewayName)
	if err != nil {
		return nil, err
	}
	// query jwt
	jwt, err := cacheimpls.GetJWTInfo(ctx, gateway.ID)
	if err != nil {
		return nil, err
	}
	return jwt, nil
}
