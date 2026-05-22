/*
 *  TencentBlueKing is pleased to support the open source community by making
 *  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 *  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
 *  Licensed under the MIT License (the "License"); you may not use this file except
 *  in compliance with the License. You may obtain a copy of the License at
 *
 *      http://opensource.org/licenses/MIT
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under
 *  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 *  either express or implied. See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 *   We undertake not to change the open source license (MIT license) applicable
 *   to the current version of the project delivered to anyone in the future.
 */

// Package metric ...
package metric

import (
	"strings"
	"time"

	"operator/pkg/entity"
	"operator/pkg/logging"
)

// ReportApisixEtcdMetric ...
func ReportApisixEtcdMetric(resType, action string, started time.Time, err error) {
	result := ResultSuccess
	if err != nil {
		result = ResultFail
	}

	ApisixOperationCounter.WithLabelValues(resType, action, result).Inc()
	ApisixOperationHistogram.WithLabelValues(resType, action, result).
		Observe(float64(time.Since(started).Milliseconds()))
}

// ReportStageConfigSyncMetric ...
func ReportStageConfigSyncMetric(gateway, stage string) {
	SynchronizerEventCounter.WithLabelValues(gateway, stage).Inc()
}

// ReportStageConfigAlterMetric ...
func ReportStageConfigAlterMetric(
	stageKey string,
	config *entity.ApisixStageResource,
	started time.Time,
	err error,
) {
	parts := strings.Split(stageKey, ".")
	// 格式必须满足 "bk.release.{gateway}.{stage}"
	if len(parts) < 4 || parts[0] != "bk" || parts[1] != "release" {
		logging.GetLogger().Infow("Invalid stage key format", "stageKey", stageKey)
		return
	}
	// 动态提取 gateway 和 stage
	gateway := strings.Join(parts[2:len(parts)-1], ".")
	stage := parts[len(parts)-1]

	result := ResultSuccess
	if err != nil {
		result = ResultFail
	} else {
		ReportResourceCountHelper(gateway, stage, config, func(gateway, stage, resType string, count int) {
			ApisixResourceWrittenCounter.WithLabelValues(gateway, stage, resType).Add(float64(count))
		})
	}

	SynchronizerFlushingCounter.WithLabelValues(gateway, stage, result).Inc()
	SynchronizerFlushingHistogram.WithLabelValues(gateway, stage, result).
		Observe(float64(time.Since(started).Milliseconds()))
}

// ReportSyncCmpMetric ...
func ReportSyncCmpMetric(gateway, stage, resourceType string) {
	SyncCmpCounter.WithLabelValues(gateway, stage, resourceType).Inc()
}

// ReportSyncCmpDiffMetric ...
func ReportSyncCmpDiffMetric(gateway, stage, resourceType string) {
	SyncCmpDiffCounter.WithLabelValues(gateway, stage, resourceType).Inc()
}
