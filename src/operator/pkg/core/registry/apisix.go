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

// Package registry ...
package registry

import (
	"context"
	"errors"
	"fmt"
	"maps"
	"strings"
	"sync"
	"time"

	json "github.com/json-iterator/go"
	v3rpc "go.etcd.io/etcd/api/v3/v3rpc/rpctypes"
	clientv3 "go.etcd.io/etcd/client/v3"
	"go.uber.org/zap"

	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/logging"
)

type ApisixEtcdRegistry struct {
	client *clientv3.Client
	Prefix string // example: /apisix/routes

	mux             sync.RWMutex
	resources       map[string]entity.ApisixResource // resource id -> resource
	syncTimeout     time.Duration
	currentRevision int64

	// ctx for controlling the lifecycle of incrSync goroutine
	ctx    context.Context
	cancel context.CancelFunc

	logger *zap.SugaredLogger
}

// NewApisixEtcdRegistry creates a new ApisixEtcdRegistry instance
func NewApisixEtcdRegistry(ctx context.Context, client *clientv3.Client, prefix string,
	syncTimeout time.Duration,
) (*ApisixEtcdRegistry, error) {
	if !strings.HasSuffix(prefix, "/") {
		prefix += "/"
	}

	// Create a cancellable context for the incrSync goroutine
	registryCtx, cancel := context.WithCancel(ctx)

	apisixEtcdRegistry := &ApisixEtcdRegistry{
		client:      client,
		Prefix:      prefix,
		logger:      logging.GetLogger().Named("etcd-resource-store"),
		syncTimeout: syncTimeout,
		ctx:         registryCtx,
		cancel:      cancel,
	}

	apisixEtcdRegistry.logger.Infow("Create etcd resource store", "Prefix", prefix)

	err := apisixEtcdRegistry.fullSync(context.Background(), syncTimeout)
	if err != nil {
		cancel() // Clean up context on error
		apisixEtcdRegistry.logger.Error(err, "full sync failed")
		return nil, fmt.Errorf("init local resource store Prefix: %s error: %w", apisixEtcdRegistry.Prefix, err)
	}
	go apisixEtcdRegistry.incrSync()

	return apisixEtcdRegistry, nil
}

// Close stops the incrSync goroutine and releases resources
func (e *ApisixEtcdRegistry) Close() {
	if e.cancel != nil {
		e.cancel()
		e.logger.Infow("ApisixEtcdRegistry closed", "Prefix", e.Prefix)
	}
}

func (e *ApisixEtcdRegistry) fullSync(ctx context.Context, syncTimeout time.Duration) error {
	e.logger.Infow("etcdLocalResourceStore start full sync", "Prefix", e.Prefix)

	ctx, cancel := context.WithTimeout(ctx, syncTimeout)
	defer cancel()

	ret, err := e.client.Get(ctx, e.Prefix, clientv3.WithPrefix())
	if err != nil {
		e.logger.Error(err, "List resource from etcd failed")
		return err
	}

	e.mux.Lock()
	defer e.mux.Unlock()

	e.resources = make(map[string]entity.ApisixResource)

	for i := range ret.Kvs {
		resource, err := e.parseResource(ret.Kvs[i].Key, ret.Kvs[i].Value)
		if err != nil {
			e.logger.Errorf("Parse resource [key=%s,value=%s] from etcd failed: %v",
				ret.Kvs[i].Key, ret.Kvs[i].Value, err)
			continue
		}

		if resource == nil {
			continue
		}

		e.logger.Debugw("store resource", "key", string(ret.Kvs[i].Key), "resourceID",
			resource.GetID())
		e.resources[resource.GetID()] = resource
	}

	e.currentRevision = ret.Header.Revision
	return nil
}

func (e *ApisixEtcdRegistry) parseResource(key, value []byte) (resource entity.ApisixResource, err error) {
	if len(e.Prefix) == len(key) {
		return nil, nil
	}
	if string(value) == constant.SkippedValueEtcdInitDir ||
		string(value) == constant.SkippedValueEtcdEmptyObject {
		return nil, nil
	}

	parts := strings.Split(strings.Trim(e.Prefix, "/"), "/")
	if len(parts) == 0 {
		e.logger.Error("Invalid Prefix key", e.Prefix)
		return nil, fmt.Errorf("invalid Prefix key: %s", e.Prefix)
	}
	resourceType := parts[len(parts)-1]
	switch resourceType {
	case constant.ApisixResourceTypeRoutes:
		resource = &entity.Route{}
	case constant.ApisixResourceTypeServices:
		resource = &entity.Service{}
	case constant.ApisixResourceTypeSSL:
		resource = &entity.SSL{}
	case constant.ApisixResourceTypeProtos:
		resource = &entity.Proto{}
	case constant.ApisixResourceTypePluginMetadata:
		var metadata entity.ResourceMetadata
		err = json.Unmarshal(value, &metadata)
		if err != nil {
			e.logger.Errorf("Unmarshal resource [key=%s,value=%s] from etcd failed: %v",
				key, value, err)
			return nil, fmt.Errorf("unmarshal resource from etcd failed: %w", err)
		}
		resource = &entity.PluginMetadata{
			ResourceMetadata: metadata,
			PluginMetadataConf: entity.PluginMetadataConf{
				metadata.GetID(): value,
			},
		}
	default:
		e.logger.Errorw("Unknown resource type", "resourceType", resourceType)
		return nil, fmt.Errorf("unknown resource type: %s", resourceType)
	}
	if resourceType != constant.ApisixResourceTypePluginMetadata {
		err = json.Unmarshal(value, resource)
		if err != nil {
			e.logger.Errorf("Unmarshal resource [key=%s,value=%s] from etcd failed: %v",
				key, value, err)
			return nil, fmt.Errorf("unmarshal resource from etcd failed: %w", err)
		}
	}
	return resource, nil
}

