#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

"""Release validation helpers."""

from typing import Optional

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.common.constants import STAGE_VAR_FOR_PATH_PATTERN
from apigateway.core import constants as core_constants
from apigateway.core.backend_config import AIBackendConfig
from apigateway.core.constants import (
    HOST_WITHOUT_SCHEME_PATTERN,
    BackendKindEnum,
    GatewayStatusEnum,
)
from apigateway.core.models import Backend, BackendConfig, Gateway, Proxy, ResourceVersion, Stage
from apigateway.service.resource_version import get_used_stage_vars


class ReleaseValidationError(Exception):
    """发布校验失败"""


class StageVarsValuesValidator:
    """
    校验变量的值是否符合要求
    - 用作路径变量时：值应符合路径片段规则
    - 用作Host变量时：值应符合 Host 规则
    """

    def __call__(self, attrs):
        """校验环境变量值是否满足资源版本引用要求，用于发布前确认目标环境变量是否可用。

        发布校验、环境变量保存校验等需要根据资源版本反查变量引用的场景使用。

        Args:
            attrs (dict): 校验上下文字典，必须包含 gateway、stage_name、vars、
                resource_version_id；可选 allow_var_not_exist 表示是否允许资源引用的变量暂时不存在。

        Returns:
            None: 校验通过时不返回值；校验失败时抛出 serializers.ValidationError。
        """
        stage_name = attrs["stage_name"]
        stage_vars = attrs["vars"]
        gateway_id = attrs["gateway"].id
        resource_version_id = attrs["resource_version_id"]

        # 允许环境中变量不存在:
        # openapi 同步环境时，存在修改变量名的情况，此时，当前 resource version 中资源引用的变量可能不存在，
        # 因此，通过 openapi 更新时，允许环境变量不存在
        allow_var_not_exist = attrs.get("allow_var_not_exist", False)

        used_stage_vars = get_used_stage_vars(gateway_id, resource_version_id)
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

    def _raise_invalid_backend_config(self, backend_config):
        raise ReleaseValidationError(
            _(
                "网关环境【{stage_name}】中的配置【后端服务 {backend_name} 地址】不合法。请在网关 `后端服务` 中进行配置。"
            ).format(
                stage_name=self.stage.name,
                backend_name=backend_config.backend.name,
            )
        )

    def _validate_backend_hosts(self, backend_configs):
        for backend_config in backend_configs:
            hosts = backend_config.config.get("hosts")
            if not hosts:
                self._raise_invalid_backend_config(backend_config)

            for host in hosts:
                if not core_constants.HOST_WITHOUT_SCHEME_PATTERN.match(host.get("host", "")):
                    self._raise_invalid_backend_config(backend_config)

    def _validate_stage_backends(self):
        """校验待发布环境的backend配置"""
        resource_version = self.resource_version or ResourceVersion.objects.get_latest_version(self.gateway.id)
        resource_configs = resource_version.data if resource_version and resource_version.data else []

        if resource_configs:
            backend_ids = {resource["proxy"]["backend_id"] for resource in resource_configs}
        else:
            backend_ids = set(
                Proxy.objects.filter(resource__gateway=self.gateway).values_list("backend_id", flat=True).distinct()
            )

        backend_configs = list(
            BackendConfig.objects.filter(stage=self.stage, backend_id__in=backend_ids).select_related("backend")
        )
        configured_backend_ids = {bc.backend_id for bc in backend_configs}

        # 检查资源用到的 backend 是否都有 stage 配置
        missing_backend_ids = backend_ids - configured_backend_ids
        if missing_backend_ids:
            missing_backends = list(
                Backend.objects.filter(id__in=missing_backend_ids).order_by("name").values_list("name", flat=True)
            )
            raise ReleaseValidationError(
                _("网关环境【{stage_name}】缺少后端服务【{backends}】的配置，请在网关 `后端服务` 中进行配置。").format(
                    stage_name=self.stage.name,
                    backends=", ".join(missing_backends),
                )
            )

        for backend_config in backend_configs:
            if backend_config.backend.kind == BackendKindEnum.AI.value:
                try:
                    config = backend_config.config
                except ValueError:
                    raise ReleaseValidationError(
                        _(
                            "网关环境【{stage_name}】中的模型后端服务【{backend_name}】配置解密失败，不允许发布。"
                        ).format(
                            stage_name=self.stage.name,
                            backend_name=backend_config.backend.name,
                        )
                    ) from None

                try:
                    AIBackendConfig.model_validate(config)
                except ValueError:
                    raise ReleaseValidationError(
                        _(
                            "网关环境【{stage_name}】中的模型后端服务【{backend_name}】配置结构不合法，不允许发布。"
                        ).format(
                            stage_name=self.stage.name,
                            backend_name=backend_config.backend.name,
                        )
                    ) from None
                continue

            self._validate_backend_hosts([backend_config])

    def _validate_stage_plugins(self):
        """校验待发布环境的plugin配置"""

        # 环境绑定的插件，同一类型，只能绑定一个即同一个类型的PluginConfig只能绑定一个环境
        stage_plugins = (
            PluginBinding.objects.filter(
                scope_id=self.stage.id,
                scope_type=PluginBindingScopeEnum.STAGE.value,
            )
            .select_related("config__type")
            .all()
        )
        stage_plugin_type_set = set()
        for stage_plugin in stage_plugins:
            plugin_config = stage_plugin.config
            if plugin_config is None or plugin_config.type is None:
                raise ReleaseValidationError(
                    _("网关环境【{stage_name}】存在插件配置或插件类型为空的插件绑定，不允许发布。").format(
                        stage_name=self.stage.name,
                    )
                )

            plugin_code = plugin_config.type.code
            if plugin_code in stage_plugin_type_set:
                raise ReleaseValidationError(
                    _("网关环境【{stage_name}】存在绑定多个相同类型[{plugin_code}]的插件。").format(
                        stage_name=self.stage.name,
                        plugin_code=plugin_code,
                    )
                )
            stage_plugin_type_set.add(plugin_code)

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

    def _validate_resource_version_schema(self):
        if not self.resource_version.is_schema_v2:
            raise ReleaseValidationError(
                _("版本【{resource_version}】数据结构已经不兼容，不允许发布，请在【资源配置】中新建版本再发布").format(
                    resource_version=self.resource_version.object_display
                )
            )

    def _validate_gateway_status(self):
        if self.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise ReleaseValidationError(
                _("网关【{gateway_name}】没有启用，不允许发布").format(gateway_name=self.gateway.name)
            )

    def __call__(self):
        """执行网关环境发布校验，用于发布前统一检查环境与资源版本是否满足发布条件。

        GatewayReleaser 或环境序列化器需要判断某个环境是否允许发布指定资源版本时使用。

        Args:
            None: 校验所需的 gateway、stage、resource_version 来自构造函数。

        Returns:
            None: 校验通过时不返回值；校验失败时抛出 ReleaseValidationError 或
                serializers.ValidationError。
        """

        # 校验网关启用状态
        self._validate_gateway_status()

        # stage相关配置
        self._validate_stage_backends()
        self._validate_stage_plugins()

        if self.resource_version:
            self._validate_resource_version_schema()
            # FIXME: 这里需要遍历所有的资源版本资源，进行校验，比较损耗性能
            self._validate_stage_vars(self.stage, self.resource_version.id)
