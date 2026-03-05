#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from typing import List, Optional, Set

from blue_krill.async_utils.django_utils import delay_on_commit

from apigateway.apps.data_plane.models import GatewayDataPlaneBinding
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.controller.constants import DELETE_PUBLISH_ID, NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.tasks import revoke_release, rolling_update_release
from apigateway.core.constants import (
    PublishSourceEnum,
    PublishSourceTriggerPublishTypeMapping,
    TriggerPublishTypeEnum,
)
from apigateway.core.models import Release, ReleaseHistory
from apigateway.service.event.event import PublishEventReporter

from .hooks import (
    _pre_publish_check_is_gateway_ready_for_releasing,
    _pre_publish_programmable_gateway_offline,
    _pre_publish_save_release_history,
)

logger = logging.getLogger(__name__)


def _filter_data_planes(data_planes, target_data_plane_ids: Optional[Set[int]] = None):
    if not target_data_plane_ids:
        return data_planes
    return [data_plane for data_plane in data_planes if data_plane.id in target_data_plane_ids]


def _trigger_rolling_update(
    source: PublishSourceEnum,
    author: str,
    release_list: List[Release],
    is_sync: Optional[bool] = False,
    target_data_plane_ids: Optional[Set[int]] = None,
):
    """触发网关滚动更新，支持多数据面"""
    has_failure = False
    for release in release_list:
        # Get active data planes for this gateway - must have at least one
        data_planes = GatewayDataPlaneBinding.objects.get_gateway_active_data_planes(release.gateway_id)
        data_planes = _filter_data_planes(data_planes, target_data_plane_ids)

        # a gateway should have at least one active data plane. The creation ensure this.
        # skip the gateway_id without active data planes
        # log error instead of raise exception
        if not data_planes:
            logger.error(
                "Gateway (id=%s) has no active data planes, cannot trigger rolling update",
                release.gateway_id,
            )
            has_failure = True
            continue

        for data_plane in data_planes:
            if source is PublishSourceEnum.CLI_SYNC:
                release_history = ReleaseHistory()
                release_history.source = PublishSourceEnum.CLI_SYNC.value
                release_history.data_plane = data_plane
                publish_id = NO_NEED_REPORT_EVENT_PUBLISH_ID
            else:
                # Create release history for each data plane
                release_history = _pre_publish_save_release_history(release, source, author, data_plane=data_plane)
                publish_id = release_history.pk

            # 发布 check
            ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(release, source)
            if not ok:
                logger.warning(msg)
                PublishEventReporter.report_config_validate_failure(release_history, msg)
                has_failure = True
                continue

            PublishEventReporter.report_config_validate_success(release_history)
            PublishEventReporter.report_create_publish_task_doing(release_history)

            # 开始发布
            if is_sync:
                is_success = rolling_update_release(
                    gateway_id=release.gateway.pk,
                    publish_id=publish_id,
                    release_id=release.pk,
                    data_plane_id=data_plane.id,
                )
                if not is_success:
                    has_failure = True
                continue

            delay_on_commit(
                rolling_update_release,
                gateway_id=release.gateway_id,
                publish_id=publish_id,
                release_id=release.pk,
                data_plane_id=data_plane.id,
            )
    return not has_failure


