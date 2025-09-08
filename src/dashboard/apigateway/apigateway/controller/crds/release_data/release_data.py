#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from django.utils.functional import cached_property

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.controller.crds.release_data.base import PluginData
from apigateway.core.models import BackendConfig, Gateway, Release, ResourceVersion, Stage
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.gateway_jwt import GatewayJWTHandler
from apigateway.service.plugin.convertor import PluginConvertorFactory

logger = logging.getLogger(__name__)


@dataclass
class ReleaseData:
    _release: Release

    @cached_property
    def gateway(self) -> Gateway:
        return self._release.gateway

    @cached_property
    def stage(self) -> Stage:
        return self._release.stage

    @cached_property
    def resource_version(self) -> ResourceVersion:
        return self._release.resource_version

    @cached_property
    def jwt_private_key(self) -> str:
        return GatewayJWTHandler.get_private_key(self.gateway.pk)

    @cached_property
    def gateway_auth_config(self) -> Dict[str, Any]:
        return GatewayAuthContext().get_config(self.gateway.pk)

    def get_stage_plugins(self) -> List[PluginData]:
        plugins: List[PluginData] = []

        # 插件
        stage_id_to_plugin_bindings = PluginBinding.objects.query_scope_id_to_bindings(
            gateway_id=self.gateway.pk,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_ids=[self.stage.pk],
        )
        plugins.extend(
            [
                PluginData(
                    type_code=binding.get_type(),
                    config=PluginConvertorFactory.get_convertor(binding.get_type()).convert(binding.config.config),
                    binding_scope_type=PluginBindingScopeEnum.STAGE.value,
                )
                for binding in stage_id_to_plugin_bindings.get(self.stage.pk, [])
            ]
        )

        # 如果环境，同时绑定了同一类型的访问策略、插件，那么只使用插件配置
        name_to_plugins = {plugin.name: plugin for plugin in plugins}
        return list(name_to_plugins.values())

    def get_stage_backend_configs(self) -> Dict[int, Dict[str, Any]]:
        backend_configs = (
            BackendConfig.objects.filter(
                gateway_id=self.gateway.pk,
                stage_id=self.stage.pk,
            )
            .prefetch_related("backend")
            .all()
        )

        return {b.backend.id: b.config for b in backend_configs}

    def get_resource_plugins(self, resource_id: int) -> List[PluginData]:
        plugins = self._resources_plugins.get(resource_id, [])

        # 如果资源，同时绑定了同一类型的访问策略、插件，那么只使用插件配置
        name_to_plugins = {plugin.name: plugin for plugin in plugins}
        return list(name_to_plugins.values())

    @property
    def _resources_plugins(self) -> Dict[int, List[PluginData]]:
        resource_id_to_plugins: Dict[int, List[PluginData]] = defaultdict(list)

        # 插件
        resource_configs = self.resource_version.data
        for resource in resource_configs:
            resource_id_to_plugins[resource["id"]].extend(
                [
                    PluginData(
                        type_code=binding["type"],
                        config=PluginConvertorFactory.get_convertor(binding["type"]).convert(binding["config"]),
                        binding_scope_type=PluginBindingScopeEnum.RESOURCE.value,
                    )
                    for binding in resource.get("plugins", [])
                ]
            )

        return resource_id_to_plugins
