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
from typing import Optional

from django.db.models import Count
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.common.mixins.contexts import GetGatewayFromContextMixin
from apigateway.core import constants as core_constants
from apigateway.core.constants import HOST_WITHOUT_SCHEME_PATTERN, GatewayStatusEnum
from apigateway.core.models import BackendConfig, Gateway, Proxy, Resource, ResourceVersion, Stage

from .constants import APP_CODE_PATTERN, STAGE_VAR_FOR_PATH_PATTERN
from .resource_version import ResourceVersionHandler
from ..apps.plugin.constants import PluginBindingScopeEnum
from ..apps.plugin.models import PluginBinding
from ..common.contexts import StageProxyHTTPContext


class ReleaseValidationError(Exception):
    """发布校验失败"""


class MaxCountPerGatewayValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __init__(self, model, max_count_callback, message):
        self.model = model
        self.max_count_callback = max_count_callback
        self.message = message

    def _get_exist_count(self, gateway):
        fields = [f.name for f in self.model._meta.get_fields()]
        return self.model.objects.filter(gateway_id=gateway.id).count()

    def __call__(self, attrs, serializer):
        gateway = self._get_gateway(serializer)
        instance = getattr(serializer, "instance", None)

        if instance:
            # 更新时，不校验
            return

        if self._get_exist_count(gateway) >= self.max_count_callback(gateway):
            message = self.message.format(max_count=self.max_count_callback(gateway))
            raise serializers.ValidationError(message)


class ResourceIDValidator(GetGatewayFromContextMixin):
    requires_context = True

    def __call__(self, value, serializer_field):
        if not value:
            return

        gateway = self._get_gateway(serializer_field)
        resource_ids = value
        if isinstance(value, int):
            resource_ids = [value]

        assert isinstance(resource_ids, list)

        from apigateway.core.models import Resource

        count = Resource.objects.filter(gateway_id=gateway.id, id__in=resource_ids).count()
        if count != len(set(resource_ids)):
            raise serializers.ValidationError(
                _("网关【id={gateway_id}】下指定的部分资源ID不存在。").format(gateway_id=gateway.id)
            )


class BKAppCodeListValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, list)

        invalid_app_codes = [app_code for app_code in value if not APP_CODE_PATTERN.match(app_code)]
        if invalid_app_codes:
            raise serializers.ValidationError(
                _("蓝鲸应用【{app_codes}】不匹配要求的模式。").format(app_codes=", ".join(sorted(invalid_app_codes)))
            )


class BKAppCodeValidator:
    def __call__(self, value):
        if not value:
            return

        assert isinstance(value, str)

        if not APP_CODE_PATTERN.match(value):
            raise serializers.ValidationError(_("蓝鲸应用【{value}】不匹配要求的模式。").format(value=value))


class StageVarsValuesValidator:
    """
    校验变量的值是否符合要求
    - 用作路径变量时：值应符合路径片段规则
    - 用作Host变量时：值应符合 Host 规则
    """

    def __call__(self, attrs):
        gateway = attrs["gateway"]
        stage_name = attrs["stage_name"]
        stage_vars = attrs["vars"]
        resource_version_id = attrs["resource_version_id"]

        # 允许环境中变量不存在:
        # openapi 同步环境时，存在修改变量名的情况，此时，当前 resource version 中资源引用的变量可能不存在，
        # 因此，通过 openapi 更新时，允许环境变量不存在
        allow_var_not_exist = attrs.get("allow_var_not_exist", False)

        used_stage_vars = ResourceVersionHandler.get_used_stage_vars(gateway.id, resource_version_id)
        if not used_stage_vars:
            return

        for key in used_stage_vars["in_path"]:
            if key not in stage_vars:
                if allow_var_not_exist:
                    continue

                raise serializers.ValidationError(
                    _(
                        "环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作路径变量，必须存在。"
                    ).format(stage_name=stage_name, key=key),
                )

            if not STAGE_VAR_FOR_PATH_PATTERN.match(stage_vars[key]):
                raise serializers.ValidationError(
                    _(
                        "环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作路径变量，变量值不是一个合法的 URL 路径片段。"
                    ).format(
                        stage_name=stage_name,
                        key=key,
                    ),
                )

        for key in used_stage_vars["in_host"]:
            _value = stage_vars.get(key)
            if not _value:
                if allow_var_not_exist:
                    continue

                raise serializers.ValidationError(
                    _(
                        "环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作 Host 变量，不能为空。"
                    ).format(stage_name=stage_name, key=key),
                )

            if not HOST_WITHOUT_SCHEME_PATTERN.match(_value):
                raise serializers.ValidationError(
                    _(
                        '环境【{stage_name}】中，环境变量【{key}】在发布版本的资源配置中被用作 Host 变量，变量值不是一个合法的 Host（不包含"http(s)://"）。'
                    ).format(
                        stage_name=stage_name,
                        key=key,
                    )
                )


