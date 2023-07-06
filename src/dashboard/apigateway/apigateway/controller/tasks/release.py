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
from typing import List

from celery import shared_task

from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.distributor.etcd import EtcdDistributor
from apigateway.controller.distributor.helm import HelmDistributor
from apigateway.controller.helm.chart import ChartHelper
from apigateway.controller.helm.release import ReleaseHelper
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import MicroGateway, MicroGatewayReleaseHistory, Release, ReleaseHistory

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def mark_release_history_status(release_history_id, status: str, message: str, stage_ids: List[int]):
    """更新 release history 的状态"""
    logger.debug(
        "mark release history status: %s, release_history_id: %s",
        status,
        release_history_id,
    )
    ReleaseHistory.objects.filter(id=release_history_id).update(status=status, message=message)
    # add  success event(only for success)
    if status == ReleaseStatusEnum.SUCCESS.value:
        for stage_id in stage_ids:
            PublishEventReporter.report_distribute_configuration_success_event(release_history_id, stage_id)


@shared_task(ignore_result=True)
def mark_release_history_failure(
    stage_ids: List[int], request=None, exc=None, traceback=None, release_history_id=None, *args, **kwargs
):
    """更新 release history 的状态为失败，并记录失败原因"""

    logger.error(
        "release to micro-gateway failed, release_history_id: %s",
        release_history_id,
        exc_info=exc,
    )

    if release_history_id is None:
        raise ValueError("release_history_id is None")

    history = ReleaseHistory.objects.get(id=release_history_id)
    stage_values = history.microgatewayreleasehistory_set.filter(status=ReleaseStatusEnum.FAILURE.value).values_list(
        "stage__name", flat=True
    )
    history.message = f"环境[{','.join(stage_values)}]发布失败，请联系管理员"
    history.status = ReleaseStatusEnum.FAILURE.value
    history.save()
    # add publish failure event
    for stage_id in stage_ids:
        PublishEventReporter.report_distribute_configuration_failure_event(history, stage_id)


def _release_gateway(
    distributor: BaseDistributor,
    micro_gateway_release_history_id: int,
    release: Release,
    micro_gateway: MicroGateway,
    procedure_logger: ReleaseProcedureLogger,
):
    """发布资源到微网关"""
    procedure_logger.info(f"release begin, micro_gateway_release_history_id({micro_gateway_release_history_id})")
    release_history_qs = MicroGatewayReleaseHistory.objects.filter(id=micro_gateway_release_history_id)
    release_history_qs_last = release_history_qs.last()
    # 表明发布已开始
    release_history_qs.update(status=ReleaseStatusEnum.RELEASING.value)
    # add publish event
    PublishEventReporter.report_create_publish_task_success_event(
        release_history_qs_last.release_history, release.stage
    )
    PublishEventReporter.report_distribute_configuration_doing_event(
        release_history_qs_last.release_history, release.stage
    )
    try:
        if distributor.distribute(
            release=release,
            micro_gateway=micro_gateway,
            release_task_id=procedure_logger.release_task_id,
            release_history_id=release_history_qs_last.release_history_id,
        ):
            release_history_qs.update(status=ReleaseStatusEnum.SUCCESS.value)
        else:
            release_history_qs.update(
                status=ReleaseStatusEnum.FAILURE.value,
                details={"message": "distribute failed"},
            )
    except Exception as err:
        # 记录失败原因
        procedure_logger.exception("release failed")
        # 更新失败状态
        release_history_qs.update(
            status=ReleaseStatusEnum.FAILURE.value,
            details={"message": f"error: {err}"},
        )
        # 异常抛出，让 celery 停止编排
        raise

    return True


@shared_task(ignore_result=True)
def release_gateway_by_helm(access_token: str, username, release_id, micro_gateway_release_history_id):
    """发布资源到专享网关"""
    logger.info(
        "release_gateway_by_helm: release_id=%s, micro_gateway_release_history_id=%s",
        release_id,
        micro_gateway_release_history_id,
    )
    release = Release.objects.prefetch_related("stage", "api", "resource_version").get(id=release_id)
    stage = release.stage
    micro_gateway = stage.micro_gateway
    procedure_logger = ReleaseProcedureLogger(
        "release_gateway_by_helm",
        logger=logger,
        gateway=release.api,
        stage=stage,
        micro_gateway=micro_gateway,
    )
    # 环境未绑定微网关
    if not micro_gateway:
        procedure_logger.warning("stage not bound to a micro-gateway, cannot release by helm.")
        return False

    # BkGatewayConfig 随着 micro-gateway 的 release 下发，所以无需包含
    return _release_gateway(
        distributor=HelmDistributor(
            chart_helper=ChartHelper(access_token=access_token),
            release_helper=ReleaseHelper(access_token=access_token),
            generate_chart=True,
            operator=username,
        ),
        micro_gateway_release_history_id=micro_gateway_release_history_id,
        release=release,
        micro_gateway=micro_gateway,
        procedure_logger=procedure_logger,
    )


@shared_task(ignore_result=True)
def release_gateway_by_registry(micro_gateway_id, release_id, micro_gateway_release_history_id):
    """发布资源到共享网关，为了使得类似环境变量等引用生效，同时会将所有配置都进行同步"""
    logger.info(
        "release_gateway_by_etcd: release_id=%s, micro_gateway_id=%s, micro_gateway_release_history_id=%s",
        release_id,
        micro_gateway_id,
        micro_gateway_release_history_id,
    )
    release = Release.objects.prefetch_related("stage", "api", "resource_version").get(id=release_id)
    micro_gateway = MicroGateway.objects.get(id=micro_gateway_id, is_shared=True)
    # 如果是共享实例对应的网关发布，同时将对应的实例资源下发
    include_gateway_global_config = release.api_id == micro_gateway.api_id
    procedure_logger = ReleaseProcedureLogger(
        "release_gateway_by_etcd",
        logger=logger,
        gateway=release.api,
        stage=release.stage,
        micro_gateway=micro_gateway,
    )
    return _release_gateway(
        distributor=EtcdDistributor(
            include_gateway_global_config=include_gateway_global_config,
            include_stage=True,  # 需要将release_id通过stage资源下发出去
        ),
        micro_gateway_release_history_id=micro_gateway_release_history_id,
        release=release,
        micro_gateway=micro_gateway,
        procedure_logger=procedure_logger,
    )
