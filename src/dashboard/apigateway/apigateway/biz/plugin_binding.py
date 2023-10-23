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
from typing import List

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
    def get_stage_plugin_binding(gateway_id: int, stage_id: int) -> dict:
        """获取环境绑定的插件"""
        stage_plugin_bindings = PluginBinding.objects.filter(
            gateway_id=gateway_id, scope_type=PluginBindingScopeEnum.STAGE.value, scope_id=stage_id
        ).prefetch_related("config", "config__type")
        return {plugin_binding.get_type(): plugin_binding for plugin_binding in stage_plugin_bindings}
