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

	"core/pkg/cacheimpls"
	"core/pkg/constant"
	"core/pkg/database"
	"core/pkg/database/dao"
	"core/pkg/database/dao/mock"

	"github.com/agiledragon/gomonkey/v2"
	"github.com/go-sql-driver/mysql"
	"github.com/golang/mock/gomock"
	. "github.com/onsi/ginkgo/v2"
	"github.com/stretchr/testify/assert"
)

var _ = Describe("PublishEventService", func() {
	Describe("publish  event report", func() {
		var patches *gomonkey.Patches
		var ctl *gomock.Controller
		var ctx context.Context
		var svc PublishEventService
		var event Event
		var releaseHistory dao.ReleaseHistory
		var stage dao.Stage

		var mockPublishEventManager *mock.MockPublishEventManger
		BeforeEach(func() {
			patches = gomonkey.NewPatches()
			ctl = gomock.NewController(GinkgoT())
			ctx = context.Background()
			event = Event{
				Gateway:   "dev",
				Stage:     "test",
				Name:      constant.EventNameLoadConfiguration,
				Status:    constant.EventStatusFailure,
				PublishID: 1,
				DetailMap: nil,
			}
			mockPublishEventManager = mock.NewMockPublishEventManger(ctl)
			svc = publishEventService{
				publishEventManager: mockPublishEventManager,
			}

			// mock data
			releaseHistory = dao.ReleaseHistory{
				ID:                1,
				CreatedTime:       time.Now().Add(time.Hour * -24),
				UpdatedTime:       time.Now().Add(time.Hour * -24),
				GatewayID:         12,
				ResourceVersionID: 13,
				StageID:           1,
			}

			stage = dao.Stage{
				ID:   1,
				Name: "stage",
			}
		})
		AfterEach(func() {
			ctl.Finish()
			patches.Reset()
		})

		It("error: release history not found", func() {
			patches.ApplyFunc(
				cacheimpls.GetReleaseHistory,
				func(ctx context.Context, publishID int64) (dao.ReleaseHistory, error) {
					return dao.ReleaseHistory{}, errors.New("get release history fail")
				},
			)
			err := svc.Report(ctx, event)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "release history by publish_id:1 failed")
		})

		It("error: event has expire", func() {
			releaseHistory.CreatedTime = time.Now().Add(time.Hour * -3)
			patches.ApplyFunc(
				cacheimpls.GetReleaseHistory,
				func(ctx context.Context, publishID int64) (dao.ReleaseHistory, error) {
					return releaseHistory, nil
				},
			)
			err := svc.Report(ctx, event)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "event has passed for a long time")
		})

		It("error: Stage not found", func() {
			releaseHistory.CreatedTime = time.Now()
			patches.ApplyFunc(
				cacheimpls.GetReleaseHistory,
				func(ctx context.Context, publishID int64) (dao.ReleaseHistory, error) {
					return releaseHistory, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetStage,
				func(ctx context.Context, gatewayID int64, name string) (dao.Stage, error) {
					return dao.Stage{}, errors.New("stage not found")
				},
			)
			err := svc.Report(ctx, event)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "get Stage[test] info failed")
		})

		It("error: duplicate report", func() {
			releaseHistory.CreatedTime = time.Now()
			patches.ApplyFunc(
				cacheimpls.GetReleaseHistory,
				func(ctx context.Context, publishID int64) (dao.ReleaseHistory, error) {
					return releaseHistory, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetStage,
				func(ctx context.Context, gatewayID int64, name string) (dao.Stage, error) {
					return stage, nil
				},
			)
			mockPublishEventManager.EXPECT().Create(ctx, gomock.Any()).Return(
				int64(0),
				&mysql.MySQLError{
					Number: database.DuplicateErrCode,
				})
			err := svc.Report(ctx, event)
			assert.Error(GinkgoT(), err)
			assert.Contains(GinkgoT(), err.Error(), "create event failed, err:")
		})
		It("ok: report success", func() {
			releaseHistory.CreatedTime = time.Now()
			patches.ApplyFunc(
				cacheimpls.GetReleaseHistory,
				func(ctx context.Context, publishID int64) (dao.ReleaseHistory, error) {
					return releaseHistory, nil
				},
			)
			patches.ApplyFunc(
				cacheimpls.GetStage,
				func(ctx context.Context, gatewayID int64, name string) (dao.Stage, error) {
					return stage, nil
				},
			)
			mockPublishEventManager.EXPECT().Create(ctx, gomock.Any()).Return(
				int64(1),
				nil)
			err := svc.Report(ctx, event)
			assert.NoError(GinkgoT(), err)
		})
	})

})
