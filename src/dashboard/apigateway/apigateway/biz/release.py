#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import time
from datetime import datetime
from typing import Any, Dict, List

from django.db.models import Max

from apigateway.biz.constants import RELEASE_GATEWAY_INTERVAL_SECOND
from apigateway.core.constants import (
    EVENT_FAIL_INTERVAL_TIME,
    GatewayStatusEnum,
    PublishEventStatusEnum,
    ReleaseHistoryStatusEnum,
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
    def get_release_history_id_to_latest_publish_event_map(release_history_ids: List[int]) -> Dict[int, PublishEvent]:
        """通过 release_history_ids 查询最新的一个发布事件"""
        # 需要按照 "publish_id", "step", "status" 升序 (django 默认 ASC) 排列，正确排列每个事件节点的不同状态事件
        publish_events = PublishEvent.objects.filter(publish_id__in=release_history_ids).order_by(
            "publish_id", "step", "status"
        )
        # here only get the latest publish event for each publish_id
        return {event.publish_id: event for event in publish_events}

    @staticmethod
    def list_publish_events_by_release_history_id(release_history_id: int) -> List[PublishEvent]:
        """通过 release_history_id 查询所有发布事件"""
        publish_events = PublishEvent.objects.filter(publish_id=release_history_id).order_by("step", "status")

        # 补全event（由于上报的事件之间时间很短，当时为了减少存储，减少了部分event上报） todo: 后续由底层补齐事件
        new_events = []
        steps = {event.step for event in publish_events}

        # 兼容历史数据,可能没有老的没有历史事件
        if not steps:
            return []

        max_step = max(steps)
        now = datetime.now().timestamp()
        # 按照step来归类确定事件完整程度来补齐event
        for step in sorted(steps):
            step_events = [event for event in publish_events if event.step == step]
            step_status_list = {event.status for event in step_events}

            if len(step_events) == 0:
                continue
            # 补全doing event
            if PublishEventStatusEnum.DOING.value not in step_status_list:
                doing_event = copy.copy(step_events[0])
                doing_event.pk = -step  # 这里避免id一样引起混淆，暂时id没有什么用
                doing_event.status = PublishEventStatusEnum.DOING.value
                new_events.append(doing_event)

            # 补全success 和 failure event
            if PublishEventStatusEnum.SUCCESS.value not in step_status_list and any(
                event.status == PublishEventStatusEnum.DOING.value for event in step_events
            ):
                if step != max_step:
                    success_event = copy.copy(step_events[0])
                    success_event.pk = -step
                    success_event.status = PublishEventStatusEnum.SUCCESS.value
                    new_events.append(success_event)

                # 如果到了最后一步并且超过了10min没有event认为失败
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
    def is_running(last_event: PublishEvent):
        """通过最新的一个event判断当前发布是否还在继续执行"""
        return last_event.status == PublishEventStatusEnum.DOING.value or (
            last_event.status
            == PublishEventStatusEnum.SUCCESS.value  # 如果不是最后一个事件,如果是success的话说明也是running
            and not last_event.is_last
        )

    @staticmethod
    def get_status(last_event: PublishEvent):
        """通过end event来返回release_history状态"""
        # 如果状态是Doing并且该状态已经过去了10min,这种也认失败
        now = datetime.now().timestamp()
        if last_event.status == PublishEventStatusEnum.DOING.value and now - last_event.created_time.timestamp() > 600:
            return ReleaseHistoryStatusEnum.FAILURE.value

        # 如果是成功但不是最后一个节点并且该状态已经过去了10min,这种也认失败
        if (
            last_event.status == PublishEventStatusEnum.SUCCESS.value and not last_event.is_last
        ) and now - last_event.created_time.timestamp() > EVENT_FAIL_INTERVAL_TIME:
            return ReleaseHistoryStatusEnum.FAILURE.value

        # 如果还在执行中
        if ReleaseHandler.is_running(last_event):
            return ReleaseHistoryStatusEnum.DOING.value

        # 如已经结束
        if last_event.status == PublishEventStatusEnum.SUCCESS.value:
            return ReleaseHistoryStatusEnum.SUCCESS.value

        if last_event.status == PublishEventStatusEnum.FAILURE.value:
            return ReleaseHistoryStatusEnum.FAILURE.value

        return ReleaseHistoryStatusEnum.DOING.value

    @staticmethod
    def batch_get_stage_release_status(stage_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量查询 stage 的当前状态 (发布状态+publish_id)"""
        """return {"stage_id":{"status"/"publish_id"}}"""

        # 获取多个 stage_id 对应的最新的 ReleaseHistory 记录的 id
        latest_release_history_ids = (
            ReleaseHistory.objects.filter(stage_id__in=stage_ids)
            .annotate(latest_created_time=Max("created_time"))
            .values_list("id", flat=True)
        )

        # 查询最新的 ReleaseHistory 记录
        latest_release_histories = ReleaseHistory.objects.filter(id__in=latest_release_history_ids).all()

        # 查询发布历史对应的最新发布事件
        publish_id_to_latest_event_map = ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
            latest_release_history_ids
        )

        # 遍历结果集
        stage_publish_status = {}
        for release_history in latest_release_histories:
            stage_id = release_history.stage_id
            publish_id = release_history.id

            state = {"publish_id": publish_id}
            # 如果没有查到任何发布事件
            if publish_id not in publish_id_to_latest_event_map:
                # 兼容以前，使用以前的状态
                state["status"] = release_history.status
            else:
                latest_event = publish_id_to_latest_event_map[publish_id]
                state["status"] = ReleaseHandler.get_status(latest_event)

            stage_publish_status[stage_id] = state

        return stage_publish_status

    @staticmethod
    def filter_released_gateway_ids(gateway_ids: List[int]) -> List[int]:
        return list(set(Release.objects.filter(gateway_id__in=gateway_ids).values_list("gateway_id", flat=True)))

    @staticmethod
    def wait_another_release_done(release_history: ReleaseHistory):
        """等待上一个最近的发布任务执行完成"""

        # 获取最近的一个发布历史
        other_latest_release = (
            ReleaseHistory.objects.filter(
                gateway_id=release_history.gateway_id, stage_id=release_history.stage_id, id__lt=release_history.id
            )
            .order_by("-created_time")
            .first()
        )

        if other_latest_release is None:
            return

        # 获取其发布状态
        # 查询发布历史对应的最新发布事件
        has_another_release_doing = True
        start_time = datetime.now().timestamp()
        while has_another_release_doing:
            # 如果等待时间超过10*RELEASE_GATEWAY_INTERVAL_SECOND就退出等待
            now = datetime.now().timestamp()
            if now - start_time > 10 * RELEASE_GATEWAY_INTERVAL_SECOND:
                break

            time.sleep(0.1)
            other_latest_release_event_map = ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
                [other_latest_release.id]
            )
            latest_event = other_latest_release_event_map.get(other_latest_release.id, None)
            if latest_event:
                has_another_release_doing = (
                    ReleaseHandler.get_status(latest_event) == ReleaseHistoryStatusEnum.DOING.value
                )
                continue
            # 如果还没生成事件,就判断之间的时间间隔
            release_interval = release_history.created_time - other_latest_release.created_time
            # 获取时间间隔的总秒数
            release_interval_in_seconds = release_interval.total_seconds()
            has_another_release_doing = release_interval_in_seconds < RELEASE_GATEWAY_INTERVAL_SECOND
