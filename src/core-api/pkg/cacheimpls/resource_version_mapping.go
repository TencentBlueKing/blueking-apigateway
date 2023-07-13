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

package cacheimpls

import (
	"context"
	"encoding/json"
	"errors"
	"strconv"

	"github.com/TencentBlueKing/gopkg/cache"
	jsoniter "github.com/json-iterator/go"

	"core/pkg/database/dao"
	"core/pkg/logging"
)

// ResourceVersionMappingKey is the key of resource version mapping
type ResourceVersionMappingKey struct {
	ID int64
}

// Key return the key string of resource version mapping
func (k ResourceVersionMappingKey) Key() string {
	return strconv.FormatInt(k.ID, 10)
}

func retrieveResourceVersionMapping(ctx context.Context, k cache.Key) (interface{}, error) {
	key := k.(ResourceVersionMappingKey)

	manager := dao.NewResourceVersionManager()

	releaseResources, err := manager.Get(ctx, key.ID)
	if err != nil {
		// TODO: wrap
		return nil, err
	}

	var releaseResourcesData []map[string]interface{}
	j := jsoniter.Config{UseNumber: true}.Froze()
	err = j.UnmarshalFromString(releaseResources.Data, &releaseResourcesData)
	if err != nil {
		// TODO: wrap
		return nil, err
	}

	resourceNameToID := make(map[string]int64, len(releaseResourcesData))
	for _, d := range releaseResourcesData {
		valueID := d["id"].(json.Number)

		id, err := valueID.Int64()
		if err != nil {
			return nil, err
		}

		resourceNameToID[d["name"].(string)] = id
	}

	logging.GetLogger().Debugw("retrieveResourceVersionMapping",
		"resourceVersionID", key.ID, "resourceNameToID", resourceNameToID)

	return resourceNameToID, nil
}

// GetResourceVersionMapping will get the resource version mapping from cache
// the mapping key is resource name, the value is resource id, resource_name => resource_id
func GetResourceVersionMapping(ctx context.Context, id int64) (resourceNameToID map[string]int64, err error) {
	key := ResourceVersionMappingKey{
		ID: id,
	}
	var value interface{}
	value, err = cacheGet(ctx, resourceVersionMappingCache, key)
	if err != nil {
		return
	}

	var ok bool
	resourceNameToID, ok = value.(map[string]int64)
	if !ok {
		err = errors.New("not map[string]int64 in cache")
		return
	}
	return
}