// nolint: staticcheck
func (e *ApisixEtcdRegistry) incrSync() {
	c, cancel := context.WithCancel(e.ctx)
	var ch clientv3.WatchChan
	needCreateChan := true
	for {
		// Check if registry context is cancelled
		select {
		case <-e.ctx.Done():
			e.logger.Infow("incrSync stopped due to context cancellation", "Prefix", e.Prefix)
			cancel()
			return
		default:
		}

		if needCreateChan {
			ch = e.client.Watch(
				clientv3.WithRequireLeader(c),
				e.Prefix,
				clientv3.WithPrefix(),
				clientv3.WithPrevKV(),
				clientv3.WithRev(e.currentRevision),
			)
			needCreateChan = false
		}

		select {
		case <-e.ctx.Done():
			e.logger.Infow("incrSync stopped due to context cancellation", "Prefix", e.Prefix)
			cancel()
			return
		case event, ok := <-ch:
			if !ok || event.Err() != nil {
				e.logger.Errorf(
					"Watch event failed: %v, prefix: %s, revision: %d",
					event.Err(),
					e.Prefix,
					e.currentRevision,
				)

				time.Sleep(constant.SyncSleepSeconds)

				switch err := event.Err(); {
				case errors.Is(err, v3rpc.ErrCompacted), errors.Is(err, v3rpc.ErrFutureRev):
					err := e.fullSync(c, e.syncTimeout)
					if err != nil {
						time.Sleep(constant.SyncSleepSeconds)
						continue
					}
				}
				// reset channel
				needCreateChan = true
				cancel()
				c, cancel = context.WithCancel(e.ctx) //nolint:fatcontext
				break
			}
			// handler event
			for _, evt := range event.Events {
				err := e.handlerEvent(evt)
				if err != nil {
					e.logger.Errorf(
						"Handle event failed: %v, prefix: %s, revision: %d",
						err,
						e.Prefix,
						e.currentRevision,
					)
					continue
				}
			}
			e.currentRevision = event.Header.Revision
		}
	}
}

func (e *ApisixEtcdRegistry) handlerEvent(event *clientv3.Event) error {
	switch event.Type {
	case clientv3.EventTypePut:
		resource, err := e.parseResource(event.Kv.Key, event.Kv.Value)
		if err != nil {
			e.logger.Errorf("parse resource[key=%s,value=%s] from etcd failed:%v",
				event.Kv.Key, event.Kv.Value, err)
			return err
		}

		// skip empty resource on constant.SkippedValueEtcdInitDir or constant.SkippedValueEtcdEmptyObject
		if resource == nil {
			return nil
		}

		e.logger.Debugw(
			"Put resource",
			"key",
			string(event.Kv.Key),
			"resourceID",
			resource.GetID(),
		)
		e.mux.Lock()
		e.resources[resource.GetID()] = resource
		e.mux.Unlock()
	case clientv3.EventTypeDelete:
		resource, err := e.parseResource(event.PrevKv.Key, event.PrevKv.Value)
		if err != nil {
			e.logger.Errorf("parse resource[key=%s,value=%s] from etcd failed:%v",
				event.PrevKv.Key, event.PrevKv.Value, err)
			return err
		}

		if resource == nil {
			return fmt.Errorf("parse resource[key=%s,value=%s] from etcd failed: resource is nil",
				event.PrevKv.Key, event.PrevKv.Value)
		}

		e.logger.Debugw(
			"Delete resource",
			"key",
			string(event.Kv.Key),
			"resourceID",
			resource.GetID(),
		)
		e.mux.Lock()
		delete(e.resources, resource.GetID())
		e.mux.Unlock()
	}
	return nil
}

// GetStageResources returns all resources for a specific stage
func (e *ApisixEtcdRegistry) GetStageResources(stageName string) map[string]entity.ApisixResource {
	e.mux.RLock()
	defer e.mux.RUnlock()
	resources := make(map[string]entity.ApisixResource)
	for key, resource := range e.resources {
		if resource.GetReleaseInfo() == nil {
			continue
		}
		stageKey := resource.GetReleaseInfo().GetStageKey()
		if stageKey == stageName {
			resources[key] = resource
		}
	}
	return resources
}

// GetAllResources returns all resources from the registry
func (e *ApisixEtcdRegistry) GetAllResources() map[string]entity.ApisixResource {
	e.mux.RLock()
	defer e.mux.RUnlock()

	resources := make(map[string]entity.ApisixResource)
	maps.Copy(resources, e.resources)

	return resources
}
