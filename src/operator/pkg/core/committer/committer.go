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

// Package committer provides the functionality to commit changes
package committer

import (
	"context"
	"encoding/json"
	"sync"

	"go.uber.org/zap"

	"operator/pkg/core/agent/timer"
	"operator/pkg/core/registry"
	"operator/pkg/core/synchronizer"
	"operator/pkg/entity"
	"operator/pkg/eventreporter"
	"operator/pkg/logging"
	"operator/pkg/metric"
	"operator/pkg/trace"
	"operator/pkg/utils"
)

const maxStageRetryCount = 3

// Committer ...
type Committer struct {
	apigwEtcdRegistry  *registry.APIGWEtcdRegistry
	commitResourceChan chan []*entity.ReleaseInfo

	synchronizer *synchronizer.ApisixConfigSynchronizer

	releaseTimer *timer.ReleaseTimer

	logger *zap.SugaredLogger

	// Gateway stage dimension
	gatewayStageChanMap     map[string]chan struct{}
	gatewayStageChanMapLock *sync.RWMutex
}

// NewCommitter 创建 Committer
// commitChanSize: buffer size for commit resource channel, use 0 for unbuffered (not recommended)
func NewCommitter(
	apigwEtcdRegistry *registry.APIGWEtcdRegistry,
	synchronizer *synchronizer.ApisixConfigSynchronizer,
	releaseTimer *timer.ReleaseTimer,
	commitChanSize int,
) *Committer {
	// Ensure minimum buffer size to avoid blocking
	if commitChanSize <= 0 {
		commitChanSize = 100 // default buffer size
	}
	return &Committer{
		apigwEtcdRegistry: apigwEtcdRegistry, // Registry for resource management
		commitResourceChan: make(
			chan []*entity.ReleaseInfo,
			commitChanSize,
		), // Buffered channel for committing resource information
		synchronizer: synchronizer,                           // Configuration synchronizer
		releaseTimer: releaseTimer,                           // Timer for stage management
		logger:       logging.GetLogger().Named("committer"), // Logger instance named "committer"
		gatewayStageChanMap: make(
			map[string]chan struct{},
		), // Map for storing gateway stage channels
		gatewayStageChanMapLock: &sync.RWMutex{},
	}
}

// Run ...
func (c *Committer) Run(ctx context.Context) {
	// 分批次处理需要同步的 resource
	for {
		c.logger.Debugw("committer waiting for commit command")
		select {
		case resourceList := <-c.commitResourceChan:
			c.logger.Infow("received commit command", "resourceList", len(resourceList))
			// 分批处理 resource，避免一次性处理过多 resource
			segmentLength := 10
			for offset := 0; offset < len(resourceList); offset += segmentLength {
				if offset+segmentLength > len(resourceList) {
					rawResource, err := json.Marshal(resourceList[offset:])
					if err != nil {
						c.logger.Errorw("marshal resource list failed", "err", err)
					}
					c.commitGroup(ctx, resourceList[offset:])
					c.logger.Infow(
						"Commit resource group done",
						"resourceList",
						string(rawResource),
					)
					break
				}
				rawResource, err := json.Marshal(resourceList[offset:(offset + segmentLength)])
				if err != nil {
					c.logger.Errorw("marshal resource list failed", "err", err)
				}
				c.commitGroup(ctx, resourceList[offset:(offset+segmentLength)])
				c.logger.Infow("Commit resource group done", "resourceList", string(rawResource))
			}

		case <-ctx.Done():
			c.logger.Info("gateway agent stopped, stop commit")
			return
		}
	}
}

// GetCommitChan 获取提交 channel
func (c *Committer) GetCommitChan() chan []*entity.ReleaseInfo {
	return c.commitResourceChan
}

// ForceCommit ...
func (c *Committer) ForceCommit(ctx context.Context, stageList []*entity.ReleaseInfo) {
	c.logger.Infow("force commit stage changes", "stageList", stageList)
	c.commitResourceChan <- stageList
}

