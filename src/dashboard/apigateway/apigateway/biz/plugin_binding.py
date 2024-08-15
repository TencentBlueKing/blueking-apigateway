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
from typing import Dict, List

from django.conf import settings
from django.db.models import Count

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig


class PluginBindingHandler:
    @staticmethod
    def delete_by_bindings(gateway_id: int, bindings: List[PluginBinding]):
        plugin_binding_ids = [binding.id for binding in bindings]
        plugin_config_ids = [binding.config.id for binding in bindings]

        PluginBinding.objects.filter(gateway_id=gateway_id, id__in=plugin_binding_ids).delete()
        PluginConfig.objects.filter(gateway_id=gateway_id, id__in=plugin_config_ids).delete()

    @staticmethod
    def get_stage_plugin_bindings(gateway_id: int, stage_id: int) -> dict:
        """获取环境绑定的插件"""
        stage_plugin_bindings = PluginBinding.objects.filter(
            gateway_id=gateway_id, scope_type=PluginBindingScopeEnum.STAGE.value, scope_id=stage_id
        ).prefetch_related("config", "config__type")
        return {plugin_binding.get_type(): plugin_binding for plugin_binding in stage_plugin_bindings}

    @staticmethod
    def get_resource_ids_plugin_binding_count(gateway_id: int, resource_ids: List[int]) -> Dict[int, int]:
        """获取资源绑定的插件数量"""
        resource_bindings = (
            PluginBinding.objects.filter(
                gateway_id=gateway_id, scope_type=PluginBindingScopeEnum.RESOURCE.value, scope_id__in=resource_ids
            )
            .values("scope_id")
            .annotate(count=Count("id"))
        )
        return {binding["scope_id"]: binding["count"] for binding in resource_bindings}

    # 应用筛选规则
    @staticmethod
    def apply_plugin_display_rules(plugins_dict: dict) -> dict:
        rules = settings.PLUGIN_FILTER_CONFIG

        # 直接在遍历过程中修改 plugins_dict
        for rule_details in rules.values():
            if "plugins" in rule_details and "display" in rule_details:
                plugins_set = set(rule_details["plugins"])

                # 检查 plugins_set 是否是 plugins_dict 的子集
                if plugins_set.issubset(set(plugins_dict.keys())):
                    display_list = set(rule_details["display"])

                    # 遍历要移除的插件
                    for plugin_type in plugins_set - display_list:
                        if plugin_type in plugins_dict:
                            del plugins_dict[plugin_type]

        return plugins_dict
