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

from collections import defaultdict
from typing import Dict

from django.core.management.base import BaseCommand

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.core.models import Gateway, Stage
from apigateway.utils.yaml import yaml_dumps


def init_stage_app_code_plugin_config(gateway: Gateway) -> Dict[int, Dict[str, Dict]]:
    """
    {
        123: {
            "app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}
        }
    }
    """
    stages = Stage.objects.filter(gateway=gateway).all()

    stage_plugin_config: Dict[int, Dict[str, Dict]] = {}
    # get all stage bindings
    for stage in stages:
        binding = AccessStrategyBinding.objects.filter(
            type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            scope_id=stage.id,
        ).first()
        # should generate a empty config for those stage without binding
        if not binding:
            stage_plugin_config[stage.id] = {}
        else:
            # {"bk_app_code_list": ["codm-api-server", "codm-ops-new"]}
            config = binding.access_strategy.config
            bk_app_code_list = config.get("bk_app_code_list", [])

            stage_plugin_config[stage.id] = {}
            # if the bk_app_code_list is empty, here will generate a empty config too
            for app_code in bk_app_code_list:
                stage_plugin_config[stage.id][app_code] = {
                    "bk_app_code": app_code,
                    "dimension": "api",
                    "resource_ids": [],
                }

    return stage_plugin_config


def init_app_plugin_config(gateway: Gateway) -> Dict[str, Dict]:
    """
    {
        "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [1,2,3]},
        "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1,2,3]}
    }
    """
    # while the resource_id in AccessStrategyBinding is uniq, use list here
    app_code_resource_ids = defaultdict(list)

    bindings = AccessStrategyBinding.objects.filter(
        type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value,
        scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
        access_strategy__api=gateway,
    ).all()
    for binding in bindings:
        resource_id = binding.scope_id

        config = binding.access_strategy.config
        bk_app_code_list = config.get("bk_app_code_list", [])
        for app_code in bk_app_code_list:
            app_code_resource_ids[app_code].append(resource_id)

    app_code_plugin_config = {}
    for app_code, resource_ids in app_code_resource_ids.items():
        app_code_plugin_config[app_code] = {
            "bk_app_code": app_code,
            "dimension": "resource",
            "resource_ids": resource_ids,
        }

    return app_code_plugin_config


def merge_plugin_config(
    stage_app_code_plugin_config: Dict[int, Dict[str, Dict]], app_code_plugin_config: Dict[str, Dict]
) -> Dict[int, Dict[str, Dict]]:
    assert len(stage_app_code_plugin_config) > 0
    merged_config: Dict[int, Dict[str, Dict]] = {}

    for stage_id, s_app_code_plugin_config in stage_app_code_plugin_config.items():
        # loop the   app_code => [resource_id]
        for app_code, plugin_config in app_code_plugin_config.items():
            if app_code not in s_app_code_plugin_config:
                s_app_code_plugin_config[app_code] = plugin_config
            else:
                print(
                    f"app_code: {app_code} already in stage: {stage_id}, skip, the resource_ids in {plugin_config} maybe permission amplification"
                )

        merged_config[stage_id] = s_app_code_plugin_config

    return merged_config


class Command(BaseCommand):
    """将访问策略 access_strategy 迁移成 pluginConfig"""

    def handle(self, *args, **options):
        # TODO: migrate for  USER_VERIFIED_UNREQUIRED_APPS
        gateway_ids = (
            AccessStrategy.objects.filter(type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value)
            .values_list("api__id", flat=True)
            .distinct()
        )

        count = 0
        for gateway_id in gateway_ids:
            gateway = Gateway.objects.get(id=gateway_id)

            # get stage_id => {app_code:*}
            # {
            #     123: {
            #         "app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []}
            #     }
            # }
            stage_app_code_plugin_config = init_stage_app_code_plugin_config(gateway)

            # get app_code => [resource_id]
            # {
            #     "app_123": {"bk_app_code": "app_123", "dimension": "resource", "resource_ids": [1,2,3]},
            #     "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1,2,3]}
            # }
            app_code_plugin_config = init_app_plugin_config(gateway)

            # merge
            # {
            #     123: {
            #         "app_123": {"bk_app_code": "app_123", "dimension": "api", "resource_ids": []},
            #         "app_456": {"bk_app_code": "app_456", "dimension": "resource", "resource_ids": [1,2,3]}
            #     }
            # }
            merged_config = merge_plugin_config(stage_app_code_plugin_config, app_code_plugin_config)

            plugin_type = PluginType.objects.get(code="bk-verified-user-exempted-apps")
            plugin_config_name = "merged_user_verified_unrequired_apps"
            # generate pluginConfig and do binding
            for stage_id, app_code_plugin_config in merged_config.items():
                exempted_apps = list(app_code_plugin_config.values())

                if not exempted_apps:
                    # TODO: should remove migrated plugin binding?
                    self.stdout.write(
                        f"gateway: {gateway}, stage: {stage_id} get no bk-verified-user-exempted-apps plugin_config, skip",
                    )
                    continue

                data = {"exempted_apps": exempted_apps}
                plugin_config = PluginConfig(
                    gateway=gateway,
                    name=plugin_config_name,
                    type=plugin_type,
                    yaml=yaml_dumps(data),
                )

                exist_plugin_binding = PluginBinding.objects.filter(
                    gateway=gateway,
                    scope_type=PluginBindingScopeEnum.STAGE.value,
                    scope_id=stage_id,
                    config__type=plugin_config.type,
                ).first()
                if exist_plugin_binding:
                    self.stdout.write(
                        f"update plugin binding: {exist_plugin_binding}, plugin config: {exist_plugin_binding.config}",
                    )
                    # update the config
                    config = exist_plugin_binding.config
                    config.name = plugin_config.name
                    config.yaml = plugin_config.yaml
                    config.save()
                else:
                    # save the config
                    plugin_config.save()

                    # create a new one
                    plugin_binding = PluginBinding(
                        gateway=gateway,
                        scope_type=PluginBindingScopeEnum.STAGE.value,
                        scope_id=stage_id,
                        config=plugin_config,
                    )
                    plugin_binding.save()
                    self.stdout.write(f"create a new plugin binding: {plugin_binding}, plugin config: {plugin_config}")
