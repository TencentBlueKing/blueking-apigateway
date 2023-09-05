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
from abc import ABCMeta
from dataclasses import dataclass
from typing import List

from attrs import define
from blue_krill.async_utils.django_utils import delay_on_commit
from celery.canvas import group
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.support.models import ReleasedResourceDoc, ResourceDocVersion
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.validators import StageVarsValuesValidator
from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.tasks import release_gateway_by_helm, release_gateway_by_registry
from apigateway.core.constants import PublishSourceEnum, ReleaseStatusEnum, StageStatusEnum
from apigateway.core.models import (
    Gateway,
    MicroGateway,
    MicroGatewayReleaseHistory,
    Release,
    ReleasedResource,
    ReleaseHistory,
    ResourceVersion,
    Stage,
)


class ReleaseError(Exception):
    """发布失败"""


class ReleaseValidationError(Exception):
    """发布校验失败"""


class NonRelatedMicroGatewayError(Exception):
    """环境未关联微网关实例"""


class SharedMicroGatewayNotFound(Exception):
    """未找到共享微网关实例"""


class GatewayReleaserFactory:
    @classmethod
    def get_releaser(
        cls,
        gateway: Gateway,
        stage_ids: List[int],
        resource_version_id: int,
        comment: str,
        access_token: str,
        username: str = "",
    ) -> "BaseGatewayReleaserHandler":
        if gateway.is_micro_gateway:
            return MicroGatewayReleaserHandler.from_data(
                gateway, stage_ids, resource_version_id, comment, access_token, username
            )

        return DefaultGatewayReleaserHandler.from_data(
            gateway, stage_ids, resource_version_id, comment, access_token, username
        )


@dataclass
class BaseGatewayReleaserHandler(metaclass=ABCMeta):
    gateway: Gateway
    stages: List[Stage]
    resource_version: ResourceVersion
    comment: str = ""
    username: str = ""
    access_token: str = ""

    @classmethod
    def from_data(
        cls,
        gateway: Gateway,
        stage_ids: List[int],
        resource_version_id: int,
        comment: str,
        access_token: str,
        username: str = "",
    ):
        """
        :param gateway: 待操作的网关
        :param stage_ids: 发布的环境id列表
        :param resource_version_id: 发布的版本id
        :param comment: 发布备注
        :param access_token: access_token
        :param username: 发布人
        """

        return cls(
            gateway=gateway,
            stages=list(Stage.objects.filter(id__in=stage_ids)),
            resource_version=ResourceVersion.objects.get(id=resource_version_id),
            comment=comment,
            username=username,
            access_token=access_token,
        )

    def release_batch(self):
        # 环境、部署信息校验
        # 普通参数校验失败，不需要记录发布日志，环境参数校验失败，需记录发布日志
        # 因此，将普通参数校验，环境参数校验分开处理

        try:
            self._validate()
        except (ValidationError, ReleaseValidationError, NonRelatedMicroGatewayError) as err:
            message = err.detail[0] if isinstance(err, ValidationError) else str(err)
            history = ReleaseHandler.save_release_history_with_id(
                gateway_id=self.gateway.id,
                stage_id=self.stages[0].id,
                resource_version_id=self.resource_version.id,
                source=PublishSourceEnum.VERSION_PUBLISH,
                author=self.username,
            )
            history.stages.set(self.stages)
            # 上报发布校验失败事件: todo: 支持批量环境发布
            PublishEventReporter.report_config_validate_fail_event(history, history.stage, message)
            raise ReleaseError(message) from err
        # save release history
        history = ReleaseHandler.save_release_history_with_id(
            gateway_id=self.gateway.id,
            stage_id=self.stages[0].id,
            resource_version_id=self.resource_version.id,
            source=PublishSourceEnum.VERSION_PUBLISH,
            author=self.username,
        )
        history.stages.set(self.stages)

        PublishEventReporter.report_config_validate_success_event(history, history.stage)

        release_instances = []

        # save release
        for stage in self.stages:
            # save release
            instance = Release.objects.save_release(
                gateway=self.gateway,
                stage=stage,
                resource_version=self.resource_version,
                comment=self.comment,
                username=self.username,
            )

            release_instances.append(instance)

            # record audit log
            record_audit_log(
                username=self.username,
                op_type=OpTypeEnum.CREATE.value,
                op_status=OpStatusEnum.SUCCESS.value,
                op_object_group=self.gateway.id,
                op_object_type=OpObjectTypeEnum.RELEASE.value,
                op_object_id=instance.id,
                op_object=f"{stage.name}:{instance.resource_version.name}",
                comment=_("版本发布"),
            )

        # 批量发布，仅对微网关生效
        self._do_release(release_instances, history)

        # 发布后，将环境状态更新为可用
        self._activate_stages()

        self._update_and_clear_released_resources()
        self._update_and_clear_released_resource_docs()

        return history

    def _validate(self):
        """校验待发布数据"""
        for stage in self.stages:
            self._validate_stage_upstreams(self.gateway.id, stage, self.resource_version.id)
            self._validate_stage_vars(stage, self.resource_version.id)

    def _validate_stage_upstreams(self, gateway_id: int, stage: Stage, resource_version_id: int):
        """检查环境的代理配置，如果未配置任何有效的上游主机地址（Hosts），则报错。

        :raise ReleaseValidationError: 当未配置 Hosts 时。
        """
        if not StageProxyHTTPContext().contain_hosts(stage.id):
            raise ReleaseValidationError(
                _("网关环境【{stage_name}】中代理配置 Hosts 未配置，请在网关 `基本设置 -> 环境管理` 中进行配置。").format(  # noqa: E501
                    stage_name=stage.name,
                )
            )

    def _validate_stage_vars(self, stage: Stage, resource_version_id: int):
        validator = StageVarsValuesValidator()
        validator(
            {
                "gateway": self.gateway,
                "stage_name": stage.name,
                "vars": stage.vars,
                "resource_version_id": resource_version_id,
            }
        )

    def _do_release(self, releases: List[Release], release_history: ReleaseHistory):
        """发布资源版本"""

    def _activate_stages(self):
        stage_ids = [stage.id for stage in self.stages]
        Stage.objects.filter(id__in=stage_ids).update(status=StageStatusEnum.ACTIVE.value)

    def _update_and_clear_released_resources(self):
        ReleasedResource.objects.save_released_resource(self.resource_version)
        ReleasedResourceHandler.clear_unreleased_resource(self.gateway.id)

    def _update_and_clear_released_resource_docs(self):
        resource_doc_version = ResourceDocVersion.objects.get_by_resource_version_id(
            self.gateway.id,
            self.resource_version.id,
        )
        ReleasedResourceDoc.objects.save_released_resource_doc(resource_doc_version)
        ReleasedResourceDoc.objects.clear_unreleased_resource_doc(self.gateway.id)


