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
from typing import List, Optional, Tuple

from blue_krill.async_utils.django_utils import delay_on_commit

from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.constants import DELETE_PUBLISH_ID, NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.tasks import revoke_release, rolling_update_release
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishSourceEnum,
    PublishSourceTriggerPublishTypeMapping,
    StageStatusEnum,
    TriggerPublishTypeEnum,
)
from apigateway.core.models import Gateway, Release, ReleaseHistory

logger = logging.getLogger(__name__)


def _is_gateway_ok_for_releasing(release: Release, source: PublishSourceEnum) -> Tuple[bool, str]:
    """网关发布校验"""
    if not release:
        return False, "release is None, ignored"

    gateway_id = release.gateway.pk
    # 剔除停用的网关
    gateway = Gateway.objects.get(pk=gateway_id)

    trigger_publish_type = PublishSourceTriggerPublishTypeMapping[source]

    # 校验环境
    if not release.stage:
        msg = f"release(id={release.pk}) has not stage, ignored"
        return False, msg

    # 非 TRIGGER_REVOKE_DISABLE_RELEASE 并且不是网关启用场景才需要校验状态
    if (
        trigger_publish_type != TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE
        and source != PublishSourceEnum.GATEWAY_ENABLE
    ):
        if gateway.status != GatewayStatusEnum.ACTIVE.value:
            msg = f"rolling_update_release: gateway(id={gateway_id}) is not active, skip"
            return False, msg

        if release.stage.status != StageStatusEnum.ACTIVE.value:
            msg = f"release(id={release.pk})  stage(name={release.stage.name}) is not active, ignored"
            return False, msg

    # 校验版本,现在只支持v2发布
    if not release.resource_version.is_schema_v2:
        msg = (
            f"The version [{release.resource_version.object_display}] is too old and is not allowed to be published."
            f"Please create a new version and publish it again."
        )
        return False, msg

    return True, ""


def _save_release_history(release: Release, source: PublishSourceEnum, author: str) -> ReleaseHistory:
    """保存发布历史"""
    return ReleaseHistory.objects.create(
        gateway=release.gateway,
        stage=release.stage,
        source=source.value,
        resource_version=release.resource_version,
        created_by=author,
    )


def _trigger_rolling_publish(
    source: PublishSourceEnum,
    author: str,
    release_list: List[Release],
    is_sync: Optional[bool] = False,
):
    """触发网关滚动更新"""

    for release in release_list:
        if source is PublishSourceEnum.CLI_SYNC:
            release_history = ReleaseHistory()
            # make it as default
            release_history.source = PublishSourceEnum.CLI_SYNC.value
            publish_id = NO_NEED_REPORT_EVENT_PUBLISH_ID
        else:
            # 如果不是手动同步就需要生成发布历史
            release_history = _save_release_history(release, source, author)

            publish_id = release_history.pk

        # 发布 check
        ok, msg = _is_gateway_ok_for_releasing(release, source)
        if not ok:
            logger.warning(msg)
            PublishEventReporter.report_config_validate_fail_event(release_history, msg)
            continue

        PublishEventReporter.report_config_validate_success_event(release_history)
        PublishEventReporter.report_create_publish_task_doing_event(release_history)

        # 开始发布
        if is_sync:
            rolling_update_release(gateway_id=release.gateway.pk, publish_id=publish_id, release_id=release.pk)
            continue

        delay_on_commit(
            rolling_update_release,
            gateway_id=release.gateway_id,
            publish_id=publish_id,
            release_id=release.pk,
        )
    return True


def _trigger_revoke_publish_for_disable(
    source: PublishSourceEnum,
    author: str,
    release_list: List[Release],
    is_sync: Optional[bool] = False,
):
    """触发撤销发布"""

    for release in release_list:
        # 创建发布历史
        release_history = _save_release_history(release, source, author)
        # 发布 check
        ok, msg = _is_gateway_ok_for_releasing(release, source)
        # 上报发布配置校验事件
        if not ok:
            logging.warning(msg)
            PublishEventReporter.report_config_validate_fail_event(release_history, msg)
            continue

        PublishEventReporter.report_config_validate_success_event(release_history)
        PublishEventReporter.report_create_publish_task_doing_event(release_history)

        # 开始发布
        if is_sync:
            return revoke_release(release_id=release.id, publish_id=release_history.id)
        delay_on_commit(revoke_release, release_id=release.id, publish_id=release_history.id)
    return None


def _trigger_revoke_publish_for_deleting(
    release_list: List[Release],
    is_sync: Optional[bool] = False,
):
    """触发删除发布"""
    for release in release_list:
        # FIXME: no release_history to report event?
        # 开始发布
        if is_sync:
            return revoke_release(release_id=release.id, publish_id=DELETE_PUBLISH_ID)
        # else:
        delay_on_commit(revoke_release, release_id=release.id, publish_id=DELETE_PUBLISH_ID)
    return None


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
      gateway_id: 网关 id
      stage_id: 环境 id
      is_sync: 同步异步
    """
    trigger_publish_type = PublishSourceTriggerPublishTypeMapping[source]
    if not trigger_publish_type:
        raise ValueError(f"source[{source}] is illegal")

    qs = Release.objects.filter(gateway_id=gateway_id)

    if stage_id:
        qs = qs.filter(stage_id=stage_id)

    release_list = qs.prefetch_related("gateway", "stage").all()
    # if not released before, skip
    if not release_list:
        return True

    if trigger_publish_type == TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE:
        return _trigger_rolling_publish(source, author, release_list, is_sync=is_sync)

    if trigger_publish_type == TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE:
        return _trigger_revoke_publish_for_disable(source, author, release_list, is_sync=is_sync)

    if trigger_publish_type == TriggerPublishTypeEnum.TRIGGER_REVOKE_DELETE_RELEASE:
        return _trigger_revoke_publish_for_deleting(release_list, is_sync=is_sync)
    return None
