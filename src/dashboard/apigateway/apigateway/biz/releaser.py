# -*- coding: utf-8 -*-
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
from dataclasses import dataclass
from typing import Optional

from blue_krill.async_utils.django_utils import delay_on_commit
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.audit import Auditor
from apigateway.biz.validators import PublishValidator, ReleaseValidationError
from apigateway.common.event.event import PublishEventReporter
from apigateway.components.paas import deploy_paas_app, set_paas_stage_env
from apigateway.controller.tasks import (
    release_gateway_by_registry,
    update_release_data_after_success,
)
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import (
    Gateway,
    MicroGateway,
    Release,
    ReleaseHistory,
    ResourceVersion,
    Stage,
)
from apigateway.utils.django import get_model_dict
from apigateway.utils.user_credentials import UserCredentials


class ReleaseError(Exception):
    """发布失败"""


class NonRelatedMicroGatewayError(Exception):
    """环境未关联微网关实例"""


class SharedMicroGatewayNotFound(Exception):
    """未找到共享微网关实例"""


@dataclass
class BaseGatewayReleaser:
    gateway: Gateway
    stage: Stage
    resource_version: ResourceVersion
    comment: str = ""
    username: str = ""
    user_credentials: Optional[UserCredentials] = None

    @classmethod
    def from_data(
        cls,
        gateway: Gateway,
        stage_id: int,
        resource_version_id: int,
        comment: str,
        username: str = "",
        user_credentials: Optional[UserCredentials] = None,
    ):
        """
        :param gateway: 待操作的网关
        :param stage_id: 发布的环境 id
        :param resource_version_id: 发布的版本 id
        :param comment: 发布备注
        :param user_credentials: user_credentials
        :param username: 发布人
        """
        return cls(
            gateway=gateway,
            stage=Stage.objects.get(id=stage_id),
            resource_version=ResourceVersion.objects.get(id=resource_version_id),
            comment=comment,
            username=username,
            user_credentials=user_credentials,
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

        # save release history
        history = self._save_release_history()
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
        except (ValidationError, ReleaseValidationError, NonRelatedMicroGatewayError) as err:
            message = err.detail[0] if isinstance(err, ValidationError) else str(err)
            history = self._save_release_history()
            PublishEventReporter.report_config_validate_failure(history, message)
            raise ReleaseError(message) from err

    def _validate(self):
        """校验待发布数据"""
        publish_validator = PublishValidator(self.gateway, self.stage, self.resource_version)
        publish_validator()

    def _do_release(self, releases: Release, release_history: ReleaseHistory):  # ruff: noqa: B027
        """发布资源版本"""


@dataclass
class MicroGatewayReleaser(BaseGatewayReleaser):
    """微网关发布器"""

    @cached_property
    def _shared_micro_gateway(self):
        # TODO: 根据网关集群分组来找到对应的网关
        try:
            return MicroGateway.objects.get_default_shared_gateway()
        except MicroGateway.DoesNotExist:
            raise SharedMicroGatewayNotFound(_("共享微网关实例不存在。"))

    def _create_release_task_for_shared_gateway(self, release: Release, release_history: ReleaseHistory):
        shared_gateway = self._shared_micro_gateway
        if not shared_gateway:
            return None

        return release_gateway_by_registry.si(
            micro_gateway_id=shared_gateway.pk,
            publish_id=release_history.pk,
        )  # type: ignore

    def _create_release_task(self, release: Release, release_history: ReleaseHistory):
        # create publish event
        PublishEventReporter.report_create_publish_task_doing(release_history)
        # NOTE: 发布专享网关时，不再将资源同时发布到共享网关
        micro_gateway = release.stage.micro_gateway
        # FIXME: refactor here
        if not micro_gateway or micro_gateway.is_shared:
            return self._create_release_task_for_shared_gateway(release, release_history)

        raise ValueError("not support release for micro gateway")

    def _do_release(self, release: Release, release_history: ReleaseHistory):
        release_success_callback = update_release_data_after_success.si(
            publish_id=release_history.id,
            release_id=release.id,
            resource_version_id=release_history.resource_version.id,
            author=release.updated_by,
            comment=release.comment,
        )

        task = self._create_release_task(release, release_history)

        # 使用 celery 的编排能力，task执行成功才会执行release_success_callback
        delay_on_commit(task | release_success_callback)


def release(
    gateway: Gateway,
    stage_id: int,
    resource_version_id: int,
    comment: str,
    username: str = "",
    user_credentials: Optional[UserCredentials] = None,
) -> ReleaseHistory:
    return MicroGatewayReleaser.from_data(
        gateway, stage_id, resource_version_id, comment, username, user_credentials
    ).release()


@dataclass
class ProgramGatewayReleaser:
    @staticmethod
    def deploy(
        gateway: Gateway,
        stage_id: int,
        branch: str,
        commit_id: str,
        version: str,
        comment: str,
        user_credentials: Optional[UserCredentials] = None,
        username: str = "",
    ) -> str:
        """
        编程网关部署
        """
        stage = Stage.objects.get(id=stage_id)

        # 调用pass平台接口设置环境变量: 版本号+版本日志
        set_paas_stage_env(app_code=gateway.name, module="default", env={"version": version, "comment": comment})

        # 调用pass平台部署接口
        deploy_id = deploy_paas_app(
            app_code=gateway.name,
            module="default",
            env=stage.name,
            revision=commit_id,
            branch=branch,
            user_credentials=user_credentials,
        )

        # 创建部署历史
        instance = ProgrammableGatewayDeployHistory.objects.create(
            gateway=gateway, stage=stage, branch=branch, version=version, commit_id=commit_id, deploy_id=deploy_id
        )

        # record audit log
        Auditor.record_release_op_success(
            op_type=OpTypeEnum.CREATE,
            username=username or settings.GATEWAY_DEFAULT_CREATOR,
            gateway_id=gateway.id,
            instance_id=instance.id,
            instance_name=f"{stage.name}:{version}",
            data_before={},
            data_after=get_model_dict(instance),
        )
        return deploy_id
