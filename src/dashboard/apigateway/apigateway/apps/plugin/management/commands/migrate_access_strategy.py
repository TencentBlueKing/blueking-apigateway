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

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding
from apigateway.apps.access_strategy.utils import parse_to_plugin_config
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding


class Command(BaseCommand):
    """将访问策略 access_strategy 迁移成 pluginConfig"""

    def handle(self, *args, **options):
        for binding in AccessStrategyBinding.objects.all():
            self.stdout.write(
                f"start to migrate AccessStrategyBinding id={binding.id}"
                f" (gateway={binding.access_strategy.api}, scope_type={binding.scope_type}, "
                f"scope_id={binding.scope_id}, access_strategy={binding.access_strategy})",
            )

            # 不需要转换的在这里过滤
            if binding.type == AccessStrategyTypeEnum.CIRCUIT_BREAKER.value:
                self.stdout.write(f"skip binding: {binding}, the strategy type is CIRCUIT_BREAKER")
                continue

            if binding.type == AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS.value:
                self.stdout.write(
                    f"skip binding: {binding}, the strategy type is USER_VERIFIED_UNREQUIRED_APPS, do migrate in another place"
                )
                continue

            scope_type = binding.scope_type
            scope_id = binding.scope_id
            strategy = binding.access_strategy
            gateway = strategy.api

            plugin_scope_type = (
                PluginBindingScopeEnum.STAGE.value
                if scope_type == AccessStrategyBindScopeEnum.STAGE.value
                else PluginBindingScopeEnum.RESOURCE.value
            )

            # here we can't check the plugin_config exists
            # so, we can delete `delete from plugin_config where id not in (select config_id from plugin_binding);`
            plugin_type, plugin_config = parse_to_plugin_config(strategy)
            if not plugin_config:
                self.stdout.write(
                    f"skip binding: {binding}, the strategy {strategy} config is empty {strategy.config}",
                )

                # 重复进入的时候，如果发现为空，但是之前已经创建了，就删除; 适用于迁移后，回滚再迁移
                deleted, _ = PluginBinding.objects.filter(
                    gateway=gateway,
                    scope_type=plugin_scope_type,
                    scope_id=scope_id,
                    config__type=plugin_type,
                ).delete()
                if deleted > 0:
                    self.stdout.write(
                        f"skip binding: {binding}, the strategy {strategy} config is empty {strategy.config}, delete {deleted} plugin bindings!"
                    )

                continue

            # if exist, update
            exist_plugin_binding = PluginBinding.objects.filter(
                gateway=gateway,
                scope_type=plugin_scope_type,
                scope_id=scope_id,
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
                    scope_type=plugin_scope_type,
                    scope_id=scope_id,
                    config=plugin_config,
                )
                plugin_binding.save()
                self.stdout.write(f"create a new plugin binding: {plugin_binding}, plugin config: {plugin_config}")