class PublishValidator:
    """
    网关环境发布校验器
    """

    def __init__(self, gateway: Gateway, stage: Stage, resource_version: Optional[ResourceVersion] = None):
        self.gateway = gateway
        self.stage = stage
        self.resource_version = resource_version

    def _validate_stage_backends(self):
        """校验待发布环境的backend配置"""
        backend_configs = BackendConfig.objects.filter(stage=self.stage)
        for backend_config in backend_configs:
            for host in backend_config.config["hosts"]:
                if not core_constants.HOST_WITHOUT_SCHEME_PATTERN.match(host["host"]):
                    raise ReleaseValidationError(
                        _(
                            "网关环境【{stage_name}】中的配置【后端服务地址】不合法。请在网关 `后端服务` 中进行配置。"
                        ).format(
                            stage_name=self.stage.name,
                        )
                    )

    def _validate_stage_plugins(self):
        """校验待发布环境的plugin配置"""

        # 环境绑定的插件，同一类型，只能绑定一个即同一个类型的PluginConfig只能绑定一个环境
        stage_plugins = (
            PluginBinding.objects.filter(
                scope_id=self.stage.id,
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
                        stage_name=self.stage.name,
                        plugin_code=stage_plugin.config.type.code,
                    )
                )
            stage_plugin_type_set.add(stage_plugin.config.type.code)

    def _validate_stage_upstreams(self):
        """检查环境的代理配置，如果未配置任何有效的上游主机地址（Hosts），则报错。

        :raise ReleaseValidationError: 当未配置 Hosts 时。
        """
        if not StageProxyHTTPContext().contain_hosts(self.stage.id):
            raise ReleaseValidationError(
                _(
                    "网关环境【{stage_name}】中代理配置 Hosts 未配置，请在网关 `基本设置 -> 环境管理` 中进行配置。"
                ).format(
                    # noqa: E501
                    stage_name=self.stage.name,
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

    def _validate_gateway_status(self):
        if self.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise ReleaseValidationError(
                _("网关【{gateway_name}】没有启用，不允许发布").format(gateway_name=self.gateway.name)
            )

    def __call__(self):
        """校验待发布数据"""

        # 校验网关启用状态
        self._validate_gateway_status()

        # stage相关配置
        self._validate_stage_backends()
        self._validate_stage_plugins()

        if self.resource_version:
            self._validate_stage_vars(self.stage, self.resource_version.id)


class ResourceVersionValidator:
    """
    资源版本创建时校验网关资源版本(open/api)
    """

    def __call__(self, attrs):
        gateway = attrs["gateway"]

        version = attrs.get("version", attrs.get("name"))  # 兼容一下open

        # 校验网关下资源数量，网关下资源数量为0时，不允许创建网关版本
        if not Resource.objects.filter(gateway_id=gateway.id).exists():
            raise serializers.ValidationError(_("请先创建资源，然后再生成版本。"))

        # 是否绑定backend
        if Proxy.objects.filter(resource__gateway=gateway, backend__isnull=True).exists():
            raise serializers.ValidationError(_("存在资源未绑定后端服务. "))

        # 是否存在绑定多个backend
        if (
            Proxy.objects.filter(resource__gateway=gateway)
            .values("resource")
            .annotate(backend_count=Count("backend"))
            .filter(backend_count__gt=1)
            .exists()
        ):
            raise serializers.ValidationError(_("存在同一资源绑定多个后端服务. "))

        # ResourceVersion 中数据量较大，因此，不使用 UniqueTogetherValidator
        if ResourceVersion.objects.filter(gateway=gateway, version=version).exists():
            raise serializers.ValidationError(_("版本 {version} 已存在。").format(version=version))
