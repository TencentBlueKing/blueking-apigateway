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
import time
from datetime import datetime
from typing import Optional

from celery import shared_task

from apigateway.apps.support.models import ReleasedResourceDoc, ResourceDocVersion
from apigateway.biz.constants import RELEASE_GATEWAY_INTERVAL_SECOND
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.distributor.etcd import EtcdDistributor
from apigateway.controller.distributor.helm import HelmDistributor
from apigateway.controller.helm.chart import ChartHelper
from apigateway.controller.helm.release import ReleaseHelper
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.constants import ReleaseHistoryStatusEnum, ReleaseStatusEnum, StageStatusEnum
from apigateway.core.models import (
    MicroGateway,
    MicroGatewayReleaseHistory,
    Release,
    ReleasedResource,
    ReleaseHistory,
    ResourceVersion,
    Stage,
)
from apigateway.utils.time import now_datetime

logger = logging.getLogger(__name__)


def _release_gateway(
    distributor: BaseDistributor,
    micro_gateway_release_history_id: int,
    release: Release,
    micro_gateway: MicroGateway,
    procedure_logger: ReleaseProcedureLogger,
):
    """发布资源到微网关"""
    procedure_logger.info(
        f"release begin, micro_gateway_release_history_id({micro_gateway_release_history_id})"  # noqa: G004
    )
    release_history_qs = MicroGatewayReleaseHistory.objects.filter(id=micro_gateway_release_history_id)
    latest_micro_gateway_release_history = release_history_qs.last()
    # 表明发布已开始
    release_history_qs.update(status=ReleaseStatusEnum.RELEASING.value)
    # add publish event
    PublishEventReporter.report_create_publish_task_success_event(latest_micro_gateway_release_history.release_history)
    PublishEventReporter.report_distribute_configuration_doing_event(
        latest_micro_gateway_release_history.release_history
    )
    try:
        is_success, fail_msg = distributor.distribute(
            release=release,
            micro_gateway=micro_gateway,
            release_task_id=procedure_logger.release_task_id,
            publish_id=latest_micro_gateway_release_history.release_history_id,
        )
        if is_success:
            PublishEventReporter.report_distribute_configuration_success_event(
                latest_micro_gateway_release_history.release_history,
            )

        else:
            PublishEventReporter.report_distribute_configuration_failure_event(
                latest_micro_gateway_release_history.release_history, fail_msg
            )
            return False
    except Exception as err:
        # 记录失败原因
        procedure_logger.exception("release failed")
        # 上报失败事件
        PublishEventReporter.report_distribute_configuration_failure_event(
            latest_micro_gateway_release_history.release_history, f"error: {err}"
        )
        # 异常抛出，让 celery 停止编排
        raise

    return True


@shared_task(ignore_result=True)
def release_gateway_by_helm(release_id, micro_gateway_release_history_id, username, user_credentials):
    """发布资源到专享网关"""
    logger.info(
        "release_gateway_by_helm: release_id=%s, micro_gateway_release_history_id=%s",
        release_id,
        micro_gateway_release_history_id,
    )
    release = Release.objects.prefetch_related("stage", "gateway", "resource_version").get(id=release_id)
    stage = release.stage
    micro_gateway = stage.micro_gateway
    procedure_logger = ReleaseProcedureLogger(
        "release_gateway_by_helm",
        logger=logger,
        gateway=release.gateway,
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
            chart_helper=ChartHelper(user_credentials=user_credentials),
            release_helper=ReleaseHelper(user_credentials=user_credentials),
            generate_chart=True,
            operator=username,
        ),
        micro_gateway_release_history_id=micro_gateway_release_history_id,
        release=release,
        micro_gateway=micro_gateway,
        procedure_logger=procedure_logger,
    )


