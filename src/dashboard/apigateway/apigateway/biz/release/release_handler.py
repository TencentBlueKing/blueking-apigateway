#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import OuterRef, Q, Subquery

from apigateway.core.constants import (
    EVENT_FAIL_INTERVAL_TIME,
    GatewayStatusEnum,
    PublishEventStatusEnum,
    ReleaseHistoryStatusEnum,
    ReleaseStatusEnum,
    StageStatusEnum,
)
from apigateway.core.models import Gateway, PublishEvent, Release, ReleaseHistory
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock

from .gateway_releaser import ReleaseError, release_gateway

logger = logging.getLogger(__name__)


class ReleaseHandler:
    @staticmethod
    def filter_release_history(
        gateway,
        query: str = "",
        stage_id: Optional[int] = None,
        created_by: str = "",
        time_start=None,
        time_end=None,
        order_by: Optional[str] = None,
        fuzzy: bool = False,
    ):
        queryset = ReleaseHistory.objects.filter(gateway=gateway)

        # query 不是模型字段，仅支持模糊匹配，如需精确匹配，可使用具体字段
        if query and fuzzy:
            queryset = queryset.filter(Q(stage__name__contains=query) | Q(resource_version__version__contains=query))

        if stage_id:
            queryset = queryset.filter(stage_id=stage_id)

        if created_by:
            if fuzzy:
                queryset = queryset.filter(created_by__contains=created_by)
            else:
                queryset = queryset.filter(created_by=created_by)

        if time_start and time_end:
            # time_start、time_end 须同时存在，否则无效
            queryset = queryset.filter(created_time__range=(time_start, time_end))

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset.select_related("data_plane", "resource_version", "stage").distinct()

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
    def get_release_status(release_history_id: int) -> str:
        """根据 release_history_id 查询发布状态"""
        event = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map([release_history_id]).get(
            release_history_id, None
        )
        if event:
            return event.get_release_history_status()

        return ReleaseHistoryStatusEnum.FAILURE.value

    @staticmethod
    def release_to_stages(
        gateway: Gateway, resource_version_id: int, stage_ids: List[int], username: str, comment: str
    ) -> Tuple[bool, str]:
        try:
            for stage_id in stage_ids:
                with Lock(
                    f"{gateway.id}_{stage_id}",
                    timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                    try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
                ):
                    release_gateway(
                        gateway=gateway,
                        stage_id=stage_id,
                        resource_version_id=resource_version_id,
                        username=username,
                        comment=comment,
                    )
        except (LockTimeout, ReleaseError) as err:
            return False, str(err)

        return True, ""

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
        # FIXME: 每个对应的 release 如果直接关联了对应的 release_history 就不需要通过这种方式去查了
        latest_release_history_id = (
            ReleaseHistory.objects.filter(stage_id=OuterRef("stage_id")).order_by("-id").values("id")[:1]
        )
        latest_release_histories = list(
            ReleaseHistory.objects.filter(
                stage_id__in=stage_ids,
                id=Subquery(latest_release_history_id),
            ).select_related("resource_version")
        )
        latest_release_history_ids = [release_history.id for release_history in latest_release_histories]

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
                "resource_version_id": release_history.resource_version_id,
                "resource_version_display": release_history.resource_version.object_display,
            }
            # 如果没有查到任何发布事件
            if publish_id not in publish_id_to_latest_event_map:
                state["status"] = ReleaseStatusEnum.PENDING.value
            else:
                latest_event = publish_id_to_latest_event_map[publish_id]
                state["status"] = latest_event.get_release_history_status()

            stage_publish_status[stage_id] = state

        return stage_publish_status

    @staticmethod
    def filter_released_gateway_ids(gateway_ids: List[int]) -> List[int]:
        return list(set(Release.objects.filter(gateway_id__in=gateway_ids).values_list("gateway_id", flat=True)))
