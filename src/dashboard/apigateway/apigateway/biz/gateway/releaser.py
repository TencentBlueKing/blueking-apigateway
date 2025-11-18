# -*- coding: utf-8 -*-
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
from dataclasses import dataclass

from blue_krill.async_utils.django_utils import delay_on_commit
from django.conf import settings
from rest_framework.exceptions import ValidationError

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.audit import Auditor
from apigateway.biz.validators import PublishValidator, ReleaseValidationError
from apigateway.controller.tasks import (
    release_gateway_by_registry,
    update_release_data_after_success,
)
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import (
    Gateway,
    Release,
    ReleaseHistory,
    ResourceVersion,
    Stage,
)
from apigateway.service.event.event import PublishEventReporter
from apigateway.utils.django import get_model_dict


class ReleaseError(Exception):
    """发布失败"""


@dataclass
class GatewayReleaser:
    gateway: Gateway
    stage: Stage
    resource_version: ResourceVersion
    comment: str = ""
    username: str = ""

    @classmethod
    def from_data(
        cls,
        gateway: Gateway,
        stage_id: int,
        resource_version_id: int,
        comment: str,
        username: str = "",
    ):
        """
        :param gateway: 待操作的网关
        :param stage_id: 发布的环境 id
        :param resource_version_id: 发布的版本 id
        :param comment: 发布备注
        :param username: 发布人
        """
        return cls(
            gateway=gateway,
            stage=Stage.objects.get(id=stage_id),
            resource_version=ResourceVersion.objects.get(id=resource_version_id),
            comment=comment,
            username=username,
        )

    def _save_release_history(self) -> ReleaseHistory:
        return ReleaseHistory.objects.create(
            gateway_id=self.gateway.id,
            stage_id=self.stage.id,
            source=PublishSourceEnum.VERSION_PUBLISH.value,
            resource_version_id=self.resource_version.id,
            comment=self.comment,
            created_by=self.username,
        )

    def release(self):
        self._pre_release()

        # 如果是编程网关，查询一下 deploy 部署历史
        deploy_history = None
        if self.gateway.is_programmable:
            deploy_history = ProgrammableGatewayDeployHistory.objects.filter(
                gateway_id=self.gateway.id, stage_id=self.stage.id, version=self.resource_version.version
            ).first()
            # 如果通过网关点击的部署按钮，则使用部署人作为发布人
            if deploy_history:
                self.username = deploy_history.created_by

        # save release history
        history = self._save_release_history()
        if deploy_history:
            # 补充 publish_id
            deploy_history.publish_id = history.id
            deploy_history.save()

        PublishEventReporter.report_config_validate_success(history)

        instance = Release.objects.get_or_create_release(
            gateway=self.gateway,
            stage=self.stage,
            resource_version=self.resource_version,
            comment=self.comment,
            username=self.username,
        )

        # record audit log
        Auditor.record_release_op_success(
            op_type=OpTypeEnum.CREATE,
            username=self.username or settings.GATEWAY_DEFAULT_CREATOR,
            gateway_id=self.gateway.id,
            instance_id=instance.id,
            instance_name=f"{self.stage.name}:{instance.resource_version.version}",
            data_before={},
            data_after=get_model_dict(instance),
        )

        # 发布，仅对微网关生效
        self._do_release(instance, history)

        # self._post_release()

        return history

    def _pre_release(self):
        # 环境、部署信息校验
        # 普通参数校验失败，不需要记录发布日志，环境参数校验失败，需记录发布日志
        # 因此，将普通参数校验，环境参数校验分开处理
        try:
            self._validate()
        except (ValidationError, ReleaseValidationError) as err:
            message = err.detail[0] if isinstance(err, ValidationError) else str(err)
            history = self._save_release_history()
            PublishEventReporter.report_config_validate_failure(history, message)
            raise ReleaseError(message) from err

    def _validate(self):
        """校验待发布数据"""
        publish_validator = PublishValidator(self.gateway, self.stage, self.resource_version)
        publish_validator()

    def _do_release(self, release: Release, release_history: ReleaseHistory):  # noqa: B027
        """发布资源版本"""
        release_success_callback = update_release_data_after_success.si(
            publish_id=release_history.id,
            release_id=release.id,
            resource_version_id=release_history.resource_version.id,
            author=release.updated_by,
            comment=release.comment,
        )

        # create publish event
        PublishEventReporter.report_create_publish_task_doing(release_history)

        task = release_gateway_by_registry.si(publish_id=release_history.pk)  # type: ignore

        # 使用 celery 的编排能力，task 执行成功才会执行 release_success_callback
        delay_on_commit(task | release_success_callback)


def release(
    gateway: Gateway,
    stage_id: int,
    resource_version_id: int,
    comment: str,
    username: str = "",
) -> ReleaseHistory:
    return GatewayReleaser.from_data(
        gateway,
        stage_id,
        resource_version_id,
        comment,
        username,
    ).release()