def _trigger_revoke_disable(
    source: PublishSourceEnum,
    author: str,
    release_list: List[Release],
    is_sync: Optional[bool] = False,
    user_credentials: Optional[UserCredentials] = None,
    target_data_plane_ids: Optional[Set[int]] = None,
):
    """触发停用/下架发布，支持多数据面"""
    has_failure = False
    for release in release_list:
        # Get active data planes for this gateway - must have at least one
        data_planes = GatewayDataPlaneBinding.objects.get_gateway_active_data_planes(release.gateway_id)
        data_planes = _filter_data_planes(data_planes, target_data_plane_ids)

        if not data_planes:
            logger.error(
                "Gateway (id=%s) has no active data planes, cannot trigger revoke disable",
                release.gateway_id,
            )
            has_failure = True
            continue

        for data_plane in data_planes:
            # 创建发布历史
            release_history = _pre_publish_save_release_history(release, source, author, data_plane=data_plane)

            # 如果是编程网关需要特殊处理
            _pre_publish_programmable_gateway_offline(source, author, release, release_history, user_credentials)

            # 发布 check
            ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(release, source)
            # 上报发布配置校验事件
            if not ok:
                logger.warning(msg)
                PublishEventReporter.report_config_validate_failure(release_history, msg)
                has_failure = True
                continue

            PublishEventReporter.report_config_validate_success(release_history)
            PublishEventReporter.report_create_publish_task_doing(release_history)

            # 开始发布
            if is_sync:
                is_success = revoke_release(
                    release_id=release.id, publish_id=release_history.id, data_plane_id=data_plane.id
                )
                if not is_success:
                    has_failure = True
                continue
            delay_on_commit(
                revoke_release,
                release_id=release.id,
                publish_id=release_history.id,
                data_plane_id=data_plane.id,
            )
    return not has_failure


def _trigger_revoke_deleting(
    release_list: List[Release],
    is_sync: Optional[bool] = False,
    target_data_plane_ids: Optional[Set[int]] = None,
):
    """触发删除发布，支持多数据面"""
    has_failure = False
    for release in release_list:
        # Get all data planes for this gateway (including inactive ones for cleanup)
        data_planes = GatewayDataPlaneBinding.objects.get_gateway_data_planes(release.gateway_id)
        data_planes = _filter_data_planes(data_planes, target_data_plane_ids)

        if not data_planes:
            logger.error(
                "Gateway (id=%s) has no data planes, cannot trigger revoke delete",
                release.gateway_id,
            )
            has_failure = True
            continue

        for data_plane in data_planes:
            # FIXME: no release_history to report event?
            # 开始发布
            if is_sync:
                is_success = revoke_release(
                    release_id=release.id, publish_id=DELETE_PUBLISH_ID, data_plane_id=data_plane.id
                )
                if not is_success:
                    has_failure = True
                continue
            delay_on_commit(
                revoke_release,
                release_id=release.id,
                publish_id=DELETE_PUBLISH_ID,
                data_plane_id=data_plane.id,
            )
    return not has_failure


def trigger_gateway_publish(
    source: PublishSourceEnum,
    author: str,
    gateway_id: int,
    stage_id: Optional[int] = None,
    is_sync: Optional[bool] = False,
    user_credentials: Optional[UserCredentials] = None,
    target_data_plane_ids: Optional[List[int]] = None,
):
    """触发网关发布
    source: 发布来源
    author: 发布者
    gateway_id: 网关 id
    stage_id: 环境 id
    is_sync: 同步异步
    user_credentials: 用户凭证
    target_data_plane_ids: 指定发布的数据面 ID 列表，不传则按默认规则发布到全部绑定数据面
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

    target_data_plane_id_set = set(target_data_plane_ids or [])

    # rolling update release
    if trigger_publish_type == TriggerPublishTypeEnum.TRIGGER_ROLLING_UPDATE_RELEASE:
        return _trigger_rolling_update(
            source,
            author,
            release_list,
            is_sync=is_sync,
            target_data_plane_ids=target_data_plane_id_set,
        )

    # revoke disable release
    if trigger_publish_type == TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE:
        return _trigger_revoke_disable(
            source,
            author,
            release_list,
            is_sync=is_sync,
            user_credentials=user_credentials,
            target_data_plane_ids=target_data_plane_id_set,
        )

    # revoke delete release
    if trigger_publish_type == TriggerPublishTypeEnum.TRIGGER_REVOKE_DELETE_RELEASE:
        return _trigger_revoke_deleting(release_list, is_sync=is_sync, target_data_plane_ids=target_data_plane_id_set)

    # do nothing
    return None
