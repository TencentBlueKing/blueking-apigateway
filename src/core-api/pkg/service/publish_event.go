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
	"fmt"
	"time"

	"core/pkg/cacheimpls"
	"core/pkg/constant"
	"core/pkg/database/dao"
)

const (
	eventExpireTime = time.Hour
)

//go:generate mockgen -source=$GOFILE -destination=./mock/$GOFILE -package=mock

type PublishEventService interface {
	Report(ctx context.Context, event Event) error
}

type publishEventService struct {
	publishEventManager dao.PublishEventManger
}

type Event struct {
	Gateway   string
	Stage     string
	Name      string
	Status    string
	PublishID int64
	DetailMap map[string]interface{}
}

var _ PublishEventService = publishEventService{}

func NewPublishEventService() PublishEventService {
	return &publishEventService{
		publishEventManager: dao.NewPublishEventManger(),
	}
}

func (p publishEventService) Report(ctx context.Context, event Event) error {
	// get release history info by publish id
	releaseHistory, err := cacheimpls.GetReleaseHistory(ctx, event.PublishID)
	if err != nil {
		return fmt.Errorf("gateway[%s] get Stage [%s] release history by publish_id:%d failed, err: %w",
			event.Gateway, event.Stage, event.PublishID, err)
	}
	// For events that have passed for a long time,  filter and lose it
	if time.Since(releaseHistory.CreatedTime) > eventExpireTime {
		return fmt.Errorf("gateway[%s] get Stage [%s] event has passed for a long time, publish id: %d",
			event.Gateway, event.Stage, event.PublishID)
	}
	// determine whether the event is reported
	// get Stage id
	stageInfo, err := cacheimpls.GetStage(ctx, releaseHistory.GatewayID, event.Stage)
	if err != nil {
		return fmt.Errorf("gateway[%s] get Stage[%s] info failed, err: %w", event.Gateway, event.Stage, err)
	}

	// Is the event present in the cache
	key := cacheimpls.PublishEventKey{
		GatewayID: releaseHistory.GatewayID,
		StageID:   stageInfo.ID,
		PublishID: event.PublishID,
		Step:      constant.GetStep(event.Name),
		Status:    event.Status,
	}
	if cacheimpls.PublishEventExists(ctx, key) {
		return fmt.Errorf("event[%+v] has been reported", event)
	}

	// create event
	publishEvent := dao.PublishEvent{
		GatewayID:   releaseHistory.GatewayID,
		PublishID:   event.PublishID,
		StageID:     stageInfo.ID,
		Name:        event.Name,
		Status:      event.Status,
		Detail:      event.DetailMap,
		Step:        constant.GetStep(event.Name),
		CreatedTime: time.Now(),
		UpdatedTime: time.Now(),
	}
	_, err = p.publishEventManager.Create(ctx, publishEvent)
	if err != nil {
		return fmt.Errorf("create event failed, err: %w", err)
	}

	// set cache
	cacheimpls.PublishEventSet(ctx, key)
	return nil
}