@shared_task(ignore_result=True)
def release_gateway_by_registry(
    micro_gateway_id, release_id, micro_gateway_release_history_id, publish_id: Optional[int] = None
):
    """发布资源到共享网关，为了使得类似环境变量等引用生效，同时会将所有配置都进行同步"""
    logger.info(
        "release_gateway_by_etcd: release_id=%s, micro_gateway_id=%s, micro_gateway_release_history_id=%s",
        release_id,
        micro_gateway_id,
        micro_gateway_release_history_id,
    )
    if not publish_id:
        logger.error(
            "release_gateway_by_etcd: release_id=%s, micro_gateway_id=%s, has no publish_id",
            release_id,
            micro_gateway_id,
        )
        return None

    release_history = ReleaseHistory.objects.get(id=publish_id)
    if not release_history:
        logger.error(
            "release_gateway_by_etcd:release_id=%s,micro_gateway_id=%s,can't find release_history: %s",
            release_id,
            micro_gateway_id,
            publish_id,
        )
        return None

    # 改成了延迟更新发布关联数据，这里的release数据需要构造才行
    release = Release.objects.save_release(
        gateway=release_history.gateway,
        stage=release_history.stage,
        resource_version=release_history.resource_version,
        comment=release_history.comment,
        username=release_history.created_by,
    )
    micro_gateway = MicroGateway.objects.get(id=micro_gateway_id, is_shared=True)
    # 如果是共享实例对应的网关发布，同时将对应的实例资源下发
    include_gateway_global_config = release.gateway_id == micro_gateway.gateway_id
    procedure_logger = ReleaseProcedureLogger(
        "release_gateway_by_etcd",
        logger=logger,
        gateway=release.gateway,
        stage=release.stage,
        micro_gateway=micro_gateway,
        release_task_id=micro_gateway_release_history_id,
        publish_id=publish_id,
    )
    return _release_gateway(
        distributor=EtcdDistributor(
            include_gateway_global_config=include_gateway_global_config,
        ),
        micro_gateway_release_history_id=micro_gateway_release_history_id,
        release=release,
        micro_gateway=micro_gateway,
        procedure_logger=procedure_logger,
    )


@shared_task(ignore_result=True)
def update_release_data_after_success(
    publish_id: int, release_id: int, resource_version_id: int, author: str, comment: str
):
    """
    发布后不断检查发布状态如果成功才更新相关数据
    """

    # 检测发布状态,只有最终发布成功才更新
    doing = True
    start_time = datetime.now().timestamp()
    wait_times = 0
    while doing:
        # 如果等待时间超过10*RELEASE_GATEWAY_INTERVAL_SECOND就退出等待
        now = datetime.now().timestamp()
        if now - start_time > 10 * RELEASE_GATEWAY_INTERVAL_SECOND:
            logger.error(
                "release[publish_id=%d,resource_version_id=%d}] check publish status timeout",
                publish_id,
                resource_version_id,
            )
            return

        time.sleep(1 * wait_times)
        wait_times += 1
        latest_release_event_map = ReleaseHandler.get_release_history_id_to_latest_publish_event_map([publish_id])
        latest_event = latest_release_event_map.get(publish_id)

        if not latest_event:
            logger.error(
                "release[publish_id=%d,resource_version_id=%d get latest event  fail", publish_id, resource_version_id
            )
            continue

        # 判断状态
        publish_status = ReleaseHandler.get_status(latest_event)

        if publish_status == ReleaseHistoryStatusEnum.SUCCESS.value:
            doing = False
        else:
            logger.debug(
                "release[publish_id=%d,resource_version_id=%d current status is %s",
                publish_id,
                resource_version_id,
                publish_status,
            )

    release = Release.objects.get(id=release_id)
    if not release:
        logger.error(
            "release[publish_id=%d,resource_version_id=%d get release[id=%d] fail",
            publish_id,
            resource_version_id,
            release_id,
        )
        return

    resource_version = ResourceVersion.objects.get(id=resource_version_id)
    if not resource_version:
        logger.error(
            "release[publish_id=%d,resource_version_id=%d get resource_version fail", publish_id, resource_version_id
        )
        return

    # update release
    release.resource_version = resource_version
    release.comment = comment
    release.updated_by = author
    release.updated_time = now_datetime()
    release.save()

    # activate stages
    Stage.objects.filter(id=release.stage.id).update(status=StageStatusEnum.ACTIVE.value)

    # update_and_clear_released_resources
    ReleasedResource.objects.save_released_resource(resource_version)
    ReleasedResourceHandler.clear_unreleased_resource(release.gateway.id)

    # update_and_clear_released_resource_docs()
    resource_doc_version = ResourceDocVersion.objects.get_by_resource_version_id(
        release.gateway.id,
        resource_version.id,
    )
    ReleasedResourceDoc.objects.save_released_resource_doc(resource_doc_version)
    ReleasedResourceDoc.objects.clear_unreleased_resource_doc(release.gateway.id)
