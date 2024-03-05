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

from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginType
from apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Context, Proxy, Stage
from apigateway.utils import yaml

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """检查stage/resource的proxy请求头配置迁移成bk-header-rewrite插件配置是否迁移正确，1.14会移除"""

    def handle(self, *args, **options):
        self.check_stage_header_rewrite_migration()
        self.check_resource_header_rewrite_migration()

    def check_stage_header_rewrite_migration(self):
        stages = Stage.objects.all()
        self.stdout.write("Checking header rewrite plugin migration for stages")
        # 统计check结果
        total_stages = stages.count()
        failed_stages = 0
        for stage in stages:
            context = Context.objects.filter(
                scope_type=ContextScopeTypeEnum.STAGE.value,
                scope_id=stage.id,
                type=ContextTypeEnum.STAGE_PROXY_HTTP.value,
            ).first()

            check_no_binding = False

            if context and "transform_headers" in context.config:
                expected_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(
                    context.config.get("transform_headers")
                )
                if not expected_config:
                    check_no_binding = True
                if expected_config and not self.is_plugin_config_migrated(
                    stage.gateway_id, PluginBindingScopeEnum.STAGE.value, stage.id, expected_config
                ):
                    failed_stages = +1
                    self.stdout.write(f"{expected_config}")
                    self.stdout.write(
                        f"Gateway {stage.gateway.name} Stage {stage.id}"
                        f" header rewrite plugin config migration check failed"
                    )
            else:
                check_no_binding = True

            if check_no_binding:
                # 不应该存在插件绑定
                plugin_binding = self._get_plugin_binding(
                    stage.gateway_id, PluginBindingScopeEnum.STAGE.value, stage.id
                )
                if plugin_binding:
                    failed_stages = +1
                    self.stdout.write(
                        f"Gateway {stage.gateway.name} Stage {stage.id}"
                        f" has plugin biding[{plugin_binding.config.yaml}] config for no transform_headers "
                    )

        self.stdout.write(
            f"Finished checking header rewrite plugin migration for stages: "
            f"{total_stages} checked, {failed_stages} failed"
        )

    def check_resource_header_rewrite_migration(self):
        proxies = Proxy.objects.prefetch_related("resource").all()
        self.stdout.write("Checking header rewrite plugin migration for resource")
        # 统计check结果
        total_resources = proxies.count()
        failed_resources = 0
        for proxy in proxies:
            check_no_binding = False

            if "transform_headers" in proxy.config:
                expected_config = HeaderRewriteConvertor.transform_headers_to_plugin_config(
                    proxy.config.get("transform_headers")
                )

                if not expected_config:
                    check_no_binding = True

                if expected_config and not self.is_plugin_config_migrated(
                    proxy.resource.gateway_id,
                    PluginBindingScopeEnum.RESOURCE.value,
                    proxy.resource.id,
                    expected_config,
                ):
                    failed_resources = +1
                    self.stdout.write(
                        f"Resource  {proxy.resource.id}" f" header rewrite plugin config migration check failed"
                    )
            else:
                check_no_binding = True

            if check_no_binding:
                # 不应该存在插件绑定
                plugin_binding = self._get_plugin_binding(
                    proxy.resource.gateway_id, PluginBindingScopeEnum.RESOURCE.value, proxy.resource.id
                )
                if plugin_binding:
                    failed_resources = +1
                    self.stdout.write(
                        f"Resource {proxy.resource.id}"
                        f" has plugin biding[{plugin_binding.config.yaml}] config for no transform_headers "
                    )

        self.stdout.write(
            f"Finished checking header rewrite plugin migration for resources: "
            f" {total_resources} checked, {failed_resources} failed"
        )

    def _get_plugin_binding(self, gateway_id, scope_type, scope_id):
        # 获取插件类型对象
        plugin_type = PluginType.objects.get(code=PluginTypeCodeEnum.BK_HEADER_REWRITE.value)

        # 获取与scope相关的插件绑定对象
        return (
            PluginBinding.objects.filter(
                gateway_id=gateway_id,
                scope_type=scope_type,
                scope_id=scope_id,
                config__type=plugin_type,
            )
            .select_related("config")
            .first()
        )

    def is_plugin_config_migrated(self, gateway_id, scope_type, scope_id, expected_config):
        """
        Check if the plugin configuration has been migrated correctly.
        """
        try:
            plugin_binding = self._get_plugin_binding(gateway_id, scope_type, scope_id)
            # 如果没有找到插件绑定，表示迁移失败
            if not plugin_binding:
                self.stdout.write(
                    f"Check gateway[{gateway_id}] header rewrite plugin [{scope_type}] failed."
                    f"\nexpected:{expected_config}"
                    f"\nactual: has no plugin_binding"
                )
                return False

            # 获取实际的插件配置
            actual_plugin_config_yaml = plugin_binding.config.yaml
            except_plugin_config_yaml = yaml.yaml_dumps(expected_config)

            # 比较预期配置与实际配置是否一致
            no_diff = actual_plugin_config_yaml == except_plugin_config_yaml
            if not no_diff:
                self.stdout.write(
                    f"Check gateway[{gateway_id}] header rewrite plugin [{scope_type}] failed."
                    f"\nexpected:{except_plugin_config_yaml}"
                    f"\nactual:{actual_plugin_config_yaml}"
                )
            return no_diff

        except PluginType.DoesNotExist:
            # 如果插件类型不存在，记录错误并返回 False
            self.stdout.write(
                f"Gateway[{gateway_id}] PluginType for code {PluginTypeCodeEnum.BK_HEADER_REWRITE.value} does not exist."
            )
            return False
        except Exception as e:
            # 如果发生其他异常，记录错误并返回 False
            self.stdout.write(f"An error occurred while checking gateway[{gateway_id}]plugin config migration: {e}")
            return False