func (c *Committer) commitGroup(ctx context.Context, releaseInfoList []*entity.ReleaseInfo) {
	c.logger.Debugw("Commit resource group", "resourceList", releaseInfoList)
	// batch write apisix conf to buffer
	wg := &sync.WaitGroup{}
	for _, resourceInfo := range releaseInfoList {
		wg.Add(1)
		tmpResourceInfo := resourceInfo
		// 判断是否是 global 资源：PluginMetadata 且 Stage 为空
		if tmpResourceInfo.IsGlobalResource() {
			// Global 资源需要单独处理
			utils.GoroutineWithRecovery(ctx, func() {
				defer wg.Done()
				c.logger.Infof("begin commit global resource: %s", tmpResourceInfo)
				c.commitGlobalResource(ctx, tmpResourceInfo)
				c.logger.Infof("end commit global resource: %s", tmpResourceInfo)
			})
		} else {
			// Stage 资源按 gateway 维度串行处理
			utils.GoroutineWithRecovery(ctx, func() {
				c.logger.Infof("begin commit gateway channel: %s", tmpResourceInfo.GetID())
				c.commitGatewayStage(ctx, tmpResourceInfo, wg)
				c.logger.Infof("end commit gateway channel: %s", tmpResourceInfo.GetID())
			})
		}
	}
	wg.Wait()
	c.logger.Debugw("Commit resource group done", "resourceList", releaseInfoList)
}

// 按照 gateway 的维度串行更新 etcd
func (c *Committer) commitGatewayStage(ctx context.Context, si *entity.ReleaseInfo, wg *sync.WaitGroup) {
	// NOTE: wg.Done() is called inside the goroutine, not here!
	// This ensures WaitGroup only completes after the actual work is done.
	c.gatewayStageChanMapLock.Lock()
	stageChan, ok := c.gatewayStageChanMap[si.GetGatewayName()]
	if !ok {
		stageChan = make(chan struct{}, 1)
		c.gatewayStageChanMap[si.GetGatewayName()] = stageChan
	}
	c.gatewayStageChanMapLock.Unlock()
	stageChan <- struct{}{}
	utils.GoroutineWithRecovery(ctx, func() {
		defer wg.Done() // Move wg.Done() here to ensure it's called after work completes
		// Control stage writes for each gateway to be serial
		c.logger.Infof("begin commit stage channel: %s", si.GetReleaseID())
		c.commitStage(ctx, si, stageChan)
		c.logger.Infof("end commit stage channel: %s", si.GetReleaseID())
	})
}

// CleanupGatewayChannel removes the channel for a gateway that is no longer needed
// This should be called when a gateway is deleted to prevent memory leaks
func (c *Committer) CleanupGatewayChannel(gatewayName string) {
	c.gatewayStageChanMapLock.Lock()
	defer c.gatewayStageChanMapLock.Unlock()
	if stageChan, ok := c.gatewayStageChanMap[gatewayName]; ok {
		// Drain the channel before deleting
		select {
		case <-stageChan:
		default:
		}
		delete(c.gatewayStageChanMap, gatewayName)
		c.logger.Infof("cleaned up gateway channel: %s", gatewayName)
	}
}

func (c *Committer) commitStage(ctx context.Context, si *entity.ReleaseInfo, stageChan chan struct{}) {
	// Ensure stageChan is always released, even if panic occurs
	stageChannelReleased := false
	defer func() {
		if !stageChannelReleased {
			select {
			case <-stageChan:
			default:
			}
		}
	}()

	// trace
	_, span := trace.StartTrace(si.Ctx, "committer.commitStage")
	defer span.End()

	span.AddEvent("committer.GetNativeApisixConfiguration")
	eventreporter.ReportParseConfigurationDoingEvent(ctx, si)
	// 直接从 etcd 获取原生 apisix 配置，无需转换
	apisixConf, err := c.GetStageReleaseNativeApisixConfiguration(ctx, si)
	if err != nil {
		c.logger.Error(err, "get native apisix configuration failed", "stageInfo", si)
		// retry
		c.retryStage(si)
		span.RecordError(err)
		eventreporter.ReportParseConfigurationFailureEvent(ctx, si, err)
		// 释放 channel
		<-stageChan
		stageChannelReleased = true
		return
	}
	eventreporter.ReportParseConfigurationSuccessEvent(ctx, si)
	eventreporter.ReportApplyConfigurationDoingEvent(ctx, si)

	span.AddEvent("committer.Sync")
	err = c.synchronizer.Sync(
		ctx,
		si.GetGatewayName(),
		si.GetStageName(),
		apisixConf,
	)
	if err != nil {
		c.logger.Error(err, "sync apisix configuration failed", "stageInfo", si)
		// retry
		c.retryStage(si)
		span.RecordError(err)
		eventreporter.ReportApplyConfigurationFailureEvent(ctx, si, err)
		// 释放 channel
		<-stageChan
		stageChannelReleased = true
		return
	}
	// eventrepoter.ReportApplyConfigurationSuccessEvent(ctx, stage) // 可以由事件之前的关系推断出来
	// Mark as released since ReportLoadConfigurationResultEvent will handle it
	stageChannelReleased = true
	eventreporter.ReportLoadConfigurationResultEvent(ctx, si, stageChan)
	c.logger.Infow("commit stage success", "stageInfo", si)
}

