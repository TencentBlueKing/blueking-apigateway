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

from typing import Optional, Tuple

from apigateway.apps.data_plane.models import DataPlane
from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.components.bkpaas import paas_app_module_offline
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishSourceEnum,
    PublishSourceTriggerPublishTypeMapping,
    StageStatusEnum,
    TriggerPublishTypeEnum,
)
from apigateway.core.models import Gateway, Release, ReleaseHistory


def _pre_publish_check_is_gateway_ready_for_releasing(release: Release, source: PublishSourceEnum) -> Tuple[bool, str]:
    """网关发布校验"""
    if not release:
        return False, "release is None, ignored"

    gateway_id = release.gateway.pk
    # 校验环境
    if not release.stage:
        msg = f"checking release(id={release.pk}): gateway(id={gateway_id}) has no stage, ignored"
        return False, msg

    gateway = Gateway.objects.get(pk=gateway_id)
    trigger_publish_type = PublishSourceTriggerPublishTypeMapping[source]

    # 非 TRIGGER_REVOKE_DISABLE_RELEASE 并且不是网关启用场景才需要校验状态
    if (
        trigger_publish_type != TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE
        and source != PublishSourceEnum.GATEWAY_ENABLE
    ):
        if gateway.status != GatewayStatusEnum.ACTIVE.value:
            msg = f"checking release(id={release.pk}): gateway(id={gateway_id}) is not active, skip"
            return False, msg

        if release.stage.status != StageStatusEnum.ACTIVE.value:
            msg = f"checking release(id={release.pk}): gateway(id={gateway_id}), stage(name={release.stage.name}) is not active, ignored"
            return False, msg

    # 校验版本，现在只支持 v2 发布
    if (
        trigger_publish_type != TriggerPublishTypeEnum.TRIGGER_REVOKE_DISABLE_RELEASE
        and not release.resource_version.is_schema_v2
    ):
        msg = (
            f"checking release(id={release.pk}): The data structure of version [{release.resource_version.object_display}] is incompatible and is not "
            f"allowed to be published. Please create a new version in [Resource Configuration] before publishing."
        )
        return False, msg

    return True, ""


def _pre_publish_save_release_history(
    release: Release,
    source: PublishSourceEnum,
    author: str,
    data_plane: DataPlane,
) -> ReleaseHistory:
    """保存发布历史"""
    return ReleaseHistory.objects.create(
        gateway=release.gateway,
        stage=release.stage,
        source=source.value,
        resource_version=release.resource_version,
        created_by=author,
        data_plane=data_plane,
    )


def _pre_publish_programmable_gateway_offline(
    source: PublishSourceEnum,
    author: str,
    release: Release,
    release_history: ReleaseHistory,
    user_credentials: Optional[UserCredentials] = None,
):
    if not release.gateway.is_programmable:
        return
    if not user_credentials:
        return

    # 需要调用 paas 下线接口
    # 停用时，需要调用 paas 的 module_offline 接口下架环境
    offline_operation_id = paas_app_module_offline(
        app_code=release.gateway.name,
        module="default",
        env=release.stage.name,
        user_credentials=user_credentials,
    )
    last_deploy_history = ProgrammableGatewayDeployHistory.objects.filter(
        gateway=release.gateway,
        version=release.resource_version.version,
    ).first()
    if last_deploy_history:
        ProgrammableGatewayDeployHistory.objects.create(
            gateway=release.gateway,
            stage=release.stage,
            branch=last_deploy_history.branch,
            version=release.resource_version.version,
            commit_id=last_deploy_history.commit_id,
            deploy_id=offline_operation_id,
            publish_id=release_history.id,
            created_by=author,
            source=source.value,
        )
