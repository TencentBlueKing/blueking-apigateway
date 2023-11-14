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
from typing import Dict, Optional

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.utils.time import now_datetime
from apigateway.utils.yaml import yaml_dumps


class HeaderRewriteConvertor:
    @staticmethod
    def transform_headers_to_plugin_config(transform_headers: dict) -> Optional[dict]:
        # both set and delete empty
        if not transform_headers or (not transform_headers.get("set") and not transform_headers.get("delete")):
            return None

        return {
            "set": [{"key": key, "value": value} for key, value in (transform_headers.get("set") or {}).items()],
            "remove": [{"key": key} for key in (transform_headers.get("delete") or [])],
        }

    @classmethod
    def sync_plugins(
        cls,
        gateway_id: int,
        scope_type: str,
        scope_id_to_plugin_config: Dict[int, Optional[Dict]],
        username: str,
    ):
        """根据配置，同步 bk-header-rewrite 插件与 scope 对象的绑定
        - scope_type: Scope 类型
        - scope_id_to_plugin_config: Scope id 到插件配置的映射
        - username: 当前操作者的用户名
        """
        plugin_type = PluginType.objects.get(code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value)
        exist_bindings = {
            binding.scope_id: binding
            for binding in PluginBinding.objects.filter(
                gateway_id=gateway_id,
                scope_type=scope_type,
                scope_id__in=scope_id_to_plugin_config.keys(),
                config__type=plugin_type,
            ).prefetch_related("config")
        }

        add_bindings = {}
        update_plugin_configs = []
        delete_bindings = []

        for scope_id, plugin_config in scope_id_to_plugin_config.items():
            if not plugin_config:
                if scope_id in exist_bindings:
                    # 配置为空，但是插件已存在，则删除
                    delete_bindings.append(exist_bindings[scope_id])
                continue

            if scope_id in exist_bindings:
                # 插件已绑定，更新插件配置
                plugin_config_obj = exist_bindings[scope_id].config
                plugin_config_obj.yaml = yaml_dumps(plugin_config)
                plugin_config_obj.updated_by = username
                plugin_config_obj.updated_time = now_datetime()
                update_plugin_configs.append(plugin_config_obj)
            else:
                # 插件未绑定，新建插件配置
                add_bindings[scope_id] = PluginConfig(
                    gateway_id=gateway_id,
                    name=cls._generate_plugin_name(scope_type, scope_id),
                    type=plugin_type,
                    yaml=yaml_dumps(plugin_config),
                    created_by=username,
                )

        if add_bindings:
            PluginConfig.objects.bulk_create(add_bindings.values(), batch_size=100)

            plugin_configs = {
                config.name: config for config in PluginConfig.objects.filter(gateway_id=gateway_id, type=plugin_type)
            }

            bindings = []
            for scope_id in add_bindings:
                plugin_name = add_bindings[scope_id].name
                plugin_config = plugin_configs[plugin_name]
                bindings.append(
                    PluginBinding(
                        gateway_id=gateway_id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        config=plugin_config,
                        created_by=username,
                    )
                )
            PluginBinding.objects.bulk_create(bindings, batch_size=100)

        if update_plugin_configs:
            PluginConfig.objects.bulk_update(
                update_plugin_configs, fields=["yaml", "updated_by", "updated_time"], batch_size=100
            )

        if delete_bindings:
            PluginBinding.objects.filter(
                gateway_id=gateway_id, id__in=[binding.id for binding in delete_bindings]
            ).delete()
            PluginConfig.objects.filter(
                gateway_id=gateway_id, id__in=[binding.config.id for binding in delete_bindings]
            ).delete()

    @staticmethod
    def _generate_plugin_name(scope_type: str, scope_id: int) -> str:
        return f"bk-header-rewrite::{scope_type}::{scope_id}"
