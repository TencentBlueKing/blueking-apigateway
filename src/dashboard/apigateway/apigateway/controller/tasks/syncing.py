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
import logging
import time
import uuid
from datetime import datetime

from celery import shared_task

from apigateway.common.constants import RELEASE_GATEWAY_INTERVAL_SECOND
from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.constants import DELETE_PUBLISH_ID, NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.distributor.combine import CombineDistributor
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.constants import (
    PublishSourceEnum,
    ReleaseHistoryStatusEnum,
    StageStatusEnum,
)
from apigateway.core.models import MicroGateway, PublishEvent, Release, ReleaseHistory
from apigateway.utils.time import now_datetime

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def rolling_update_release(gateway_id: int, publish_id: int, release_id: int):
    """滚动同步微网关配置，不会生成新的版本"""

    release = Release.objects.get(id=release_id)

    is_cli_sync = publish_id is NO_NEED_REPORT_EVENT_PUBLISH_ID
    release_history = None if is_cli_sync else ReleaseHistory.objects.get(id=publish_id)

    # 事件上报要以 release 维度的 stage 来上报
    if release_history:
        release_history.stage = release.stage
        # 如果有正在发布则等待其发布完成，避免事件收敛导致发布事件丢失导致失败
        wait_another_release_done(release_history)

    PublishEventReporter.report_create_publish_task_success(release_history)

    logger.info("rolling_update_release[gateway_id=%d] begin", gateway_id)

    shared_gateway = MicroGateway.objects.get_default_shared_gateway()
    distributor = CombineDistributor()

    release_task_id = str(uuid.uuid4())

    procedure_logger = ReleaseProcedureLogger(
        "rolling_update_release",
        logger=logger,
        gateway=release.gateway,
        stage=release.stage,
        micro_gateway=shared_gateway,
        release_task_id=release_task_id,
        publish_id=publish_id,
    )

    PublishEventReporter.report_distribute_config_doing(release_history)

    procedure_logger.info("distribute begin")
    is_success, err_msg = distributor.distribute(
        release,
        micro_gateway=shared_gateway,
        release_task_id=release_task_id,
        publish_id=publish_id,
    )
    if not is_success:
        msg = f"distribute failed: {err_msg}"
        if not is_cli_sync:
            PublishEventReporter.report_distribute_config_failure(release_history, err_msg)
        procedure_logger.info(msg)

    else:
        # 更新 release 的发布时间和发布人
        release.updated_time = now_datetime()
        release.updated_by = release_history.created_by if release_history else "admin"
        release.save()

        # 如果是网关启用，需要更新环境状态
        if release_history and release_history.source == PublishSourceEnum.GATEWAY_ENABLE.value:
            stage = release.stage
            stage.status = StageStatusEnum.ACTIVE.value
            stage.save()

        PublishEventReporter.report_distribute_config_success(release_history)
        procedure_logger.info("distribute succeeded")

    return is_success


@shared_task(ignore_result=True)
def revoke_release(release_id: int, publish_id: int):
    """删除环境的已发布的资源"""

    release = Release.objects.get(id=release_id)

    shared_gateway = MicroGateway.objects.get_default_shared_gateway()

    distributor = CombineDistributor()
    if publish_id == DELETE_PUBLISH_ID:
        is_success, err_msg = distributor.revoke(release, shared_gateway, str(uuid.uuid4()), publish_id=publish_id)
        if not is_success:
            logger.error(err_msg)
        return is_success

    release_history = ReleaseHistory.objects.get(id=publish_id)

    # 如果有正在发布则等待其发布完成，避免事件收敛导致发布事件丢失导致失败
    wait_another_release_done(release_history)

    PublishEventReporter.report_create_publish_task_success(release_history)

    procedure_logger = ReleaseProcedureLogger(
        "revoke_release",
        logger=logger,
        gateway=release.gateway,
        stage=release.stage,
        micro_gateway=shared_gateway,
        publish_id=release_history.pk,
    )
    PublishEventReporter.report_distribute_config_doing(release_history)

    procedure_logger.info("revoke begin")

    is_success, err_msg = distributor.revoke(
        release, shared_gateway, procedure_logger.release_task_id, publish_id=release_history.pk
    )
    if not is_success:
        msg = f"revoke failed: {err_msg}"
        PublishEventReporter.report_distribute_config_failure(release_history, err_msg)
        procedure_logger.info(msg)
    else:
        PublishEventReporter.report_distribute_config_success(release_history)
        procedure_logger.info("revoke succeeded")
        # 修改对应环境状态
        stage = release.stage
        stage.status = StageStatusEnum.INACTIVE.value
        stage.save()

    return is_success


def wait_another_release_done(release_history: ReleaseHistory):
    """这里主要是为了避免并发发布过程中，如果同时发布导致 operator 事件收敛导致事件丢失，需要等待上一个最近的发布任务执行完成"""

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
    wait_times = 0
    while has_another_release_doing:
        # 如果等待时间超过 10*RELEASE_GATEWAY_INTERVAL_SECOND 就退出等待
        now = datetime.now().timestamp()
        if now - start_time > 10 * RELEASE_GATEWAY_INTERVAL_SECOND:
            break

        time.sleep(1 * wait_times)

        wait_times += 1
        other_latest_release_event_map = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
            [other_latest_release.id]
        )
        latest_event = other_latest_release_event_map.get(other_latest_release.id, None)
        if latest_event:
            has_another_release_doing = (
                latest_event.get_release_history_status() == ReleaseHistoryStatusEnum.DOING.value
            )
            continue
        # 如果还没生成事件，就判断之间的时间间隔
        release_interval = release_history.created_time - other_latest_release.created_time
        # 获取时间间隔的总秒数
        release_interval_in_seconds = release_interval.total_seconds()
        has_another_release_doing = release_interval_in_seconds < RELEASE_GATEWAY_INTERVAL_SECOND
