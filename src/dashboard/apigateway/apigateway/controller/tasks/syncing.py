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
import logging
import uuid
from time import sleep

from celery import shared_task

from apigateway.biz.constants import RELEASE_GATEWAY_INTERVAL_SECOND
from apigateway.biz.release import ReleaseHandler
from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.constants import DELETE_PUBLISH_ID, NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.distributor.combine import CombineDistributor
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.models import MicroGateway, Release, ReleaseHistory

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def rolling_update_release(gateway_id: int, publish_id: int, release_id: int):
    """滚动同步微网关配置，不会生成新的版本"""

    release = Release.objects.get(id=release_id)

    is_cli_sync = publish_id is NO_NEED_REPORT_EVENT_PUBLISH_ID
    release_history = None if is_cli_sync else ReleaseHistory.objects.get(id=publish_id)

    # 事件上报要以release维度的stage来上报
    if release_history:
        release_history.stage = release.stage
        # 如果有正在发布则暂停RELEASE_GATEWAY_INTERVAL_SECOND，避免事件收敛导致发布事件丢失导致失败
        if ReleaseHandler.have_other_latest_release_doing(release_history):
            sleep(RELEASE_GATEWAY_INTERVAL_SECOND)

    PublishEventReporter.report_create_publish_task_success_event(release_history)

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

    PublishEventReporter.report_distribute_configuration_doing_event(release_history)

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
            PublishEventReporter.report_distribute_configuration_failure_event(release_history, err_msg)
        procedure_logger.info(msg)
    else:
        PublishEventReporter.report_distribute_configuration_success_event(release_history)
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

    # 如果有正在发布则暂停RELEASE_GATEWAY_INTERVAL_SECOND，避免事件收敛导致发布事件丢失导致失败
    if ReleaseHandler.have_other_latest_release_doing(release_history):
        sleep(RELEASE_GATEWAY_INTERVAL_SECOND)

    PublishEventReporter.report_create_publish_task_success_event(release_history)

    procedure_logger = ReleaseProcedureLogger(
        "revoke_release",
        logger=logger,
        gateway=release.gateway,
        stage=release.stage,
        micro_gateway=shared_gateway,
        publish_id=release_history.pk,
    )
    PublishEventReporter.report_distribute_configuration_doing_event(release_history)

    procedure_logger.info("revoke begin")

    is_success, err_msg = distributor.revoke(
        release, shared_gateway, procedure_logger.release_task_id, publish_id=release_history.pk
    )
    if not is_success:
        msg = f"revoke failed: {err_msg}"
        PublishEventReporter.report_distribute_configuration_failure_event(release_history, err_msg)
        procedure_logger.info(msg)
    else:
        PublishEventReporter.report_distribute_configuration_success_event(release_history)
        procedure_logger.info("revoke succeeded")
    return is_success
