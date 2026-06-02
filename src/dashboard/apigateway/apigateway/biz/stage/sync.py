# -*- coding: utf-8 -*-
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
from typing import Any, Dict, List, Optional

from django.utils.translation import gettext as _
from pydantic import TypeAdapter
from rest_framework import serializers

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginType
from apigateway.biz.plugin import PluginConfigData, PluginSynchronizer
from apigateway.core.constants import LoadBalanceTypeEnum
from apigateway.service.plugin import PluginConfigYamlValidator


class StageSyncHandler:
    @staticmethod
    def build_proxy_http_backend_config(proxy_http_config: dict) -> dict:
        """Build backend config from open-v1 proxy_http input payload."""
        hosts = []
        for host in proxy_http_config["upstreams"]["hosts"]:
            scheme, _host = host["host"].rstrip("/").split("://")
            hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})

        return {
            "type": "node",
            "timeout": proxy_http_config["timeout"],
            "loadbalance": proxy_http_config["upstreams"]["loadbalance"],
            "hosts": hosts,
        }

    @staticmethod
    def build_backend_item_config(backend_item: dict) -> dict:
        """Build backend config from one `backends` list item payload (used by open + v2/sync)."""
        backend_config = backend_item["config"]

        hosts = []
        for host in backend_config["hosts"]:
            scheme, _host = host["host"].rstrip("/").split("://")
            hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})

        loadbalance = backend_config["loadbalance"]
        config = {
            "type": "node",
            "timeout": backend_config["timeout"],
            "loadbalance": loadbalance,
            "hosts": hosts,
        }

        if loadbalance == LoadBalanceTypeEnum.CHASH.value:
            config["hash_on"] = backend_config["hash_on"]
            config["key"] = backend_config["key"]

        if backend_config.get("checks"):
            config["checks"] = backend_config["checks"]

        return config

    @staticmethod
    def validate_plugin_configs(plugin_configs: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
        """
        校验插件配置
        - 1. 插件类型不能重复
        - 2. 插件类型必须已存在
        - 3. 插件配置，必须符合插件类型的 schema 约束
        """
        if not plugin_configs:
            return plugin_configs

        types = set()
        for plugin_config in plugin_configs:
            plugin_type = plugin_config["type"]
            if plugin_type in types:
                raise serializers.ValidationError(_("插件类型重复：{plugin_type}。").format(plugin_type=plugin_type))
            types.add(plugin_type)

        all_plugin_type = PluginType.objects.all()
        exist_plugin_types = set(all_plugin_type.values_list("code", flat=True))
        not_exist_types = types - exist_plugin_types
        if not_exist_types:
            raise serializers.ValidationError(
                _("插件类型 {not_exist_types} 不存在。").format(not_exist_types=", ".join(not_exist_types))
            )

        plugin_types = {plugin_type.code: plugin_type for plugin_type in all_plugin_type}
        yaml_validator = PluginConfigYamlValidator()

        for plugin_config in plugin_configs:
            plugin_type = plugin_types[plugin_config["type"]]
            try:
                yaml_validator.validate(
                    plugin_type.code,
                    plugin_config["yaml"],
                    plugin_type.schema and plugin_type.schema.schema,
                )
            except Exception as err:  # pylint: disable=broad-except
                raise serializers.ValidationError(
                    _("插件配置校验失败，插件类型：{plugin_type_code}，错误信息：{err}。").format(
                        plugin_type_code=plugin_type.code,
                        err=err,
                    )
                )

        return plugin_configs

    @staticmethod
    def sync_plugin_configs(gateway_id: int, stage_id: int, plugin_configs: Optional[List[Dict[str, Any]]]) -> None:
        # plugin_configs 为 None 则，plugin_config_datas 设置 [] 则清空对应配置
        plugin_config_datas = (
            TypeAdapter(Optional[List[PluginConfigData]]).validate_python(plugin_configs) if plugin_configs else []
        )

        scope_id_to_plugin_configs = {stage_id: plugin_config_datas}
        synchronizer = PluginSynchronizer()
        synchronizer.sync(
            gateway_id=gateway_id,
            scope_type=PluginBindingScopeEnum.STAGE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )
