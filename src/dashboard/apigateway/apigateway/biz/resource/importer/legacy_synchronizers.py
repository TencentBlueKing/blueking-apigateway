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
# 1.13 版本: 兼容旧版 (api_version=0.1) 资源 yaml 通过 openapi 导入
import logging
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.biz.resource.models import ResourceData
from apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor
from apigateway.core.constants import DEFAULT_BACKEND_NAME, STAGE_VAR_PATTERN
from apigateway.core.models import Backend, BackendConfig, Gateway, Stage
from apigateway.utils.yaml import yaml_dumps

logger = logging.getLogger(__name__)


LEGACY_BACKEND_NAME_PREFIX = "backend-"


class LegacyUpstream:
    def __init__(self, upstreams: Dict[str, Any]):
        self.upstreams = upstreams

    def get_stage_id_to_backend_config(
        self,
        stages: List[Stage],
        stage_id_to_timeout: Dict[int, int],
    ) -> Dict[int, Dict]:
        """获取此 upstream 对应的后端，在各个环境的后端配置"""
        backend_configs = {}

        for stage in stages:
            stage_vars = stage.vars

            hosts = []
            for host in self.upstreams["hosts"]:
                scheme, host_ = host["host"].rstrip("/").split("://")
                hosts.append(
                    {
                        "scheme": scheme,
                        "host": self._render_host(stage_vars, host_),
                        "weight": host["weight"],
                    }
                )

            backend_configs[stage.id] = {
                "type": "node",
                # 新创建的后端，其超时时间，默认使用 default 后端在各环境配置的超时时间
                "timeout": stage_id_to_timeout[stage.id],
                "loadbalance": self.upstreams["loadbalance"],
                "hosts": hosts,
            }

        return backend_configs

    def _render_host(self, vars: Dict[str, Any], host: str) -> str:
        def replace(matched):
            return vars.get(matched.group(1), matched.group(0))

        return re.sub(STAGE_VAR_PATTERN, replace, host)


class LegacyBackendCreator:
    def __init__(self, gateway: Gateway, username: str):
        self.gateway = gateway
        self.username = username

        self._existing_backends = {backend.id: backend for backend in Backend.objects.filter(gateway=gateway)}
        self._existing_backend_configs = self._get_existing_backend_configs()
        self._max_legacy_backend_number = self._get_max_legacy_backend_number()

    def match_or_create_backend(self, stage_id_to_backend_config: Dict[int, Dict]) -> Backend:
        """根据后端配置，匹配一个后端服务；如果未匹配，根据规则生成一个新的后端服务"""
        # 排序 hosts，使其与 existing_backend_configs 中 hosts 顺序一致，便于对比数据
        for backend_config in stage_id_to_backend_config.values():
            backend_config["hosts"] = self._sort_hosts(backend_config["hosts"])

        backend_id = self._match_existing_backend(stage_id_to_backend_config)
        if backend_id:
            return self._existing_backends[backend_id]

        new_backend_name = self._generate_new_backend_name()
        backend = self._create_backend_and_backend_configs(new_backend_name, stage_id_to_backend_config)

        # 用新创建的 backend 更新辅助数据
        self._existing_backends[backend.id] = backend
        self._existing_backend_configs[backend.id] = stage_id_to_backend_config

        return backend

    def _match_existing_backend(self, stage_id_to_backend_config: Dict[int, Dict]) -> Optional[int]:
        for backend_id, existing_backend_configs in self._existing_backend_configs.items():
            if stage_id_to_backend_config == existing_backend_configs:
                return backend_id

        return None

    def _get_existing_backend_configs(self) -> Dict[int, Dict[int, Dict]]:
        """仅获取名称以 backend- 开头的后端服务的配置；即根据后端配置匹配后端服务时，仅匹配同一规则创建的后端服务"""

        # 对应关系：backend_id -> stage_id -> config
        backend_configs: Dict[int, Dict[int, Dict]] = defaultdict(dict)

        for backend_config in BackendConfig.objects.filter(
            gateway=self.gateway,
            backend__name__startswith=LEGACY_BACKEND_NAME_PREFIX,
        ):
            config = backend_config.config
            config["hosts"] = self._sort_hosts(config["hosts"])

            backend_configs[backend_config.backend_id][backend_config.stage_id] = config

        return backend_configs

    def _generate_new_backend_name(self) -> str:
        self._max_legacy_backend_number += 1
        return f"{LEGACY_BACKEND_NAME_PREFIX}{self._max_legacy_backend_number}"

    def _create_backend_and_backend_configs(
        self,
        backend_name: str,
        stage_id_to_backend_config: Dict[int, Dict],
    ) -> Backend:
        backend = Backend.objects.create(
            gateway=self.gateway, name=backend_name, created_by=self.username, updated_by=self.username
        )

        backend_configs = [
            BackendConfig(
                gateway=self.gateway,
                stage_id=stage_id,
                backend=backend,
                config=config,
                created_by=self.username,
                updated_by=self.username,
            )
            for stage_id, config in stage_id_to_backend_config.items()
        ]
        BackendConfig.objects.bulk_create(backend_configs)

        return backend

    def _sort_hosts(self, hosts: List[Dict[str, Dict]]) -> List[Dict[str, Dict]]:
        # 排序 host，使用 "==" 对比配置时顺序一致
        return sorted(hosts, key=lambda x: "{}://{}#{}".format(x["scheme"], x["host"], x["weight"]))

    def _get_max_legacy_backend_number(self) -> int:
        """获取网关创建的后端中，后端名称中已使用的最大序号"""
        names = Backend.objects.filter(gateway=self.gateway, name__startswith=LEGACY_BACKEND_NAME_PREFIX).values_list(
            "name", flat=True
        )

        backend_numbers = [
            int(name[len(LEGACY_BACKEND_NAME_PREFIX) :])
            for name in names
            if name[len(LEGACY_BACKEND_NAME_PREFIX) :].isdigit()
        ]
        return max(backend_numbers, default=0)


