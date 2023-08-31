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


import logging

from django.core.management.base import BaseCommand

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding
from apigateway.apps.access_strategy.utils import parse_to_plugin_config
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """将访问策略 access_strategy 迁移成 pluginConfig"""

    def handle(self, *args, **options):
        for binding in AccessStrategyBinding.objects.all():
            # 不需要转换的在这里过滤
            if binding.type == AccessStrategyTypeEnum.CIRCUIT_BREAKER.value:
                logger.info("skip binding: %s, the strategy type is CIRCUIT_BREAKER", binding)

                continue

            scope_type = binding.scope_type
            scope_id = binding.scope_id
            strategy = binding.AccessStrategy
            gateway = strategy.api

            plugin_config = parse_to_plugin_config(strategy)
            if not plugin_config:
                logger.info("skip binding: %s, the strategy %d config is empty %s", binding, strategy, strategy.config)

                continue

            plugin_config.save()

            plugin_scope_type = (
                PluginBindingScopeEnum.STAGE.value
                if scope_type == AccessStrategyTypeEnum.STAGE.value
                else PluginBindingScopeEnum.RESOURCE.value
            )
            # FIXME: 绑定前需要检测，如果已经有了，跳过
            plugin_binding = PluginBinding(
                gateway=gateway,
                scope_type=plugin_scope_type,
                scope_id=scope_id,
                config=plugin_config,
            )
            plugin_binding.save()
