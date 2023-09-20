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

import (
	"context"
	"fmt"
	"time"

	"core/pkg/cacheimpls"
	"core/pkg/logging"
)

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

// ClientLRUCacheTTL ...
const (
	// seconds
	ClientLRUCacheTTL = 60
)

// AppPermissionService is the interface of app permission service
type AppPermissionService interface {
	Query(
		ctx context.Context,
		instanceID, gatewayName, stageName, resourceName, appCode string,
	) (map[string]int64, error)
}

type appPermissionService struct {
	// NOTE: move all data query into cache layer
	//       if you need use dao directly, no performance guarantee, uncomment what you need
	// gatewayManager         dao.GatewayManager
	// microGatewayManager    dao.MicroGatewayManager
	// stageManager           dao.StageManager
	// releaseManager         dao.ReleaseManager
	// resourceVersionManager dao.ResourceVersionManager

	// appGatewayPermissionManager  dao.AppGatewayPermissionManager
	// appResourcePermissionManager dao.AppResourcePermissionManager
}

// NewAppPermissionService will create a new AppPermissionService
func NewAppPermissionService() AppPermissionService {
	return &appPermissionService{
		// gatewayManager:         dao.NewGatewayManager(),
		// microGatewayManager:    dao.NewMicroGatewayManager(),
		// stageManager:           dao.NewStageManager(),
		// releaseManager:         dao.NewReleaseManager(),
		// resourceVersionManager: dao.NewResourceVersionManager(),

		// appGatewayPermissionManager:  dao.NewAppGatewayPermissionManager(),
		// appResourcePermissionManager: dao.NewAppResourcePermissionManager(),
	}
}

type appGatewayPermissionKey struct {
	GatewayName string
	AppCode     string
}

// Key will return the specific key for the result of app-gateway permission
func (k appGatewayPermissionKey) Key() string {
	return fmt.Sprintf("%s:-:%s", k.GatewayName, k.AppCode)
}

type appResourcePermissionKey struct {
	GatewayName  string
	ResourceName string
	AppCode      string
}

// Key will return the specific key for the result of app-resource permission
func (k appResourcePermissionKey) Key() string {
	return fmt.Sprintf("%s:%s:%s", k.GatewayName, k.ResourceName, k.AppCode)
}

// Query will query the app permission, it will get app-permission and resource-permission from cache
func (s *appPermissionService) Query(
	ctx context.Context, instanceID, gatewayName, stageName, resourceName, appCode string,
) (map[string]int64, error) {
	permissions := make(map[string]int64, 2)

	gatewayID, err := getGatewayID(ctx, instanceID, gatewayName)
	if err != nil {
		return nil, err
	}

	// 1. get app-gateway permission
	gatewayPermissionExpiredAt, err := cacheimpls.GetAppGatewayPermissionExpiredAt(ctx, appCode, gatewayID)
	if err != nil {
		return nil, fmt.Errorf("call GetAppGatewayPermissionExpiredAt fail: %w, gatewayID = %d", err, gatewayID)
	}
	logging.GetLogger().Debugw("call GetAppGatewayPermissionExpiredAt",
		"instanceID", instanceID,
		"gatewayName", gatewayName,
		"stageName", stageName,
		"resourceName", resourceName,
		"appCode", appCode,
		"gatewayID", gatewayID,
		"gatewayPermissionExpiredAt", gatewayPermissionExpiredAt,
	)
	// if has app gateway permission records
	if gatewayPermissionExpiredAt != 0 {
		appGatewayKey := appGatewayPermissionKey{
			GatewayName: gatewayName,
			AppCode:     appCode,
		}
		permissions[appGatewayKey.Key()] = gatewayPermissionExpiredAt

		// if app has gateway permission, and expires greater than now+60s(apisix plugin lrucache)
		now := time.Now().Unix()
		if gatewayPermissionExpiredAt > now+ClientLRUCacheTTL {
			logging.GetLogger().
				Debugw("app has gateway permission, and expires greater than now + ClientLRUCacheTTL, will return",
					"ClientLRUCacheTTL", ClientLRUCacheTTL,
					"instanceID", instanceID,
					"gatewayName", gatewayName,
					"stageName", stageName,
					"resourceName", resourceName,
					"appCode", appCode,
					"gatewayID", gatewayID,
					"gatewayPermissionExpiredAt", gatewayPermissionExpiredAt,
				)
			// no need to query app-resource permission
			return permissions, nil
		}
	}

	stageID, err := getStageID(ctx, gatewayID, stageName)
	if err != nil {
		return nil, err
	}

	// 2. get app-resource permission

	// 2.1 get resourceID by resourceName from release-resource_version-data
	resourceID, ok, err := getResourceIDByName(ctx, gatewayID, stageID, resourceName)
	if err != nil {
		return nil, err
	}
	// got no records, return directly
	if !ok {
		logging.GetLogger().Debugw("app has no resource permission records, will return",
			"instanceID", instanceID,
			"gatewayName", gatewayName,
			"stageName", stageName,
			"resourceName", resourceName,
			"appCode", appCode,
			"gatewayID", gatewayID,
			"stageID", stageID,
		)
		return permissions, nil
	}

	// 2.2 query app-resource permission
	resourcePermissionExpiredAt, err := cacheimpls.GetAppResourcePermissionExpiredAt(
		ctx,
		appCode,
		gatewayID,
		resourceID,
	)
	if err != nil {
		return nil, fmt.Errorf(
			"call GetAppResourcePermissionExpiredAt fail: %w, appCode=%s, gatewayID=%d, resourceID=%d",
			err,
			appCode,
			gatewayID,
			resourceID,
		)
	}
	logging.GetLogger().Debugw("call GetAppResourcePermissionExpiredAt",
		"instanceID", instanceID,
		"gatewayName", gatewayName,
		"stageName", stageName,
		"resourceName", resourceName,
		"appCode", appCode,
		"gatewayID", gatewayID,
		"resourceID", resourceID,
		"resourcePermissionExpiredAt", resourcePermissionExpiredAt,
	)
	if resourcePermissionExpiredAt != 0 {
		appResourceKey := appResourcePermissionKey{
			GatewayName:  gatewayName,
			ResourceName: resourceName,
			AppCode:      appCode,
		}
		permissions[appResourceKey.Key()] = resourcePermissionExpiredAt
	}

	return permissions, nil
}

