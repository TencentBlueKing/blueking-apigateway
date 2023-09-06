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
from typing import Optional, Tuple

from blue_krill.async_utils.django_utils import delay_on_commit
from celery import shared_task

from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.constants import DELETE_PUBLISH_ID, NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.distributor.combine import CombineDistributor
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishSourceEnum,
    PublishSourceTriggerPublishTypeMapping,
    StageStatusEnum,
    TriggerPublishType,
)
from apigateway.core.models import Gateway, MicroGateway, Release, ReleaseHistory

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def rolling_update_release(gateway_id: int, publish_id: int, release_id: int):
    """滚动同步微网关配置，不会生成新的版本"""
    is_cli_sync = publish_id is NO_NEED_REPORT_EVENT_PUBLISH_ID

    release = Release.objects.get(id=release_id)

    release_history = None if is_cli_sync else ReleaseHistory.objects.get(id=release_id)
    if release_history:
        PublishEventReporter.report_create_publish_task_success_event(release_history, release.stage)

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

    if release_history:
        PublishEventReporter.report_distribute_configuration_doing_event(release_history, release.stage)

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
            PublishEventReporter.report_distribute_configuration_failure_event(
                release_history, release.stage.pk, err_msg
            )
        procedure_logger.info(msg)
    else:
        if release_history:
            PublishEventReporter.report_distribute_configuration_success_event(release_history, release.stage)
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

    PublishEventReporter.report_create_publish_task_success_event(release_history, release.stage)

    procedure_logger = ReleaseProcedureLogger(
        "revoke_release",
        logger=logger,
        gateway=release.gateway,
        stage=release.stage,
        micro_gateway=shared_gateway,
        publish_id=release_history.pk,
    )
    PublishEventReporter.report_distribute_configuration_doing_event(release_history, release.stage)

    procedure_logger.info("revoke begin")

    is_success, err_msg = distributor.revoke(
        release, shared_gateway, procedure_logger.release_task_id, publish_id=release_history.pk
    )
    if not is_success:
        msg = f"revoke failed: {err_msg}"
        PublishEventReporter.report_distribute_configuration_failure_event(
            release_history, release_history.stage, err_msg
        )
        procedure_logger.info(msg)
    else:
        PublishEventReporter.report_distribute_configuration_success_event(release_history, release_history.stage)
        procedure_logger.info("revoke succeeded")
    return is_success


def _check_release_gateway(gateway_id: Optional[int] = None, release: Optional[Release] = None) -> Tuple[bool, str]:
    """网关发布校验"""

    # 剔除非微网关托管的网关
    if gateway_id:
        gateway = Gateway.objects.get(pk=gateway_id)
        if gateway.is_micro_gateway:
            msg = f"rolling_update_release: gateway(id={gateway_id}) not exist or is not a micro-gateway, skip"
            return False, msg

        if gateway.status != GatewayStatusEnum.ACTIVE.value:
            msg = f"rolling_update_release: gateway(id={gateway_id}) is not active, skip"
            return False, msg

    # 校验环境
    if release and not release.stage:
        msg = f"release(id={release.pk}) has not stage, ignored"
        return False, msg
    elif release and release.stage and release.stage.status != StageStatusEnum.ACTIVE.value:
        msg = f"release(id={release.pk})  stage(name={release.stage.name}) is not active, ignored"
        return False, msg

    return True, ""


def _save_release_history(release: Release, source: PublishSourceEnum, author: str) -> ReleaseHistory:
    """保存发布历史"""
    release_history = ReleaseHistory.objects.create(
        gateway=release.gateway,
        stage=release.stage,
        source=source.value,
        resource_version=release.resource_version,
        created_by=author,
    )
    return release_history


