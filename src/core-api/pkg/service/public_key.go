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

package service

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

import (
	"context"

	"core/pkg/cacheimpls"
	"core/pkg/database/dao"
)

// GatewayPublicKeyService is the interface of gateway public key service
type GatewayPublicKeyService interface {
	Get(ctx context.Context, instanceID, gatewayName string) (string, error)
	GetByGatewayName(ctx context.Context, gatewayName string) (string, error)
}

type gatewayPublicKeyService struct {
	jwtManager dao.JWTManager
}

// NewGatewayPublicKeyService create a new GatewayPublicKeyService instance
func NewGatewayPublicKeyService() GatewayPublicKeyService {
	return &gatewayPublicKeyService{
		jwtManager: dao.NewJWTManager(),
	}
}

// Get will get the gateway public key from cache by instanceID and gatewayName
func (s *gatewayPublicKeyService) Get(ctx context.Context, instanceID, gatewayName string) (string, error) {
	// get gatewayID
	gatewayID, err := getGatewayID(ctx, instanceID, gatewayName)
	if err != nil {
		return "", err
	}

	// query jwt
	publicKey, err := cacheimpls.GetJWTPublicKey(ctx, gatewayID)
	if err != nil {
		return "", err
	}

	return publicKey, nil
}

// GetByGatewayName will get the gateway public key from cache by gatewayName
func (s *gatewayPublicKeyService) GetByGatewayName(ctx context.Context, gatewayName string) (string, error) {
	// get gateway
	gateway, err := cacheimpls.GetGatewayByName(ctx, gatewayName)
	if err != nil {
		return "", err
	}
	// query jwt
	publicKey, err := cacheimpls.GetJWTPublicKey(ctx, gateway.ID)
	if err != nil {
		return "", err
	}
	return publicKey, nil
}
