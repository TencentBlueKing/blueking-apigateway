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
from copy import deepcopy
from typing import Optional

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.core.models import Gateway
from apigateway.utils.yaml import yaml_dumps


class HeaderRewriteConvertor:
    @staticmethod
    def transform_headers_to_plugin_config(transform_headers: dict) -> Optional[dict]:
        # both set and delete empty
        if not transform_headers or (
            not transform_headers.get("set", None) and not transform_headers.get("delete", None)
        ):
            return None

        return {"set": transform_headers.get("set") or {}, "remove": transform_headers.get("delete") or []}

    @staticmethod
    def merge_plugin_config(stage_config: Optional[dict], resource_config: Optional[dict]) -> Optional[dict]:
        if not stage_config and not resource_config:
            return None

        if not stage_config and resource_config:
            return resource_config

        if stage_config and not resource_config:
            return stage_config

        merge_config = deepcopy(stage_config)
        merge_config["set"].update(resource_config.get("set", {}))  # type: ignore
        for key in resource_config.get("remove", []):  # type: ignore
            if key not in merge_config["remove"]:  # type: ignore
                merge_config["remove"].append(key)  # type: ignore

        return merge_config

    @staticmethod
    def alter_plugin(gateway: Gateway, scope_type: str, scope_id: int, plugin_config: Optional[dict]):
        # 1. 判断resource是否已经绑定header rewrite插件
        binding = (
            PluginBinding.objects.filter(
                scope_type=scope_type,
                scope_id=scope_id,
                config__type__code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value,
            )
            .prefetch_related("config")
            .first()
        )

        # 2. 创建/更新/删除对应的插件与插件配置
        # 插件配置为空, 清理数据
        if binding and not plugin_config:
            config = binding.config
            # NOTE: 用bulk_delete避免触发信号
            PluginBinding.objects.bulk_delete([binding])
            PluginConfig.objects.bulk_delete([config])
            return

        # 如果没有绑定, 新建插件配置, 并绑定到stage
        if not binding and plugin_config:
            config = PluginConfig(
                api=gateway,
                name=f"{scope_type} [{scope_id}] header rewrite",
                type=PluginType.objects.get(code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value),
                yaml=yaml_dumps(plugin_config),
            )
            config.save()
            binding = PluginBinding(
                api=gateway,
                scope_type=scope_type,
                scope_id=scope_id,
                config=config,
            )
            # NOTE: 用bulk_create避免触发信号
            PluginBinding.objects.bulk_create([binding])
            return

        # 如果已经绑定, 更新插件配置
        if binding and plugin_config:
            config = binding.config
            config.yaml = yaml_dumps(plugin_config)
            # NOTE: 用bulk_update避免触发信号
            PluginConfig.objects.bulk_update([config], ["yaml"])
