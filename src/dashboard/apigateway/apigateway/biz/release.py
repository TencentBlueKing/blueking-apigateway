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

from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.components.paas import get_paas_deployment_result, get_paas_offline_result
from apigateway.core.constants import (
    EVENT_FAIL_INTERVAL_TIME,
    GatewayStatusEnum,
    PublishEventStatusEnum,
    PublishSourceEnum,
    ReleaseHistoryStatusEnum,
    ReleaseStatusEnum,
    StageStatusEnum,
)
from apigateway.core.models import Gateway, PublishEvent, Release, ReleaseHistory
from apigateway.utils.user_credentials import UserCredentials


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
    def get_release_status(release_history_id: int) -> str:
        """根据 release_history_id 查询发布状态"""
        event = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map([release_history_id]).get(
            release_history_id, None
        )
        if event:
            return event.get_release_history_status()

        return ReleaseHistoryStatusEnum.FAILURE.value

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
                state["status"] = ReleaseStatusEnum.PENDING.value
            else:
                latest_event = publish_id_to_latest_event_map[publish_id]
                state["status"] = latest_event.get_release_history_status()

            stage_publish_status[stage_id] = state

        return stage_publish_status

    @staticmethod
    def get_paas_deploy_result(
        gateway: Gateway, deploy_history: ProgrammableGatewayDeployHistory, user_credentials: UserCredentials
    ) -> Dict[str, Any]:
        """查询 paas 的deploy结果"""
        # 查询paas部署结果
        is_offline = deploy_history.source != PublishSourceEnum.VERSION_PUBLISH.value
        if not is_offline:
            return get_paas_deployment_result(
                app_code=gateway.name,
                module="default",
                deploy_id=deploy_history.deploy_id,
                user_credentials=user_credentials,
            )
        return get_paas_offline_result(
            app_code=gateway.name,
            module="default",
            deploy_id=deploy_history.deploy_id,
            user_credentials=user_credentials,
        )

    @staticmethod
    def get_stage_deploy_status(gateway: Gateway, stage_id: int, user_credentials: UserCredentials) -> Dict[str, Any]:
        """查询 stage 的deploy状态"""
        latest_deploy_history = ProgrammableGatewayDeployHistory()
        last_deploy_history = ProgrammableGatewayDeployHistory()
        # 查询当前deploy历史
        deploy_history = (
            ProgrammableGatewayDeployHistory.objects.filter(
                gateway=gateway,
                stage_id=stage_id,
            )
            .order_by("-id")
            .first()
        )
        stage_release = ReleasedResourceHandler.get_stage_release(gateway, [stage_id]).get(stage_id)
        # 正在发布版本状态
        latest_publish_status = ""
        latest_history_id = 0
        # 当前生效版本状态
        last_publish_status = ""
        if stage_release:
            # 优先使用与 stage_release 匹配的记录
            last_deploy_history = (
                ProgrammableGatewayDeployHistory.objects.filter(
                    gateway=gateway, stage_id=stage_id, version=stage_release["resource_version_display"]
                ).first()
                or deploy_history  # 回退到最新记录
            )
            # 查询当前生效环境的 release history
            last_release_history = ReleaseHistory.objects.filter(
                gateway=gateway, stage_id=stage_id, resource_version__version=stage_release["resource_version_display"]
            ).first()
            if last_release_history:
                last_publish_status = ReleaseHandler.get_release_status(last_release_history.id)

            # 如果 stage_release 的版本和 deploy_history的第一个不一致，说明正在发布
            if stage_release["resource_version_display"] != deploy_history.version:
                latest_deploy_history = deploy_history
                latest_publish_status = ReleaseHistoryStatusEnum.DOING.value

        if deploy_history and latest_publish_status != "":
            if not deploy_history.publish_id:
                latest_publish_status = ReleaseHistoryStatusEnum.DOING.value
            else:
                latest_publish_status = ReleaseHandler.get_release_status(deploy_history.publish_id)
                latest_history_id = deploy_history.publish_id

        if deploy_history:
            result = ReleaseHandler.get_paas_deploy_result(gateway, deploy_history, user_credentials)
            # 正在发布的话需要判断是否失败
            if latest_publish_status != "" and result.get("status", "") == "failed":
                latest_publish_status = ReleaseHistoryStatusEnum.FAILURE.value

            # 第一次发布
            if last_publish_status == "" and result.get("status", "") == "failed":
                last_deploy_history = deploy_history
                last_publish_status = ReleaseHistoryStatusEnum.FAILURE.value
            elif last_publish_status == "" and result.get("status", "") != "failed":
                latest_deploy_history = deploy_history
                if deploy_history.publish_id:
                    latest_publish_status = ReleaseHandler.get_release_status(deploy_history.publish_id)
                else:
                    latest_publish_status = ReleaseHistoryStatusEnum.DOING.value
        return {
            "latest_deploy_history": latest_deploy_history,
            "latest_history_id": latest_history_id,
            "latest_publish_status": latest_publish_status,
            "last_publish_status": last_publish_status,
            "last_deploy_history": last_deploy_history,
        }

    @staticmethod
    def batch_get_stage_deploy_status(
        gateway: Gateway, stage_ids: List[int], user_credentials: UserCredentials
    ) -> dict[int, dict[str, Any]]:
        """批量查询 stage 的deploy状态"""
        return {
            stage_id: ReleaseHandler.get_stage_deploy_status(gateway, stage_id, user_credentials)
            for stage_id in stage_ids
        }

    @staticmethod
    def filter_released_gateway_ids(gateway_ids: List[int]) -> List[int]:
        return list(set(Release.objects.filter(gateway_id__in=gateway_ids).values_list("gateway_id", flat=True)))