func getGatewayID(ctx context.Context, instanceID, gatewayName string) (int64, error) {
	microGateway, err := cacheimpls.GetMicroGateway(ctx, instanceID)
	if err != nil {
		return 0, fmt.Errorf("call GetMicroGateway fail: %w, instanceID=%s", err, instanceID)
	}

	// var gateway dao.Gateway
	if microGateway.IsShared {
		gateway, err := cacheimpls.GetGatewayByName(ctx, gatewayName)
		if err != nil {
			return 0, fmt.Errorf("call GetGatewayByName fail: %w, isShared=true, gatewayName=%s", err, gatewayName)
		}
		return gateway.ID, nil
	}

	// The micro_gateway.gateway_id is referenced to the gateway, so just return
	return microGateway.GatewayID, nil
}

func getStageID(ctx context.Context, gatewayID int64, stageName string) (int64, error) {
	stage, err := cacheimpls.GetStage(ctx, gatewayID, stageName)
	if err != nil {
		return 0, fmt.Errorf("call GetStage fail: %w, gatewayID = %d, stageName = %s", err, gatewayID, stageName)
	}

	return stage.ID, nil
}

func getResourceIDByName(
	ctx context.Context,
	gatewayID int64,
	stageID int64,
	resourceName string,
) (int64, bool, error) {
	// NOTE: there got no resourceID in private Gateway(isShared=False), only have resourceName
	//       so, we should get resourceID by resourceName
	// 1. get `Release` by gatewayID and stageID, release has a reference field `resource_version_id ` to ResourceVersion
	// 2. get `ResourceVersion` by `resource_version_id`, ResourceVersion has data field `[{}, {}]`
	// 3. unmarshal the data into a map[string]int64, key is resourceName, value is resourceID
	// 4. get resourceID by resourceName

	// 2.1 get release id first
	release, err := cacheimpls.GetRelease(ctx, gatewayID, stageID)
	if err != nil {
		err = fmt.Errorf("call GetRelease fail: %w, gatewayID=%d, stageID=%d", err, gatewayID, stageID)
		return 0, false, err
	}

	resourceNameToID, err := cacheimpls.GetResourceVersionMapping(ctx, release.ResourceVersionID)
	if err != nil {
		err = fmt.Errorf("call GetResourceVersionMapping fail: %w, releaseID=%d, resourceVersionID=%d",
			err,
			release.ID,
			release.ResourceVersionID,
		)
		return 0, false, err
	}

	// 2.2 get resource id
	resourceID, ok := resourceNameToID[resourceName]
	return resourceID, ok, nil
}
