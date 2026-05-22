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

// Package timer provides the functionality to manage the timer for the BlueKing API Gateway Operator.
package timer

import (
	"sync"
	"time"

	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/trace"
)

// CacheTimer ...
type CacheTimer struct {
	ReleaseInfo *entity.ReleaseInfo

	CachedTime       time.Time
	ShouldCommitTime time.Time
}

// Reset ...
func (t *CacheTimer) Reset(offset time.Duration) {
	t.CachedTime = time.Now()
	t.ShouldCommitTime = time.Now().Add(offset)
}

// Update ...
func (t *CacheTimer) Update(offset time.Duration) {
	t.ShouldCommitTime = time.Now().Add(offset)
}

// ReleaseTimer ...
type ReleaseTimer struct {
	releaseTimer sync.Map
}

// NewReleaseTimer ...
func NewReleaseTimer() *ReleaseTimer {
	return &ReleaseTimer{}
}

// Update ...
func (t *ReleaseTimer) Update(releaseInfo *entity.ReleaseInfo) {
	// trace
	ctx, span := trace.StartTrace(releaseInfo.Ctx, "timer.Update")
	releaseInfo.Ctx = ctx
	defer span.End()

	var timer *CacheTimer
	cacheKey := releaseInfo.GetReleaseID()
	// 全局资源
	if releaseInfo.Kind == constant.PluginMetadata {
		cacheKey = constant.GlobalResourceKey
	}
	timerInterface, ok := t.releaseTimer.Load(cacheKey)
	if !ok {
		timer = &CacheTimer{ReleaseInfo: releaseInfo}
		timer.Reset(eventsWaitingTimeWindow)
	} else {
		var typeOk bool
		timer, typeOk = timerInterface.(*CacheTimer)
		if !typeOk {
			// Handle unexpected type - create new timer
			timer = &CacheTimer{ReleaseInfo: releaseInfo}
			timer.Reset(eventsWaitingTimeWindow)
		} else {
			// end old releaseInfo trace
			_, span := trace.StartTrace(timer.ReleaseInfo.Ctx, "timer.Replace")
			span.End()

			timer.ReleaseInfo = releaseInfo
			timer.Update(eventsWaitingTimeWindow)
		}
	}
	t.releaseTimer.Store(cacheKey, timer)
}

// ListReleaseForCommit ...
func (t *ReleaseTimer) ListReleaseForCommit() []*entity.ReleaseInfo {
	releaseInfos := make([]*entity.ReleaseInfo, 0)
	t.releaseTimer.Range(func(key, timerInterface any) bool {
		timer, ok := timerInterface.(*CacheTimer)
		if !ok {
			// Skip invalid entries and clean them up
			t.releaseTimer.Delete(key)
			return true
		}
		if time.Since(timer.ShouldCommitTime) > 0 || time.Since(timer.CachedTime) > forceUpdateTimeWindow {
			releaseInfos = append(releaseInfos, timer.ReleaseInfo)
			t.releaseTimer.Delete(key)
		}
		return true
	})

	return releaseInfos
}
