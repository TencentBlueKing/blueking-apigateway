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

// Package synchronizer provides the functionality to synchronize the API Gateway configuration.
package synchronizer

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

import (
	"context"
	"sync"

	"go.uber.org/zap"

	cfg "operator/pkg/config"
	"operator/pkg/core/store"
	"operator/pkg/entity"
	"operator/pkg/logging"
	"operator/pkg/metric"
)

// ApisixConfigSynchronizer synchronizes the API Gateway configuration.
type ApisixConfigSynchronizer struct {
	store    *store.ApisixEtcdStore
	flushMux sync.Mutex

	apisixHealthzURI string

	logger *zap.SugaredLogger
}

// NewSynchronizer create new Synchronizer
func NewSynchronizer(store *store.ApisixEtcdStore, apisixHealthzURI string) *ApisixConfigSynchronizer {
	syncer := &ApisixConfigSynchronizer{
		store:            store,
		apisixHealthzURI: apisixHealthzURI,
		logger:           logging.GetLogger().Named("apisix-config-synchronizer"),
	}
	return syncer
}

// Sync will sync new staged apisix configuration
func (as *ApisixConfigSynchronizer) Sync(
	ctx context.Context,
	gatewayName, stageName string,
	config *entity.ApisixStageResource,
) error {
	key := cfg.GenStagePrimaryKey(gatewayName, stageName)

	as.flushMux.Lock()
	defer as.flushMux.Unlock()

	as.logger.Debugw("flush changes", "key", key, "config", config)
	err := as.store.Alter(ctx, key, config)
	if err != nil {
		as.logger.Errorw("Failed to sync stage", "err", err, "key", key, "content", config)
		return err
	}

	metric.ReportStageConfigSyncMetric(gatewayName, stageName)

	return nil
}

// SyncGlobal 同步全局资源配置到 apisix etcd
func (as *ApisixConfigSynchronizer) SyncGlobal(
	ctx context.Context,
	config *entity.ApisixGlobalResource,
) error {
	as.flushMux.Lock()
	defer as.flushMux.Unlock()
	as.logger.Debugw("flush global changes", "config", config)
	err := as.store.AlterGlobal(ctx, config)
	if err != nil {
		as.logger.Errorw("Failed to sync global resource", "err", err, "content", config)
		return err
	}
	metric.ReportStageConfigSyncMetric("global", "global")

	as.logger.Debugw("flush virtual stage", "key", cfg.VirtualStageKey)
	virtualStage := NewVirtualStage(as.apisixHealthzURI)
	err = as.store.Alter(ctx, cfg.VirtualStageKey, virtualStage.MakeConfiguration())
	if err != nil {
		as.logger.Errorw(
			"Failed to sync virtual stage",
			"err", err, "key", cfg.VirtualStageKey,
			"content", virtualStage.MakeConfiguration(),
		)
		return err
	}
	return nil
}