func (c *Committer) retryStage(si *entity.ReleaseInfo) {
	if si.RetryCount >= maxStageRetryCount {
		c.logger.Errorw("too many retries", "stageInfo", si)
		return
	}
	si.RetryCount++
	c.releaseTimer.Update(si)
}

// GetStageReleaseNativeApisixConfiguration 直接从 etcd 获取原生 apisix 配置
func (c *Committer) GetStageReleaseNativeApisixConfiguration(
	ctx context.Context,
	si *entity.ReleaseInfo,
) (*entity.ApisixStageResource, error) {
	// 直接从 etcd 获取原生 apisix 配置
	resources, err := c.apigwEtcdRegistry.ListStageResources(si)
	if err != nil {
		c.logger.Errorf("get native apisix[stage:%s] configuration failed: %v", si.GetStageKey(), err)
		return nil, err
	}
	metric.ReportResourceCountHelper(
		si.GetGatewayName(),
		si.GetStageName(),
		resources,
		ReportResourceConvertedMetric,
	)
	return resources, nil
}

// GetGlobalApisixConfiguration 直接从 etcd 获取原生全局 apisix 配置
func (c *Committer) GetGlobalApisixConfiguration(
	ctx context.Context,
	si *entity.ReleaseInfo,
) (*entity.ApisixGlobalResource, error) {
	// 直接从 etcd 获取原生 apisix 配置
	resources, err := c.apigwEtcdRegistry.ListGlobalResources(si)
	if err != nil {
		c.logger.Errorf("get native apisix[global:%s] configuration failed: %v", si.GetStageKey(), err)
		return nil, err
	}
	return resources, nil
}

func (c *Committer) commitGlobalResource(ctx context.Context, si *entity.ReleaseInfo) {
	// trace
	_, span := trace.StartTrace(si.Ctx, "committer.commitGlobalResource")
	defer span.End()

	span.AddEvent("committer.GetGlobalApisixConfiguration")
	// 直接从 etcd 获取原生全局 apisix 配置，无需转换
	apisixGlobalConf, err := c.GetGlobalApisixConfiguration(ctx, si)
	if err != nil {
		c.logger.Error(err, "get native global apisix configuration failed", "globalInfo", si)
		// retry
		c.retryStage(si)
		span.RecordError(err)
		return
	}
	span.AddEvent("committer.SyncGlobal")
	err = c.synchronizer.SyncGlobal(
		ctx,
		apisixGlobalConf,
	)
	if err != nil {
		c.logger.Error(err, "sync global apisix configuration failed", "globalInfo", si)
		// retry
		c.retryStage(si)
		span.RecordError(err)
		return
	}
	c.logger.Infow("commit global resource success", "globalInfo", si)
}

// GetStageReleaseNativeApisixConfigurationByID 根据资源 ID 从 etcd 获取原生 apisix 配置
func (c *Committer) GetStageReleaseNativeApisixConfigurationByID(
	ctx context.Context,
	resourceID string,
	si *entity.ReleaseInfo,
) (*entity.ApisixStageResource, error) {
	// 直接从 etcd 获取原生 apisix 配置
	resources, err := c.apigwEtcdRegistry.GetStageResourceByID(resourceID, si)
	if err != nil {
		c.logger.Errorf("get native apisix[stage:%s] configuration failed: %v", si.GetStageKey(), err)
		return nil, err
	}
	metric.ReportResourceCountHelper(
		si.GetGatewayName(),
		si.GetStageName(),
		resources,
		ReportResourceConvertedMetric,
	)
	return resources, nil
}

// GetResourceCount 获取资源数量
func (c *Committer) GetResourceCount(
	ctx context.Context,
	si *entity.ReleaseInfo,
) (int64, error) {
	// 直接从 etcd 获取原生 apisix 配置
	count, err := c.apigwEtcdRegistry.Count(si)
	if err != nil {
		c.logger.Errorf("get native apisix[stage:%s] configuration failed: %v", si.GetStageKey(), err)
		return 0, err
	}
	return count, nil
}

// GetStageReleaseVersion 获取指定环境的发布版本信息
func (c *Committer) GetStageReleaseVersion(
	ctx context.Context,
	si *entity.ReleaseInfo,
) (*entity.ReleaseInfo, error) {
	// 直接从 etcd 获取原生 apisix 配置
	releaseVersionInfo, err := c.apigwEtcdRegistry.StageReleaseVersion(si)
	if err != nil {
		c.logger.Errorf("get native apisix[stage:%s] configuration failed: %v", si.GetStageKey(), err)
		return nil, err
	}
	return releaseVersionInfo, nil
}
