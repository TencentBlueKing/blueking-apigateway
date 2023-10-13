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
from typing import Dict, List, Tuple

from pydantic import BaseModel

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.biz.plugin_binding import PluginBindingHandler


class PluginConfigData(BaseModel):
    type: str
    yaml: str


class PluginSynchronizer:
    def sync(
        self,
        gateway_id: int,
        scope_type: PluginBindingScopeEnum,
        scope_id_to_plugin_configs: Dict[int, List[PluginConfigData]],
        username: str = "",
    ):
        code_to_plugin_type = {plugin_type.code: plugin_type for plugin_type in PluginType.objects.all()}

        remaining_key_to_binding: Dict[str, PluginBinding] = {
            f"{binding.scope_id}:{binding.config.type.code}": binding
            for binding in PluginBinding.objects.filter(
                gateway_id=gateway_id,
                scope_type=scope_type.value,
                scope_id__in=scope_id_to_plugin_configs.keys(),
            ).prefetch_related("config", "config__type")
        }

        # list[(scope_id, plugin_config)]
        add_bindings: List[Tuple[int, PluginConfig]] = []
        update_plugin_configs = []
        for scope_id, plugin_config_data_list in scope_id_to_plugin_configs.items():
            for plugin_config_data in plugin_config_data_list:
                key = f"{scope_id}:{plugin_config_data.type}"
                # scope 对象已绑定此类型插件，需更新插件配置
                if key in remaining_key_to_binding:
                    # remaining_bindings 中去除已绑定的插件，剩余的即为待删除的插件绑定
                    existing_binding = remaining_key_to_binding.pop(key)

                    plugin_config_obj = existing_binding.config
                    plugin_config_obj.config = plugin_config_data.yaml
                    plugin_config_obj.updated_by = username
                    update_plugin_configs.append(plugin_config_obj)
                else:
                    plugin_type = code_to_plugin_type[plugin_config_data.type]
                    add_bindings.append(
                        (
                            scope_id,
                            PluginConfig(
                                gateway_id=gateway_id,
                                name=self._generate_plugin_name(
                                    scope_type,
                                    scope_id,
                                    type_id=plugin_type.id,
                                ),
                                type=plugin_type,
                                yaml=plugin_config_data.yaml,
                                created_by=username,
                            ),
                        )
                    )

        if add_bindings:
            PluginConfig.objects.bulk_create([plugin_config for _, plugin_config in add_bindings], batch_size=100)

            plugin_configs = {config.name: config for config in PluginConfig.objects.filter(gateway_id=gateway_id)}
            bindings = []
            for scope_id, plugin_config in add_bindings:
                # add_bindings 中的 plugin_config 对象 id 为空，因此，需要重新获取
                bindings.append(
                    PluginBinding(
                        gateway_id=gateway_id,
                        scope_type=scope_type.value,
                        scope_id=scope_id,
                        config=plugin_configs[plugin_config.name],
                        created_by=username,
                    )
                )
            PluginBinding.objects.bulk_create(bindings, batch_size=100)

        if update_plugin_configs:
            PluginConfig.objects.bulk_update(update_plugin_configs, fields=["yaml", "updated_by"], batch_size=100)

        if remaining_key_to_binding:
            # 已创建且当前存在的 binding 已被 pop 出去，剩余的即为需要删除的 binding
            PluginBindingHandler.delete_by_bindings(gateway_id, list(remaining_key_to_binding.values()))

    def _generate_plugin_name(self, scope_type: PluginBindingScopeEnum, scope_id: int, type_id: int) -> str:
        # 因 plugin_type code 可能较长，故使用 type_id
        return f"type:{type_id}:{scope_type.value}:{scope_id}"