def _trigger_rolling_publish(
    source: PublishSourceEnum,
    author: str,
    gateway_id: int,
    stage_id: Optional[int] = None,
    is_sync: Optional[bool] = False,
):
    """触发网关滚动更新"""

    for release in Release.objects.filter(gateway_id=gateway_id).prefetch_related("stage"):
        # 如果是环境变量发布，需要过滤对应stage
        if stage_id and release.stage.pk != stage_id:
            continue

        release_history = ReleaseHistory()
        publish_id = NO_NEED_REPORT_EVENT_PUBLISH_ID
        is_cli_sync = source is PublishSourceEnum.CLI_SYNC
        if not is_cli_sync:
            # 如果不是手动同步就需要生成发布历史
            release_history = _save_release_history(release, source, author)
            publish_id = release_history.pk

        # 发布check
        check_release_result, msg = _check_release_gateway(gateway_id=gateway_id, release=release)
        if not check_release_result:
            logging.warning(msg)
            if not is_cli_sync:
                PublishEventReporter.report_config_validate_fail_event(release_history, release.stage, msg)
            continue
        else:
            if not is_cli_sync:
                PublishEventReporter.report_config_validate_success_event(release_history, release.stage)
        if not is_cli_sync:
            PublishEventReporter.report_create_publish_task_doing_event(release_history, release.stage)

        # 开始发布
        if is_sync:
            return rolling_update_release(gateway_id=gateway_id, publish_id=publish_id, release_id=release.pk)
        else:
            delay_on_commit(
                rolling_update_release,
                gateway_id=gateway_id,
                publish_id=publish_id,
                release_id=release.pk,
            )


def _trigger_revoke_disable_publish(
    source: PublishSourceEnum,
    author: str,
    gateway_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    is_sync: Optional[bool] = False,
):
    """触发撤销发布"""

    release_list = []
    if gateway_id:
        release_list = Release.objects.get_release_by_gateway_id(gateway_id)
    if stage_id:
        release_list = Release.objects.get_release_by_stage_id(stage_id)
    for release in release_list:
        # 创建发布历史
        release_history = _save_release_history(release, source, author)

        # 发布check
        check_result, msg = _check_release_gateway(gateway_id=gateway_id, release=release)

        # 上报发布配置校验事件
        if check_result:
            PublishEventReporter.report_config_validate_success_event(release_history, release.stage)
        else:
            logging.warning(msg)
            PublishEventReporter.report_config_validate_fail_event(release_history, release.stage, msg)
            continue

        PublishEventReporter.report_distribute_configuration_doing_event(release_history, release_history.stage)

        # 开始发布
        if is_sync:
            return revoke_release(release_id=release.id, publish_id=release_history.id, author=author, source=source)
        else:
            delay_on_commit(
                revoke_release, release_id=release.id, publish_id=release_history.id, author=author, source=source
            )


def _trigger_revoke_delete_publish(
    source: PublishSourceEnum,
    author: str,
    gateway_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    is_sync: Optional[bool] = False,
):
    """触发删除发布"""

    release_list = []
    if gateway_id:
        release_list = Release.objects.get_release_by_gateway_id(gateway_id)
    if stage_id:
        release_list = Release.objects.get_release_by_stage_id(stage_id)
    for release in release_list:
        # 开始发布
        if is_sync:
            return revoke_release(
                release_id=release.id, publish_id=NO_NEED_REPORT_EVENT_PUBLISH_ID, author=author, source=source
            )
        else:
            delay_on_commit(
                revoke_release,
                release_id=release.id,
                publish_id=NO_NEED_REPORT_EVENT_PUBLISH_ID,
                author=author,
                source=source,
            )


def trigger_gateway_publish(
    source: PublishSourceEnum,
    author: str,
    gateway_id: int,
    stage_id: Optional[int] = None,
    is_sync: Optional[bool] = False,
):
    """触发网关发布"""
    """
      source: 发布来源
      author: 发布者
      gateway_id: 网关id
      stage_id: 环境id
      is_sync: 同步异步
    """
    trigger_publish_type = PublishSourceTriggerPublishTypeMapping[source]
    if not trigger_publish_type:
        raise ValueError(f"source[{source}] is illegal")

    if trigger_publish_type == TriggerPublishType.TRIGGER_ROLLING_UPDATE_RELEASE:
        return _trigger_rolling_publish(source, author, gateway_id=gateway_id, stage_id=stage_id, is_sync=is_sync)

    if trigger_publish_type == TriggerPublishType.TRIGGER_REVOKE_DISABLE_RELEASE:
        return _trigger_revoke_disable_publish(source, author, gateway_id, stage_id, is_sync=is_sync)
    if trigger_publish_type == TriggerPublishType.TRIGGER_REVOKE_DELETE_RELEASE:
        return _trigger_revoke_delete_publish(source, author, gateway_id, stage_id, is_sync=is_sync)
