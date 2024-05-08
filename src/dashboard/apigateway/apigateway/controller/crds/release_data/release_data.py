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
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from django.utils.functional import cached_property

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.plugin.plugin_convertors import PluginConvertorFactory
from apigateway.controller.crds.release_data.base import PluginData
from apigateway.core.constants import (
    DEFAULT_BACKEND_NAME,
    ContextScopeTypeEnum,
    ContextTypeEnum,
)
from apigateway.core.models import BackendConfig, Context, Gateway, Release, ResourceVersion, Stage

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
    def _stage_contexts(self) -> Dict[str, Dict[str, Any]]:
        """
        :return: A dict contains all the context objects at "stage" scope, the key is
            the type of context.
        """
        return {
            c.type: c.snapshot(as_dict=True)
            for c in Context.objects.filter(
                scope_id=self.stage.pk,
                scope_type=ContextScopeTypeEnum.STAGE.value,
            )
        }

    @cached_property
    def stage_backend_config(self) -> Dict[str, Any]:
        return json.loads(self._stage_contexts[ContextTypeEnum.STAGE_PROXY_HTTP.value]["config"])

    @cached_property
    def stage_upstreams(self) -> Dict[str, Any]:
        return self.stage_backend_config.get("upstreams")

    @cached_property
    def jwt_private_key(self) -> str:
        return GatewayJWTHandler.get_private_key(self.gateway.pk)

    @cached_property
    def api_auth_config(self) -> Dict[str, Any]:
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

    def get_resource_plugins(self, resource_id: int) -> List[PluginData]:
        plugins = self._resources_plugins.get(resource_id, [])

        # 如果资源，同时绑定了同一类型的访问策略、插件，那么只使用插件配置
        name_to_plugins = {plugin.name: plugin for plugin in plugins}
        return list(name_to_plugins.values())

    @cached_property
    def _resources_plugins(self) -> Dict[int, List[PluginData]]:
        resource_id_to_plugins: Dict[int, List[PluginData]] = defaultdict(list)

        # 插件
        resource_id_to_plugin_bindings = PluginBinding.objects.query_scope_id_to_bindings(
            gateway_id=self.gateway.pk,
            scope_type=PluginBindingScopeEnum.RESOURCE,
        )
        for resource_id, bindings in resource_id_to_plugin_bindings.items():
            resource_id_to_plugins[resource_id].extend(
                [
                    PluginData(
                        type_code=binding.get_type(),
                        config=PluginConvertorFactory.get_convertor(binding.get_type()).convert(binding.config.config),
                        binding_scope_type=PluginBindingScopeEnum.RESOURCE.value,
                    )
                    for binding in bindings
                ]
            )

        return resource_id_to_plugins

    def get_resources_upstream(self, resource_proxy: Dict[str, Any], backend_id: int):
        return resource_proxy.get("upstreams")

    def get_upstream_host(self, upstream: Dict[str, Any]) -> str:
        return upstream["host"]


class ReleaseDataV2(ReleaseData):
    @cached_property
    def _stage_backend(self) -> BackendConfig:
        """
        :return: A dict contains all the backend objects at "stage" scope, the key is
            the type of backend, such as "http/grpc".
        """
        return (
            BackendConfig.objects.filter(
                gateway_id=self.gateway.pk, stage_id=self.stage.pk, backend__name=DEFAULT_BACKEND_NAME
            )
            .prefetch_related("backend")
            .get()
        )

    @property
    def stage_upstreams(self) -> Dict[str, Any]:
        return self.stage_backend_config

    @property
    def stage_backend_config(self) -> Dict[str, Any]:
        return self._stage_backend.config

    def get_resources_upstream(self, resource_proxy: Dict[str, Any], backend_id: int) -> Dict[str, Any]:
        return (
            BackendConfig.objects.filter(
                backend_id=backend_id,
                gateway_id=self.gateway.pk,
                stage_id=self.stage.pk,
            )
            .values_list("config", flat=True)
            .first()
        )

    def get_upstream_host(self, upstream: Dict[str, Any]) -> str:
        return upstream["scheme"] + "://" + upstream["host"]

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
