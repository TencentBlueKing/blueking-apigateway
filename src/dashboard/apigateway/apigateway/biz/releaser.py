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

from blue_krill.async_utils.django_utils import delay_on_commit
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.models import ReleasedResourceDoc, ResourceDocVersion
from apigateway.biz.audit import Auditor
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.validators import StageVarsValuesValidator
from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.tasks import release_gateway_by_helm, release_gateway_by_registry
from apigateway.core import constants
from apigateway.core.constants import PublishSourceEnum, ReleaseStatusEnum, StageStatusEnum
from apigateway.core.models import (
    BackendConfig,
    Gateway,
    MicroGateway,
    MicroGatewayReleaseHistory,
    Release,
    ReleasedResource,
    ReleaseHistory,
    ResourceVersion,
    Stage,
)
from apigateway.utils.django import get_model_dict


class ReleaseError(Exception):
    """发布失败"""


class ReleaseValidationError(Exception):
    """发布校验失败"""


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
    access_token: str = ""
    username: str = ""

    @classmethod
    def from_data(
        cls,
        gateway: Gateway,
        stage_id: int,
        resource_version_id: int,
        comment: str,
        access_token: str,
        username: str = "",
    ):
        """
        :param gateway: 待操作的网关
        :param stage_id: 发布的环境 id
        :param resource_version_id: 发布的版本 id
        :param comment: 发布备注
        :param access_token: access_token
        :param username: 发布人
        """
        return cls(
            gateway=gateway,
            stage=Stage.objects.get(id=stage_id),
            resource_version=ResourceVersion.objects.get(id=resource_version_id),
            comment=comment,
            access_token=access_token,
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

        # save release history
        history = self._save_release_history()
        PublishEventReporter.report_config_validate_success_event(history)

        instance = Release.objects.save_release(
            gateway=self.gateway,
            stage=self.stage,
            resource_version=self.resource_version,
            comment=self.comment,
            username=self.username,
        )

        # record audit log
        Auditor.record_release_op_success(
            op_type=OpTypeEnum.CREATE,
            username=self.username,
            gateway_id=self.gateway.id,
            instance_id=instance.id,
            instance_name=f"{self.stage.name}:{instance.resource_version.name}",
            data_before={},
            data_after=get_model_dict(instance),
        )

        # 发布，仅对微网关生效
        self._do_release(instance, history)

        self._post_release()

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
            PublishEventReporter.report_config_validate_fail_event(history, message)
            raise ReleaseError(message) from err

    def _validate(self):
        """校验待发布数据"""
        if self.resource_version.is_schema_v2:
            self._validate_stage_backends(self.stage)
            self._validate_stage_plugins(self.stage)
        else:
            self._validate_stage_upstreams(self.gateway.id, self.stage, self.resource_version.id)

        self._validate_stage_vars(self.stage, self.resource_version.id)

    def _validate_stage_backends(self, stage: Stage):
        """校验待发布环境的backend配置"""
        backend_configs = BackendConfig.objects.filter(stage=stage)
        for backend_config in backend_configs:
            for host in backend_config.config["hosts"]:
                if not constants.HOST_WITHOUT_SCHEME_PATTERN.match(host["host"]):
                    raise ReleaseValidationError(
                        _(
                            "网关环境【{stage_name}】中的配置Scheme【{scheme}】不合法。请在网关 `基本设置 -> 后端服务` 中进行配置。"
                        ).format(
                            stage_name=stage.name,
                            scheme=host["scheme"],
                        )
                    )

    def _validate_stage_plugins(self, stage: Stage):
        """校验待发布环境的plugin配置"""

        # 环境绑定的插件，同一类型，只能绑定一个即同一个类型的PluginConfig只能绑定一个环境
        stage_plugins = (
            PluginBinding.objects.filter(
                scope_id=stage.id,
                scope_type=PluginBindingScopeEnum.STAGE.value,
            )
            .prefetch_related("config")
            .all()
        )
        stage_plugin_type_set = set()
        for stage_plugin in stage_plugins:
            if stage_plugin.config.type.code in stage_plugin_type_set:
                raise ReleaseValidationError(
                    _("网关环境【{stage_name}】存在绑定多个相同类型[{plugin_code}]的插件。").format(
                        # noqa: E501
                        stage_name=stage.name,
                        plugin_code=stage_plugin.config.type.code,
                    )
                )
            stage_plugin_type_set.add(stage_plugin.config.type.code)

    def _validate_stage_upstreams(self, gateway_id: int, stage: Stage, resource_version_id: int):
        """检查环境的代理配置，如果未配置任何有效的上游主机地址（Hosts），则报错。

        :raise ReleaseValidationError: 当未配置 Hosts 时。
        """
        if not StageProxyHTTPContext().contain_hosts(stage.id):
            raise ReleaseValidationError(
                _(
                    "网关环境【{stage_name}】中代理配置 Hosts 未配置，请在网关 `基本设置 -> 环境管理` 中进行配置。"
                ).format(
                    # noqa: E501
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

    def _do_release(self, releases: Release, release_history: ReleaseHistory):  # ruff: noqa: B027
        """发布资源版本"""

    def _post_release(self):
        # 发布后，将环境状态更新为可用
        # activate stages
        Stage.objects.filter(id=self.stage.id).update(status=StageStatusEnum.ACTIVE.value)

        # update_and_clear_released_resources
        ReleasedResource.objects.save_released_resource(self.resource_version)
        ReleasedResourceHandler.clear_unreleased_resource(self.gateway.id)

        # update_and_clear_released_resource_docs()
        resource_doc_version = ResourceDocVersion.objects.get_by_resource_version_id(
            self.gateway.id,
            self.resource_version.id,
        )
        ReleasedResourceDoc.objects.save_released_resource_doc(resource_doc_version)
        ReleasedResourceDoc.objects.clear_unreleased_resource_doc(self.gateway.id)


#
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
            return None

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
        PublishEventReporter.report_create_publish_task_doing_event(release_history)
        # NOTE: 发布专享网关时，不再将资源同时发布到共享网关
        micro_gateway = release.stage.micro_gateway
        if not micro_gateway or micro_gateway.is_shared:
            return self._create_release_task_for_shared_gateway(release, release_history)

        return self._create_release_task_for_micro_gateway(release, release_history)

    def _do_release(self, release: Release, release_history: ReleaseHistory):
        task = self._create_release_task(release, release_history)
        # 任意一个任务失败都表示发布失败
        # 使用 celery 的编排能力，并发发布多个微网关，并且在发布完成后，更新微网关发布历史的状态
        delay_on_commit(task)


class Releaser:
    access_token: str = ""

    def __init__(self, access_token):
        self.access_token = access_token

    def release(
        self, gateway: Gateway, stage_id: int, resource_version_id: int, comment: str, username: str = ""
    ) -> ReleaseHistory:
        return MicroGatewayReleaser.from_data(
            gateway, stage_id, resource_version_id, comment, self.access_token, username
        ).release()
