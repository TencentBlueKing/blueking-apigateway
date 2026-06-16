/*
 *  TencentBlueKing is pleased to support the open source community by making
 *  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 *  Copyright (C) Tencent. All rights reserved.
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

// Package store ...
package store

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"sync"
	"time"

	json "github.com/json-iterator/go"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.uber.org/zap"

	"operator/pkg/config"
	"operator/pkg/constant"
	"operator/pkg/core/differ"
	"operator/pkg/core/registry"
	"operator/pkg/entity"
	"operator/pkg/logging"
	"operator/pkg/metric"
	"operator/pkg/utils"
)

var apisixResourceTypes = []string{
	constant.ApisixResourceTypeRoutes,
	constant.ApisixResourceTypeServices,
	constant.ApisixResourceTypeSSL,
	constant.ApisixResourceTypePluginMetadata,
}

// ApisixEtcdStore ...
type ApisixEtcdStore struct {
	client *clientv3.Client
	prefix string

	registry map[string]*registry.ApisixEtcdRegistry
	differ   *differ.ConfigDiffer

	logger *zap.SugaredLogger

	putInterval time.Duration

	delInterval time.Duration

	syncTimeout time.Duration

	lock *sync.RWMutex

	// ctx for controlling the lifecycle of registry goroutines
	ctx    context.Context
	cancel context.CancelFunc
}

// NewApisixEtcdStore ...
func NewApisixEtcdStore(ctx context.Context, client *clientv3.Client, prefix string,
	putInterval, delInterval, syncTimeout time.Duration,
) (*ApisixEtcdStore, error) {
	// Create a cancellable context for managing registry lifecycles
	storeCtx, cancel := context.WithCancel(ctx)

	s := &ApisixEtcdStore{
		client:      client,
		prefix:      strings.TrimRight(prefix, "/"),
		registry:    make(map[string]*registry.ApisixEtcdRegistry, 4),
		differ:      differ.NewConfigDiffer(),
		logger:      logging.GetLogger().Named("etcd-config-store"),
		putInterval: putInterval,
		delInterval: delInterval,
		syncTimeout: syncTimeout,
		lock:        &sync.RWMutex{},
		ctx:         storeCtx,
		cancel:      cancel,
	}
	s.Init()

	s.logger.Infow("Create etcd config store", "prefix", prefix)

	if len(s.registry) != len(apisixResourceTypes) {
		cancel() // Clean up context on error
		s.logger.Error("Create etcd config store failed")
		return nil, fmt.Errorf("create etcd config store failed")
	}

	return s, nil
}

// Close stops all registry goroutines and releases resources
func (s *ApisixEtcdStore) Close() {
	if s.cancel != nil {
		s.cancel()
	}
	s.lock.RLock()
	defer s.lock.RUnlock()
	for _, reg := range s.registry {
		reg.Close()
	}
	s.logger.Infow("ApisixEtcdStore closed", "prefix", s.prefix)
}

// Init initializes the etcd config store
func (s *ApisixEtcdStore) Init() {
	wg := &sync.WaitGroup{}
	for _, resourceType := range apisixResourceTypes {
		wg.Add(1)

		// 避免闭包导致变量覆盖问题
		tempResourceType := resourceType
		utils.GoroutineWithRecovery(context.Background(), func() {
			defer wg.Done()
			apisixEtcdRegistry, err := registry.NewApisixEtcdRegistry(
				s.ctx, s.client, s.prefix+"/"+tempResourceType+"/", s.syncTimeout)
			if err != nil {
				s.logger.Errorw("Create resource store failed", "resourceType", tempResourceType)
				return
			}
			s.lock.Lock()
			defer s.lock.Unlock()
			s.registry[tempResourceType] = apisixEtcdRegistry
		})
	}
	wg.Wait()
}

// Get get a staged apisix configuration
func (s *ApisixEtcdStore) Get(stageKey string) *entity.ApisixStageResource {
	ret := entity.NewEmptyApisixConfiguration()
	routes := s.registry[constant.ApisixResourceTypeRoutes].GetStageResources(stageKey)
	for key, val := range routes {
		ret.Routes[key] = val.(*entity.Route) //nolint:forcetypeassert
	}
	services := s.registry[constant.ApisixResourceTypeServices].GetStageResources(stageKey)
	for key, val := range services {
		ret.Services[key] = val.(*entity.Service) //nolint:forcetypeassert
	}
	ssls := s.registry[constant.ApisixResourceTypeSSL].GetStageResources(stageKey)
	for key, val := range ssls {
		ret.SSLs[key] = val.(*entity.SSL) //nolint:forcetypeassert
	}
	return ret
}

// GetAll get staged apisix configuration map
func (s *ApisixEtcdStore) GetAll() map[string]*entity.ApisixStageResource {
	configMap := make(map[string]*entity.ApisixStageResource)
	routeMap := s.registry[constant.ApisixResourceTypeRoutes].GetAllResources()
	for key, route := range routeMap {
		stageName := route.GetStageName()
		if _, ok := configMap[stageName]; !ok {
			configMap[stageName] = entity.NewEmptyApisixConfiguration()
		}
		configMap[stageName].Routes[key] = route.(*entity.Route) //nolint:forcetypeassert
	}

	serviceMap := s.registry[constant.ApisixResourceTypeServices].GetAllResources()
	for key, service := range serviceMap {
		stageName := service.GetStageName()
		if _, ok := configMap[stageName]; !ok {
			configMap[stageName] = entity.NewEmptyApisixConfiguration()
		}
		configMap[stageName].Services[key] = service.(*entity.Service) //nolint:forcetypeassert
	}

	sslMap := s.registry[constant.ApisixResourceTypeSSL].GetAllResources()
	for key, ssl := range sslMap {
		stageName := ssl.GetStageName()
		if _, ok := configMap[stageName]; !ok {
			configMap[stageName] = entity.NewEmptyApisixConfiguration()
		}
		configMap[stageName].SSLs[key] = ssl.(*entity.SSL) //nolint:forcetypeassert
	}
	return configMap
}

// Alter ...
func (s *ApisixEtcdStore) Alter(
	ctx context.Context,
	stageKey string,
	config *entity.ApisixStageResource,
) error {
	st := time.Now()
	err := s.alterByStage(ctx, stageKey, nil, config)

	// metric
	metric.ReportStageConfigAlterMetric(stageKey, config, st, err)

	if err != nil {
		s.logger.Errorw("Alter by stage failed", "err", err, "stage", stageKey)
		return err
	}

	return nil
}

// AlterForRelease syncs one stage config and keeps release context in logs.
func (s *ApisixEtcdStore) AlterForRelease(
	ctx context.Context,
	releaseInfo *entity.ReleaseInfo,
	config *entity.ApisixStageResource,
) error {
	stageKey := releaseInfo.GetStageKey()
	st := time.Now()
	err := s.alterByStage(ctx, stageKey, releaseInfo, config)

	// metric
	metric.ReportStageConfigAlterMetric(stageKey, config, st, err)

	if err != nil {
		s.logger.Errorw("Alter by stage failed", "err", err, "stage", stageKey)
		return err
	}

	return nil
}

func (s *ApisixEtcdStore) alterByStage(
	ctx context.Context, stageKey string, releaseInfo *entity.ReleaseInfo, conf *entity.ApisixStageResource,
) (err error) {
	logFields := []any{"stage_key", stageKey}
	if releaseInfo != nil {
		logFields = append(releaseInfo.LogFields(), logFields...)
	}
	// get cached config
	oldConf := s.Get(stageKey)

	// diff config
	putConf, deleteConf := s.differ.Diff(oldConf, conf)

	var putFlag, delFlag bool
	// put resources
	if putConf != nil {
		if err = s.batchPutResource(ctx, constant.ApisixResourceTypeSSL, putConf.SSLs); err != nil {
			return fmt.Errorf("batch put ssl failed: %w", err)
		}
		if err = s.batchPutResource(ctx, constant.ApisixResourceTypeServices, putConf.Services); err != nil {
			return fmt.Errorf("batch put services failed: %w", err)
		}

		// sleep putInterVal to avoid resource data inconsistency
		time.Sleep(s.putInterval)

		if err = s.batchPutResource(ctx, constant.ApisixResourceTypeRoutes, putConf.Routes); err != nil {
			return fmt.Errorf("batch put routes failed: %w", err)
		}

		if len(putConf.Routes)+len(putConf.Services)+len(putConf.SSLs) > 0 {
			s.logger.Infow(
				"put stage config",
				append(
					logFields,
					"route_count", len(putConf.Routes),
					"service_count", len(putConf.Services),
					"ssl_count", len(putConf.SSLs),
				)...,
			)
			putFlag = true
		}
	}

	// delete resources
	if deleteConf != nil {
		if err = s.batchDeleteResource(ctx, constant.ApisixResourceTypeRoutes, deleteConf.Routes); err != nil {
			return fmt.Errorf("batch delete routes failed: %w", err)
		}
		if err = s.batchDeleteResource(ctx, constant.ApisixResourceTypeSSL, deleteConf.SSLs); err != nil {
			return fmt.Errorf("batch delete ssl failed: %w", err)
		}

		if len(deleteConf.Services) > 0 {
			// sleep delInterval to avoid resource data inconsistency
			time.Sleep(s.delInterval)
			if err = s.batchDeleteResource(
				ctx,
				constant.ApisixResourceTypeServices,
				deleteConf.Services,
			); err != nil {
				return fmt.Errorf("batch delete service failed: %w", err)
			}
		}
		if len(deleteConf.Routes)+len(deleteConf.Services)+len(deleteConf.SSLs) > 0 {
			s.logger.Infow(
				"delete stage config",
				append(
					logFields,
					"route_count", len(deleteConf.Routes),
					"service_count", len(deleteConf.Services),
					"ssl_count", len(deleteConf.SSLs),
				)...,
			)
			delFlag = true
		}
	}

	if !putFlag && !delFlag {
		s.logger.Infow("stage config has no change", logFields...)
	}

	return nil
}

// GetGlobal 获取全局资源配置（从 apisix etcd 中获取所有没有 stage 标签的 plugin metadata）
func (s *ApisixEtcdStore) GetGlobal() *entity.ApisixGlobalResource {
	ret := entity.NewEmptyApisixGlobalResource()
	// 获取所有 plugin metadata，过滤出没有 stage 标签的（即 global 资源）
	pmMap := s.registry[constant.ApisixResourceTypePluginMetadata].GetAllResources()
	for key, pm := range pmMap {
		// Global 资源没有 stage 标签，stage 为空字符串
		if pm.GetStageName() == "" {
			ret.PluginMetadata[key] = pm.(*entity.PluginMetadata) //nolint:forcetypeassert
		}
	}
	return ret
}

// AlterGlobal 同步全局资源配置到 apisix etcd
func (s *ApisixEtcdStore) AlterGlobal(
	ctx context.Context,
	conf *entity.ApisixGlobalResource,
) error {
	st := time.Now()
	err := s.alterGlobal(ctx, conf)

	// metric
	metric.ReportStageConfigAlterMetric(config.GenStagePrimaryKey("apigw", "global_resource"), nil, st, err)

	if err != nil {
		s.logger.Errorw("Alter global resource failed", "err", err)
		return err
	}

	return nil
}

func (s *ApisixEtcdStore) alterGlobal(
	ctx context.Context, conf *entity.ApisixGlobalResource,
) (err error) {
	// get cached global config
	oldConf := s.GetGlobal()

	// diff config
	putConf, deleteConf := s.differ.DiffGlobal(oldConf, conf)

	var putFlag, delFlag bool
	// put resources
	if putConf != nil && len(putConf.PluginMetadata) > 0 {
		if err = s.batchPutResource(
			ctx,
			constant.ApisixResourceTypePluginMetadata,
			putConf.PluginMetadata,
		); err != nil {
			return fmt.Errorf("batch put global plugin metadata failed: %w", err)
		}
		putFlag = true
		s.logger.Infof(
			"put global plugin_metadata count:%d",
			len(putConf.PluginMetadata),
		)
	}

	// delete resources
	if deleteConf != nil && len(deleteConf.PluginMetadata) > 0 {
		if err = s.batchDeleteResource(
			ctx, constant.ApisixResourceTypePluginMetadata, deleteConf.PluginMetadata,
		); err != nil {
			return fmt.Errorf("batch delete global plugin metadata failed: %w", err)
		}
		delFlag = true
		s.logger.Infof(
			"delete global plugin_metadata count:%d",
			len(deleteConf.PluginMetadata),
		)
	}

	if !putFlag && !delFlag {
		s.logger.Infof("global resource has no change")
	}

	return nil
}

func (s *ApisixEtcdStore) batchPutResource(
	ctx context.Context, resourceType string, resources any,
) error {
	resourceStore := s.registry[resourceType]

	resourceIter := reflect.ValueOf(resources).MapRange()
	for resourceIter.Next() {
		// set create time from cache resource
		st := time.Now()
		key := resourceIter.Key().Interface().(string)                       //nolint:forcetypeassert
		resource := resourceIter.Value().Interface().(entity.ApisixResource) //nolint:forcetypeassert
		if resource.GetCreateTime() == 0 {
			resource.SetCreateTime(st.Unix())
		}
		resource.SetUpdateTime(st.Unix())
		// remove unused fields
		resource.ClearUnusedFields()
		bytes, err := json.Marshal(resource)
		if err != nil {
			s.logger.Error(
				"Marshal resource failed",
				"err",
				err,
				"resourceType",
				resourceType,
				"resourceID",
				resource.GetID(),
			)
			return fmt.Errorf("marshal resource failed: %w", err)
		}

		s.logger.Debugw("Put resource to etcd", "resourceType", resourceType, "resourceID", resource.GetID())

		_, err = s.client.Put(ctx, resourceStore.Prefix+key, string(bytes))

		metric.ReportApisixEtcdMetric(resourceType, metric.ActionPut, st, err)

		if err != nil {
			s.logger.Errorw(
				"Put resource failed",
				"err",
				err,
				"resourceType",
				resourceType,
				"resourceID",
				resource.GetID(),
			)
			return fmt.Errorf("put resource failed: %w", err)
		}
	}
	return nil
}

func (s *ApisixEtcdStore) batchDeleteResource(
	ctx context.Context, resourceType string, resources any,
) error {
	resourceStore := s.registry[resourceType]
	resourceMap := reflect.ValueOf(resources).MapRange()
	for resourceMap.Next() {
		st := time.Now()

		key := resourceMap.Key().Interface().(string)                       //nolint:forcetypeassert
		resource := resourceMap.Value().Interface().(entity.ApisixResource) //nolint:forcetypeassert

		s.logger.Debugw(
			"Delete resource from etcd",
			"resourceType",
			resourceType,
			"resourceID",
			resource.GetID(),
		)

		_, err := s.client.Delete(ctx, resourceStore.Prefix+key)

		metric.ReportApisixEtcdMetric(resourceType, metric.ActionDelete, st, err)

		if err != nil {
			s.logger.Errorw(
				"Delete resource failed",
				"err",
				err,
				"resourceType",
				resourceType,
				"resourceID",
				resource.GetID(),
			)
			return fmt.Errorf("delete resource failed: %w", err)
		}
	}

	return nil
}
