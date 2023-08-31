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
from typing import List

from django.db.models import Max

from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusEnum,
    PublishSourceEnum,
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
    def save_release_history(release: Release, source: PublishSourceEnum, author: str) -> ReleaseHistory:
        """保存发布历史"""
        release_history = ReleaseHistory.objects.create(
            gateway=release.gateway,
            stage=release.stage,
            source=source.value,
            resource_version=release.resource_version,
            created_by=author,
        )
        return release_history

    @staticmethod
    def save_release_history_with_id(
        gateway_id: int, stage_id: int, resource_version_id: int, source: PublishSourceEnum, author: str
    ) -> ReleaseHistory:
        """保存发布历史"""
        release_history = ReleaseHistory.objects.create(
            gateway_id=gateway_id,
            stage_id=stage_id,
            source=source.value,
            resource_version_id=resource_version_id,
            created_by=author,
        )
        return release_history

    @staticmethod
    def batch_get_publish_event_by_release_history_ids(release_history_ids: List[int]) -> List[PublishEvent]:
        # 需要按照 "publish_id", "step", "status" 升序(django默认 ASC)排列,正确排列每个事件节点的不同状态事件
        publish_events = PublishEvent.objects.filter(publish_id__in=release_history_ids).order_by(
            "publish_id", "step", "status"
        )
        return publish_events

    @staticmethod
    def get_latest_publish_event_by_release_history_ids(release_history_ids: List[int]):
        """通过release_history_ids查询最新的一个发布事件"""

        publish_events = ReleaseHandler.batch_get_publish_event_by_release_history_ids(release_history_ids)

        return {event.publish_id: event for event in publish_events}

    @staticmethod
    def get_publish_events_by_release_history_id(release_history_id: int) -> List[PublishEvent]:
        """通过release_history_id查询所有发布事件"""

        publish_events = ReleaseHandler.batch_get_publish_event_by_release_history_ids([release_history_id])

        return list(publish_events)

    @staticmethod
    def batch_get_stage_release_status(stage_ids: List[int]):
        """批量查询stage的当前状态(发布状态+publish_id)"""
        """return {"stage_id":{"status"/"publish_id"}}"""

        # 获取多个 stage_id 对应的最新的 ReleaseHistory 记录的 id
        latest_release_history_ids = (
            ReleaseHistory.objects.filter(stage_id__in=stage_ids)
            .annotate(latest_created_time=Max("created_time"))
            .values_list("id", flat=True)
        )

        # 查询最新的 ReleaseHistory 记录
        latest_release_histories = ReleaseHistory.objects.filter(id__in=latest_release_history_ids)

        # 查询发布历史对应的最新发布事件
        release_event_map = ReleaseHandler.get_latest_publish_event_by_release_history_ids(latest_release_history_ids)

        # 遍历结果集
        stage_publish_status = {}
        for release_history in latest_release_histories:
            stage_publish_status[release_history.stage_id] = {"publish_id": release_history.id}
            # 如果没有查到任何发布事件
            if release_history.id not in release_event_map:
                # 兼容以前，使用以前的状态
                stage_publish_status[release_history.stage_id]["status"] = release_history.status
            else:
                # 如果最新事件状态是成功，但不是最后一个节点，返回发布中
                latest_event = release_event_map[release_history.id]
                if (
                    latest_event.status == PublishEventStatusEnum.SUCCESS.value
                    and latest_event.name != PublishEventNameTypeEnum.LOAD_CONFIGURATION.value
                ):
                    stage_publish_status[release_history.stage_id]["status"] = PublishEventStatusEnum.DOING.value
                else:
                    stage_publish_status[release_history.stage_id]["status"] = latest_event.status
        return stage_publish_status