class LegacyUpstreamToBackendSynchronizer:
    def __init__(self, gateway: Gateway, resource_data_list: List[ResourceData], username: str):
        self.gateway = gateway
        self.resource_data_list = resource_data_list
        self.username = username

    def sync_backends_and_replace_resource_backend(self):
        if not self._has_legacy_upstreams():
            return

        self._sync_backends_and_replace_resource_backend()

    def _has_legacy_upstreams(self) -> bool:
        return any(resource_data.backend_config.legacy_upstreams for resource_data in self.resource_data_list)

    def _sync_backends_and_replace_resource_backend(self):
        backend_creator = LegacyBackendCreator(self.gateway, self.username)
        stages = list(Stage.objects.filter(gateway=self.gateway))
        stage_id_to_timeout = self._get_stage_id_to_default_timeout()

        for resource_data in self.resource_data_list:
            if not resource_data.backend_config.legacy_upstreams:
                continue

            legacy_upstream = LegacyUpstream(resource_data.backend_config.legacy_upstreams)
            stage_id_to_backend_config = legacy_upstream.get_stage_id_to_backend_config(stages, stage_id_to_timeout)
            backend = backend_creator.match_or_create_backend(stage_id_to_backend_config)
            resource_data.backend = backend

    def _get_stage_id_to_default_timeout(self) -> Dict[int, int]:
        return {
            backend_config.stage_id: backend_config.config["timeout"]
            for backend_config in BackendConfig.objects.filter(
                gateway=self.gateway,
                backend__name=DEFAULT_BACKEND_NAME,
            )
        }


class LegacyTransformHeadersToPluginSynchronizer:
    def __init__(self, gateway: Gateway, resource_data_list: List[ResourceData], username: str):
        self.gateway = gateway
        self.resource_data_list = resource_data_list
        self.username = username

    def sync_plugins(self):
        if not self._has_legacy_transform_headers():
            return

        plugin_type = PluginType.objects.get(code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value)
        exist_bindings = {
            binding.scope_id: binding
            for binding in PluginBinding.objects.filter(
                gateway=self.gateway,
                scope_type=PluginBindingScopeEnum.RESOURCE.value,
                config__type=plugin_type,
            ).prefetch_related("config")
        }

        add_bindings = {}
        update_plugin_configs = []
        delete_bindings = []
        for resource_data in self.resource_data_list:
            transform_headers = resource_data.backend_config.legacy_transform_headers
            if transform_headers is None:
                continue

            assert resource_data.resource

            plugin_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(transform_headers)
            if not plugin_config:
                if resource_data.resource.id in exist_bindings:
                    delete_bindings.append(exist_bindings[resource_data.resource.id])
                continue

            if resource_data.resource.id not in exist_bindings:
                add_bindings[resource_data.resource.id] = PluginConfig(
                    gateway=self.gateway,
                    name=self._generate_plugin_name(resource_data.resource.id),
                    type=plugin_type,
                    yaml=yaml_dumps(plugin_config),
                )
            else:
                plugin_config_obj = exist_bindings[resource_data.resource.id].config
                plugin_config_obj.yaml = yaml_dumps(plugin_config)
                update_plugin_configs.append(plugin_config_obj)

        if add_bindings:
            PluginConfig.objects.bulk_create(add_bindings.values(), batch_size=100)

            plugin_configs = {
                config.name: config for config in PluginConfig.objects.filter(gateway=self.gateway, type=plugin_type)
            }

            bindings = []
            for resource_id in add_bindings:
                plugin_config = plugin_configs[self._generate_plugin_name(resource_id)]
                bindings.append(
                    PluginBinding(
                        gateway=self.gateway,
                        scope_type=PluginBindingScopeEnum.RESOURCE.value,
                        scope_id=resource_id,
                        config=plugin_config,
                    )
                )
            PluginBinding.objects.bulk_create(bindings, batch_size=100)

        if update_plugin_configs:
            PluginConfig.objects.bulk_update(update_plugin_configs, fields=["yaml"], batch_size=100)

        if delete_bindings:
            PluginBinding.objects.filter(
                gateway=self.gateway, id__in=[binding.id for binding in delete_bindings]
            ).delete()
            PluginConfig.objects.filter(
                gateway=self.gateway, id__in=[binding.config.id for binding in delete_bindings]
            ).delete()

    def _generate_plugin_name(self, resource_id: int) -> str:
        return f"bk-header-rewrite::resource::{resource_id}"

    def _has_legacy_transform_headers(self) -> bool:
        return any(
            resource_data.backend_config.legacy_transform_headers is not None
            for resource_data in self.resource_data_list
        )
