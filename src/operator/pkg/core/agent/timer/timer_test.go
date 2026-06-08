// Package timer ...
/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

package timer

import (
	"context"
	"time"

	. "github.com/onsi/ginkgo/v2"
	"github.com/onsi/gomega"

	"operator/pkg/constant"
	"operator/pkg/entity"
)

var _ = Describe("Timer", func() {
	var (
		stageTimer *ReleaseTimer
		stageInfo  entity.ReleaseInfo
	)

	BeforeEach(func() {
		stageTimer = NewReleaseTimer()
		stageInfo = entity.ReleaseInfo{
			ResourceMetadata: entity.ResourceMetadata{
				Labels: &entity.LabelInfo{
					Gateway:       "gateway",
					Stage:         "stage",
					PublishId:     "1",
					ApisixVersion: "2.13.1",
				},
				ID:  "gateway-stage",
				Ctx: context.Background(),
			},

			PublishId:       1,
			PublishTime:     "2023-01-01T00:00:00Z",
			ApisixVersion:   "2.13.1",
			ResourceVersion: "1",
		}

		eventsWaitingTimeWindow = 100 * time.Millisecond
	})

	AfterEach(func() {
		eventsWaitingTimeWindow = 2 * time.Second
	})

	It("should update the stage timer correctly", func() {
		stageTimer.Update(&stageInfo)
		stageTimer.Update(&stageInfo)
		stageList := stageTimer.ListReleaseForCommit()
		// no sleep for exceeding 100ms (eventsWaitingTimeWindow)
		gomega.Expect(stageList).To(gomega.HaveLen(0))
	})

	It("should list stages for commit correctly", func() {
		stageTimer.Update(&stageInfo)
		stageTimer.Update(&stageInfo)

		time.Sleep(200 * time.Millisecond)

		stageList := stageTimer.ListReleaseForCommit()
		gomega.Expect(stageList).To(gomega.HaveLen(1))
		gomega.Expect(stageList[0].ID).To(gomega.Equal(stageInfo.ID))
	})

	Describe("CacheTimer", func() {
		It("should reset timer correctly", func() {
			cacheTimer := &CacheTimer{ReleaseInfo: &stageInfo}
			cacheTimer.Reset(100 * time.Millisecond)

			gomega.Expect(cacheTimer.CachedTime).NotTo(gomega.BeZero())
			gomega.Expect(cacheTimer.ShouldCommitTime).NotTo(gomega.BeZero())
			gomega.Expect(cacheTimer.ShouldCommitTime.After(cacheTimer.CachedTime)).To(gomega.BeTrue())
		})

		It("should update timer correctly", func() {
			cacheTimer := &CacheTimer{ReleaseInfo: &stageInfo}
			cacheTimer.Reset(100 * time.Millisecond)
			oldCommitTime := cacheTimer.ShouldCommitTime

			time.Sleep(10 * time.Millisecond)
			cacheTimer.Update(100 * time.Millisecond)

			gomega.Expect(cacheTimer.ShouldCommitTime.After(oldCommitTime)).To(gomega.BeTrue())
		})
	})

	Describe("ReleaseTimer", func() {
		It("should handle global resource with PluginMetadata kind", func() {
			globalInfo := entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "",
						Stage:   "",
					},
					ID:   "plugin-metadata-1",
					Kind: constant.PluginMetadata,
					Ctx:  context.Background(),
				},
			}

			stageTimer.Update(&globalInfo)

			time.Sleep(200 * time.Millisecond)

			stageList := stageTimer.ListReleaseForCommit()
			gomega.Expect(stageList).To(gomega.HaveLen(1))
		})

		It("should handle multiple releases", func() {
			stageInfo1 := entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "gateway1",
						Stage:   "stage1",
					},
					ID:  "gateway1-stage1",
					Ctx: context.Background(),
				},
			}
			stageInfo2 := entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "gateway2",
						Stage:   "stage2",
					},
					ID:  "gateway2-stage2",
					Ctx: context.Background(),
				},
			}

			stageTimer.Update(&stageInfo1)
			stageTimer.Update(&stageInfo2)

			time.Sleep(200 * time.Millisecond)

			stageList := stageTimer.ListReleaseForCommit()
			gomega.Expect(stageList).To(gomega.HaveLen(2))
		})

		It("should replace existing release info on update", func() {
			stageInfo1 := entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "gateway",
						Stage:   "stage",
					},
					ID:  "gateway-stage",
					Ctx: context.Background(),
				},
				PublishId: 1,
			}
			stageInfo2 := entity.ReleaseInfo{
				ResourceMetadata: entity.ResourceMetadata{
					Labels: &entity.LabelInfo{
						Gateway: "gateway",
						Stage:   "stage",
					},
					ID:  "gateway-stage",
					Ctx: context.Background(),
				},
				PublishId: 2,
			}

			stageTimer.Update(&stageInfo1)
			stageTimer.Update(&stageInfo2)

			time.Sleep(200 * time.Millisecond)

			stageList := stageTimer.ListReleaseForCommit()
			gomega.Expect(stageList).To(gomega.HaveLen(1))
			gomega.Expect(stageList[0].PublishId).To(gomega.Equal(2))
		})

		It("should handle invalid type in sync.Map gracefully", func() {
			// Store an invalid type directly
			stageTimer.releaseTimer.Store("invalid-key", "invalid-value")

			// Should not panic and should clean up invalid entry
			stageList := stageTimer.ListReleaseForCommit()
			gomega.Expect(stageList).To(gomega.HaveLen(0))

			// Verify invalid entry was cleaned up
			_, exists := stageTimer.releaseTimer.Load("invalid-key")
			gomega.Expect(exists).To(gomega.BeFalse())
		})

		It("should force commit after forceUpdateTimeWindow", func() {
			// Set a very long waiting window but short force update window
			eventsWaitingTimeWindow = 10 * time.Second
			forceUpdateTimeWindow = 50 * time.Millisecond

			stageTimer.Update(&stageInfo)

			// Wait for force update window
			time.Sleep(100 * time.Millisecond)

			stageList := stageTimer.ListReleaseForCommit()
			gomega.Expect(stageList).To(gomega.HaveLen(1))

			// Reset
			forceUpdateTimeWindow = 30 * time.Second
		})
	})
})
