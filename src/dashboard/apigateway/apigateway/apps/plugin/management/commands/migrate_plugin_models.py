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

from apigateway.apps.plugin.models import Plugin, PluginConfig, PluginType, legacy_plugin_type_mappings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """将旧版本插件模型数据迁移到新版本的插件模型，本命令应该保留一两个版本后尽快删除"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="dry run mode",
        )
        parser.add_argument(
            "--keep-legacy",
            action="store_true",
            default=False,
            help="keep the legacy plugin",
        )

    def _sync_models(self, plugin: Plugin, dry_run: bool):
        bindings = plugin.pluginbinding_set.all()

        print(
            f"migrating legacy plugin[{plugin.type}], "
            f"id={plugin.pk}, name={plugin.name}, bindings count={bindings.count()}"
        )

        if dry_run:
            return

        # trigger plugin pre_save hook
        plugin.save()

        for binding in bindings:
            # trigger plugin binding pre_save hook, it should call after plugin save
            binding.save()

    def _patch_legacy_plugin_types(self, dry_run: bool):
        """修复部分早期版本类型映射问题"""

        for legacy_code, current_code in legacy_plugin_type_mappings.items():
            legacy = PluginType.objects.filter(code=legacy_code).first()
            current = PluginType.objects.filter(code=current_code).first()

            if not (legacy and current):
                continue

            configs = PluginConfig.objects.filter(type=legacy)

            print(f"patching {configs.count()} plugin configs from legacy type[{legacy_code}] to type[{current_code}]")

            if not dry_run:
                configs.update(type=current)

    def _delete_legacy_models(self, plugin: Plugin, dry_run: bool):
        plugin.disable_syncing = True
        plugin.delete()

    def handle(self, dry_run: bool, keep_legacy: bool, **options):
        for plugin in Plugin.objects.all().order_by("type", "id"):
            self._sync_models(plugin, dry_run)

            if keep_legacy:
                continue

            self._delete_legacy_models(plugin, dry_run)

        self._patch_legacy_plugin_types(dry_run)