@dataclass
class DefaultGatewayReleaserHandler(BaseGatewayReleaserHandler):
    """APIGateway 默认网关发布器"""


@dataclass
class MicroGatewayReleaserHandler(BaseGatewayReleaserHandler):
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
            return

        history = MicroGatewayReleaseHistory.objects.create(
            gateway=release.gateway,
            stage=release.stage,
            micro_gateway=shared_gateway,
            release_history=release_history,
            status=ReleaseStatusEnum.RELEASING.value,
        )
        return release_gateway_by_registry.si(
            release_id=release.pk,
            micro_gateway_release_history_id=history.pk,
            micro_gateway_id=shared_gateway.pk,
            publish_id=release_history.pk,
        )  # type: ignore

    def _create_release_task_for_micro_gateway(self, release: Release, release_history: ReleaseHistory):
        stage = release.stage
        micro_gateway = stage.micro_gateway
        if not micro_gateway or not micro_gateway.is_managed:
            return

        history = MicroGatewayReleaseHistory.objects.create(
            gateway=release.gateway,
            stage=stage,
            micro_gateway=micro_gateway,
            release_history=release_history,
            status=ReleaseStatusEnum.RELEASING.value,
        )

        return release_gateway_by_helm.si(
            access_token=self.access_token,
            release_id=release.pk,
            micro_gateway_release_history_id=history.pk,
            username=self.username,
        )  # type: ignore

    def _create_release_task(self, release: Release, release_history: ReleaseHistory):
        # create publish event
        PublishEventReporter.report_create_publish_task_doing_event(release_history, release.stage)
        # NOTE: 发布专享网关时，不再将资源同时发布到共享网关
        micro_gateway = release.stage.micro_gateway
        if not micro_gateway or micro_gateway.is_shared:
            return self._create_release_task_for_shared_gateway(release, release_history)

        return self._create_release_task_for_micro_gateway(release, release_history)

    def _do_release(self, releases: List[Release], release_history: ReleaseHistory):
        tasks = []
        for release in releases:
            task = self._create_release_task(release, release_history)
            # 任意一个任务失败都表示发布失败
            tasks.append(task)

        # 使用 celery 的编排能力，并发发布多个微网关，并且在发布完成后，更新微网关发布历史的状态
        delay_on_commit(group(*tasks))


@define(slots=False)
class ReleaseBatchHandler:
    access_token: str = ""

    def release_batch(
        self, gateway: Gateway, stage_ids: List[int], resource_version_id: int, comment: str, username: str = ""
    ):
        return GatewayReleaserFactory.get_releaser(
            gateway, stage_ids, resource_version_id, comment, access_token=self.access_token, username=username
        ).release_batch()
