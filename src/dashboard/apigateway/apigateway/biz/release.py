#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import copy
from datetime import datetime
from typing import Any, Dict, List

from apigateway.core.constants import (
    EVENT_FAIL_INTERVAL_TIME,
    GatewayStatusEnum,
    PublishEventStatusEnum,
    StageStatusEnum,
)
from apigateway.core.models import PublishEvent, Release, ReleaseHistory


class ReleaseHandler:
    @staticmethod
    def get_released_stage_ids(gateway_ids: List[int]) -> List[int]:
        return list(
            Release.objects.filter(
                gateway_id__in=gateway_ids,
                gateway__status=GatewayStatusEnum.ACTIVE.value,
                stage__status=StageStatusEnum.ACTIVE.value,
            ).values_list("stage_id", flat=True)
        )

    @staticmethod
    def list_publish_events_by_release_history_id(release_history_id: int) -> List[PublishEvent]:
        """通过 release_history_id 查询所有发布事件"""
        publish_events = PublishEvent.objects.filter(publish_id=release_history_id).order_by("step", "status")

        # 补全 event（由于上报的事件之间时间很短，当时为了减少存储，减少了部分 event 上报）todo: 后续由底层补齐事件
        new_events = []
        steps = {event.step for event in publish_events}

        # 兼容历史数据，可能没有老的没有历史事件
        if not steps:
            return []

        max_step = max(steps)
        now = datetime.now().timestamp()
        # 按照 step 来归类确定事件完整程度来补齐 event
        for step in sorted(steps):
            step_events = [event for event in publish_events if event.step == step]
            step_status_list = {event.status for event in step_events}

            if len(step_events) == 0:
                continue
            # 补全 doing event
            if PublishEventStatusEnum.DOING.value not in step_status_list:
                doing_event = copy.copy(step_events[0])
                doing_event.pk = -step  # 这里避免 id 一样引起混淆，暂时 id 没有什么用
                doing_event.status = PublishEventStatusEnum.DOING.value
                new_events.append(doing_event)

            # 补全 success 和 failure event
            if PublishEventStatusEnum.SUCCESS.value not in step_status_list and any(
                event.status == PublishEventStatusEnum.DOING.value for event in step_events
            ):
                if step != max_step:
                    success_event = copy.copy(step_events[0])
                    success_event.pk = -step
                    success_event.status = PublishEventStatusEnum.SUCCESS.value
                    new_events.append(success_event)

                # 如果到了最后一步并且超过了 10min 没有 event 认为失败
                if (
                    step == max_step
                    and PublishEventStatusEnum.FAILURE.value not in step_status_list
                    and now - step_events[0].created_time.timestamp() > EVENT_FAIL_INTERVAL_TIME
                ):
                    fail_event = copy.copy(step_events[0])
                    fail_event.pk = -step
                    fail_event.status = PublishEventStatusEnum.FAILURE.value
                    new_events.append(fail_event)

        return sorted(list(publish_events) + new_events, key=lambda event: (event.step, event.status))

    @staticmethod
    def batch_get_stage_release_status(stage_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量查询 stage 的当前状态 (发布状态+publish_id+ 发布版本)"""
        """return {"stage_id":{"status"/"publish_id"}}"""

        # 获取多个 stage_id 对应的最新的 ReleaseHistory 记录
        # FIXME: 每个对应的release如果直接关联了对应的release_history就不需要通过这种方式去查了
        latest_release_histories = []
        latest_release_history_ids = []
        for stage_id in stage_ids:
            latest_release_history = ReleaseHistory.objects.filter(stage_id=stage_id).order_by("-id").first()
            if not latest_release_history:
                continue
            latest_release_histories.append(latest_release_history)
            latest_release_history_ids.append(latest_release_history.id)

        # 查询发布历史对应的最新发布事件
        publish_id_to_latest_event_map = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
            latest_release_history_ids
        )

        # 遍历结果集
        stage_publish_status = {}
        for release_history in latest_release_histories:
            stage_id = release_history.stage_id
            publish_id = release_history.id

            state = {
                "publish_id": publish_id,
                "resource_version_display": release_history.resource_version.object_display,
            }
            # 如果没有查到任何发布事件
            if publish_id not in publish_id_to_latest_event_map:
                # 兼容以前，使用以前的状态
                state["status"] = release_history.status
            else:
                latest_event = publish_id_to_latest_event_map[publish_id]
                state["status"] = latest_event.get_release_history_status()

            stage_publish_status[stage_id] = state

        return stage_publish_status

    @staticmethod
    def filter_released_gateway_ids(gateway_ids: List[int]) -> List[int]:
        return list(set(Release.objects.filter(gateway_id__in=gateway_ids).values_list("gateway_id", flat=True)))
