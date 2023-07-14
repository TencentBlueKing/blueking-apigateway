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
	"errors"
	"time"

	gomonkey "github.com/agiledragon/gomonkey/v2"
	. "github.com/onsi/ginkgo/v2"
	"github.com/stretchr/testify/assert"

	"core/pkg/cacheimpls"
	"core/pkg/database/dao"
)

var _ = Describe("AppPermissionService", func() {
	Describe("appGatewayPermissionKey", func() {
		It("key", func() {
			gatewayName := "gatewayName"
			appCode := "appCode"
			key := appGatewayPermissionKey{gatewayName, appCode}

			assert.Equal(GinkgoT(), "gatewayName:-:appCode", key.Key())
		})
	})

	Describe("appResourcePermissionKey", func() {
		It("key", func() {
			gatewayName := "gatewayName"
			resourceName := "resourceName"
			appCode := "appCode"

			key := appResourcePermissionKey{gatewayName, resourceName, appCode}
			assert.Equal(GinkgoT(), "gatewayName:resourceName:appCode", key.Key())
		})
	})

	Describe("getGatewayID", func() {
		var patches *gomonkey.Patches
		var instanceID, gatewayName string
		BeforeEach(func() {
			patches = gomonkey.NewPatches()
			instanceID = "hello"
			gatewayName = "world"
		})

		AfterEach(func() {
			patches.Reset()
		})

		It("getGatewayID fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetMicroGateway,
				func(ctx context.Context, instanceID string) (dao.MicroGateway, error) {
					return dao.MicroGateway{}, errors.New("get GetMicroGateway fail")
				},
			)

			_, err := getGatewayID(context.Background(), instanceID, gatewayName)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetMicroGateway fail")
		})

		It("getGatewayID ok, not shared", func() {
			patches.ApplyFunc(
				cacheimpls.GetMicroGateway,
				func(ctx context.Context, instanceID string) (dao.MicroGateway, error) {
					return dao.MicroGateway{
						IsShared:  false,
						GatewayID: 123,
					}, nil
				},
			)
			id, err := getGatewayID(context.Background(), instanceID, gatewayName)
			assert.NoError(GinkgoT(), err)
			assert.Equal(GinkgoT(), int64(123), id)
		})

		It("getGatewayID ok, shared, GetGatewayByName fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetMicroGateway,
				func(ctx context.Context, instanceID string) (dao.MicroGateway, error) {
					return dao.MicroGateway{
						IsShared:  true,
						GatewayID: 123,
					}, nil
				},
			)

			patches.ApplyFunc(
				cacheimpls.GetGatewayByName,
				func(context.Context, string) (dao.Gateway, error) {
					return dao.Gateway{}, errors.New("get GetGatewayByName fail")
				},
			)

			_, err := getGatewayID(context.Background(), instanceID, gatewayName)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetGatewayByName fail")
		})

		It("getGatewayID ok, shared, GetGatewayByName ok", func() {
			patches.ApplyFunc(
				cacheimpls.GetMicroGateway,
				func(ctx context.Context, instanceID string) (dao.MicroGateway, error) {
					return dao.MicroGateway{
						IsShared:  true,
						GatewayID: 123,
					}, nil
				},
			)

			patches.ApplyFunc(
				cacheimpls.GetGatewayByName,
				func(context.Context, string) (dao.Gateway, error) {
					return dao.Gateway{
						ID: 456,
					}, nil
				},
			)
			id, err := getGatewayID(context.Background(), instanceID, gatewayName)
			assert.NoError(GinkgoT(), err)
			assert.Equal(GinkgoT(), int64(456), id)
		})
	})

	Describe("getStageID", func() {
		var patches *gomonkey.Patches
		var gatewayID int64
		var stageName string
		BeforeEach(func() {
			patches = gomonkey.NewPatches()
			gatewayID = 1
			stageName = "world"
		})

		AfterEach(func() {
			patches.Reset()
		})

		It("GetStage fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetStage,
				func(ctx context.Context, gatewayID int64, stageName string) (dao.Stage, error) {
					return dao.Stage{}, errors.New("get GetStage fail")
				},
			)

			_, err := getStageID(context.Background(), gatewayID, stageName)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetStage fail")
		})

		It("GetStage ok", func() {
			patches.ApplyFunc(
				cacheimpls.GetStage,
				func(ctx context.Context, gatewayID int64, stageName string) (dao.Stage, error) {
					return dao.Stage{ID: 1}, nil
				},
			)
			id, err := getStageID(context.Background(), gatewayID, stageName)
			assert.NoError(GinkgoT(), err)
			assert.Equal(GinkgoT(), int64(1), id)
		})
	})

	Describe("getResourceIDByName", func() {
		var patches *gomonkey.Patches
		var gatewayID int64
		var stageID int64
		var resourceName string
		BeforeEach(func() {
			patches = gomonkey.NewPatches()
			gatewayID = 1
			stageID = 2
			resourceName = "hello"
		})

		AfterEach(func() {
			patches.Reset()
		})

		It("GetRelease fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetRelease,
				func(context.Context, int64, int64) (dao.Release, error) {
					return dao.Release{}, errors.New("get GetRelease fail")
				},
			)

			_, _, err := getResourceIDByName(context.Background(), gatewayID, stageID, resourceName)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetRelease fail")
		})

		It("GetRelease ok, GetResourceVersionMapping fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetRelease,
				func(context.Context, int64, int64) (dao.Release, error) {
					return dao.Release{
						ID:                1,
						ResourceVersionID: 2,
					}, nil
				},
			)

			patches.ApplyFunc(
				cacheimpls.GetResourceVersionMapping,
				func(context.Context, int64) (map[string]int64, error) {
					return nil, errors.New("get GetResourceVersionMapping fail")
				},
			)

			_, _, err := getResourceIDByName(context.Background(), gatewayID, stageID, resourceName)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetResourceVersionMapping fail")
		})

		It("getGatewayID ok, shared, GetGatewayByName ok", func() {
			patches.ApplyFunc(
				cacheimpls.GetRelease,
				func(context.Context, int64, int64) (dao.Release, error) {
					return dao.Release{
						ID:                1,
						ResourceVersionID: 2,
					}, nil
				},
			)

			patches.ApplyFunc(
				cacheimpls.GetResourceVersionMapping,
				func(context.Context, int64) (map[string]int64, error) {
					return map[string]int64{
						resourceName: 456,
					}, nil
				},
			)

			resourceID, ok, err := getResourceIDByName(context.Background(), gatewayID, stageID, resourceName)
			assert.NoError(GinkgoT(), err)
			assert.True(GinkgoT(), ok)
			assert.Equal(GinkgoT(), int64(456), resourceID)
		})
	})

	Describe("appPermissionService Query", func() {
		var patches *gomonkey.Patches
		var instanceID, gatewayName, stageName, resourceName, appCode string
		var gatewayID, stageID, resourceID int64
		BeforeEach(func() {
			patches = gomonkey.NewPatches()
			instanceID = "1"
			gatewayName = "hello"
			stageName = "world"
			resourceName = "resource"
			appCode = "app"

			gatewayID = 1
			stageID = 2
			resourceID = 3

			patches.ApplyFunc(
				getGatewayID,
				func(ctx context.Context, instanceID, gatewayName string) (int64, error) {
					return gatewayID, nil
				},
			)
			patches.ApplyFunc(
				getStageID,
				func(ctx context.Context, gatewayID int64, stageName string) (int64, error) {
					return stageID, nil
				},
			)
			patches.ApplyFunc(
				getResourceIDByName,
				func(ctx context.Context, gatewayID, stageID int64, resourceName string) (int64, bool, error) {
					return resourceID, true, nil
				},
			)
		})

		AfterEach(func() {
			patches.Reset()
		})

		It("GetAppGatewayPermissionExpiredAt fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetAppGatewayPermissionExpiredAt,
				func(context.Context, string, int64) (int64, error) {
					return 0, errors.New("get GetAppGatewayPermissionExpiredAt fail")
				},
			)

			svc := &appPermissionService{}
			_, err := svc.Query(context.Background(), instanceID, gatewayName, stageName, resourceName, appCode)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetAppGatewayPermissionExpiredAt fail")
		})

		It("GetAppResourcePermissionExpiredAt fail", func() {
			patches.ApplyFunc(
				cacheimpls.GetAppGatewayPermissionExpiredAt,
				func(context.Context, string, int64) (int64, error) {
					return 123, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetAppResourcePermissionExpiredAt,
				func(context.Context, string, int64, int64) (int64, error) {
					return 0, errors.New("get GetAppResourcePermissionExpiredAt fail")
				},
			)

			svc := &appPermissionService{}
			_, err := svc.Query(context.Background(), instanceID, gatewayName, stageName, resourceName, appCode)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get GetAppResourcePermissionExpiredAt fail")
		})

		It("ok", func() {
			patches.ApplyFunc(
				cacheimpls.GetAppGatewayPermissionExpiredAt,
				func(context.Context, string, int64) (int64, error) {
					return 123, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetAppResourcePermissionExpiredAt,
				func(context.Context, string, int64, int64) (int64, error) {
					return 456, nil
				},
			)

			svc := &appPermissionService{}
			permissions, err := svc.Query(
				context.Background(),
				instanceID,
				gatewayName,
				stageName,
				resourceName,
				appCode,
			)
			assert.NoError(GinkgoT(), err)

			assert.Equal(GinkgoT(), int64(123), permissions[gatewayName+":-:"+appCode])
			assert.Equal(GinkgoT(), int64(456), permissions[gatewayName+":"+resourceName+":"+appCode])
		})

		It("ok, gateway permission return early", func() {
			expiredAt := time.Now().Unix() + 1000
			patches.ApplyFunc(
				cacheimpls.GetAppGatewayPermissionExpiredAt,
				func(context.Context, string, int64) (int64, error) {
					return expiredAt, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetAppResourcePermissionExpiredAt,
				func(context.Context, string, int64, int64) (int64, error) {
					return 456, nil
				},
			)

			svc := &appPermissionService{}
			permissions, err := svc.Query(
				context.Background(),
				instanceID,
				gatewayName,
				stageName,
				resourceName,
				appCode,
			)
			assert.NoError(GinkgoT(), err)

			assert.Equal(GinkgoT(), expiredAt, permissions[gatewayName+":-:"+appCode])
			assert.Len(GinkgoT(), permissions, 1)
		})
	})
})
