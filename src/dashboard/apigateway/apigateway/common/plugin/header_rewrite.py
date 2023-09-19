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

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
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

    @staticmethod
    def alter_plugin(gateway_id: int, scope_type: str, scope_id: int, plugin_config: Optional[dict]):
        # 判断是否已经绑定header rewrite插件
        binding = (
            PluginBinding.objects.filter(
                scope_type=scope_type,
                scope_id=scope_id,
                config__type__code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value,
            )
            .prefetch_related("config")
            .first()
        )

        if not binding and not plugin_config:
            return

        if binding:
            if plugin_config:
                # 如果已经绑定, 更新插件配置
                config = binding.config
                config.yaml = yaml_dumps(plugin_config)
                PluginConfig.objects.bulk_update([config], ["yaml"])
                return

            # 插件配置为空, 清理数据
            config = binding.config
            PluginBinding.objects.bulk_delete([binding])
            PluginConfig.objects.bulk_delete([config])
            return

        # 如果没有绑定, 新建插件配置, 并绑定到scope
        if plugin_config:
            config = PluginConfig(
                gateway_id=gateway_id,
                name=f"{scope_type} [{scope_id}] header rewrite",
                type=PluginType.objects.get(code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value),
                yaml=yaml_dumps(plugin_config),
            )
            config.save()
            binding = PluginBinding(
                gateway_id=gateway_id,
                scope_type=scope_type,
                scope_id=scope_id,
                config=config,
            )
            PluginBinding.objects.bulk_create([binding])
