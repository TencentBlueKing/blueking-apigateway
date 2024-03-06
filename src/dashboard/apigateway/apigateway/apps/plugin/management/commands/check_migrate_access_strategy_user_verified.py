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
from django.core.management.base import BaseCommand

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginType
from apigateway.core.models import Gateway
from apigateway.utils.yaml import yaml_dumps

from .migrate_access_strategy_user_verified import (
    init_app_plugin_config,
    init_stage_app_code_plugin_config,
    merge_plugin_config,
)

# 仅在 1.13 使用， 1.14 会删掉


class Command(BaseCommand):
    """校验访问策略迁移数据"""

    def handle(self, *args, **options):
        gateway_ids = (
            AccessStrategy.objects.filter(type=AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value)
            .values_list("api__id", flat=True)
            .distinct()
        )

        for gateway_id in gateway_ids:
            gateway = Gateway.objects.get(id=gateway_id)
            stage_app_code_plugin_config = init_stage_app_code_plugin_config(gateway)
            app_code_plugin_config = init_app_plugin_config(gateway)
            merged_config = merge_plugin_config(stage_app_code_plugin_config, app_code_plugin_config)

            plugin_type = PluginType.objects.get(code="bk-verified-user-exempted-apps")

            for stage_id, app_code_plugin_config in merged_config.items():
                exempted_apps = list(app_code_plugin_config.values())

                exist_plugin_binding = PluginBinding.objects.filter(
                    gateway=gateway,
                    scope_type=PluginBindingScopeEnum.STAGE.value,
                    scope_id=stage_id,
                    config__type=plugin_type,
                ).first()

                if not exempted_apps and exist_plugin_binding:
                    self.stdout.write(
                        f"empty exempted_apps: gateway_id={gateway_id}, stage_id={stage_id}, but have binding"
                    )
                    continue

                if not exist_plugin_binding:
                    self.stdout.write(f"missing plugin binding: gateway_id={gateway_id}, stage_id={stage_id}")
                    continue

                data = {"exempted_apps": exempted_apps}
                yaml = yaml_dumps(data)

                if exist_plugin_binding.config.yaml != yaml:
                    self.stdout.write(
                        f"mismatch plugin binding: gateway_id={gateway_id}, stage_id={stage_id}, expect={yaml}, actual={exist_plugin_binding.config.yaml}"
                    )

        self.stdout.write(f"{len(gateway_ids)} gateways checked")
