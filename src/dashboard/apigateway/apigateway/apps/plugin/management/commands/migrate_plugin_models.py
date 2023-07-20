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

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from jsonschema import ValidationError as SchemaValidationError
from jsonschema import validate

from apigateway.apps.plugin.constants import PluginTypeEnum
from apigateway.apps.plugin.models import Plugin, PluginBinding, PluginConfig, PluginType
from apigateway.controller.crds.release_data.plugin import PluginConvertorFactory


class Command(BaseCommand):
    """将旧版本插件模型数据迁移到新版本的插件模型，本命令应该保留一两个版本后尽快删除"""

    # 处理特殊插件映射，暂无需增加
    legacy_plugin_type_mappings = {
        PluginTypeEnum.IP_RESTRICTION.value: "bk-ip-restriction",
        PluginTypeEnum.CORS.value: "bk-cors",
        PluginTypeEnum.RATE_LIMIT.value: "bk-rate-limit",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="dry run mode",
        )

    @transaction.atomic
    def handle(self, dry_run: bool, **options):
        for plugin in Plugin.objects.all().order_by("type", "id"):
            self._sync_models(plugin, dry_run)
            self._delete_legacy_models(plugin, dry_run)

        self._patch_legacy_plugin_types(dry_run)

    def _sync_models(self, plugin: Plugin, dry_run: bool):
        bindings = plugin.pluginbinding_set.all()

        print(
            f"migrating legacy plugin: type={plugin.type}, "
            f"id={plugin.pk}, name={plugin.name}, bindings count={bindings.count()}"
        )

        if dry_run:
            return

        plugin_config = self._sync_legacy_plugin_to_plugin_config(plugin)

        for binding in bindings:
            self._update_binding_to_plugin_config(binding, plugin_config)

    def _sync_legacy_plugin_to_plugin_config(self, plugin: Plugin) -> PluginConfig:
        """将旧版 Plugin 同步到新版 PluginConfig"""
        if plugin.target is None:
            plugin_type = self._get_plugin_type_by_plugin(plugin)
            if plugin_type is None:
                raise CommandError(
                    f"Plugin type {plugin.type} used by legacy plugin (id={plugin.pk}) not found, "
                    "you should initial it first."
                )

            plugin_config, _ = PluginConfig.objects.get_or_create(
                api=plugin.api,
                name=f"[迁移] {plugin.name}",
                type=plugin_type,
                defaults={
                    "created_by": plugin.created_by,
                    "updated_by": plugin.updated_by,
                    "description": plugin.description,
                },
            )
            plugin_config.config = plugin._config
            self._validate_plugin_config(plugin_config)
            plugin_config.save(update_fields=["yaml"])

            plugin.target = plugin_config
            plugin.save(update_fields=["target"])

            return plugin_config

        if plugin.target.config == plugin.config:
            return plugin.target

        raise CommandError(
            f"legacy plugin (id={plugin.pk}) config conflict! "
            f"The config of legacy plugin (id={plugin.pk}) is different from the config of it's target plugin_config. "
            f"Please review and fix the data before migrating."
        )

    def _get_plugin_type_by_plugin(self, plugin: Plugin) -> Optional[PluginType]:
        """获取插件类型，如果为旧版插件，返回对应的新版插件类型"""
        code = self.legacy_plugin_type_mappings.get(plugin.type, plugin.type)
        return PluginType.objects.filter(code=code).last()

    def _update_binding_to_plugin_config(self, binding: PluginBinding, plugin_config: PluginConfig):
        if binding.config is None:
            binding.config = plugin_config
            binding.save(update_fields=["config"])
            return

        if binding.config.pk == plugin_config.pk:
            return

        raise CommandError(
            f"Plugin binding (id={binding.pk}) config conflict! "
            f"Binding configures legacy plugin (id={binding.plugin.pk}) and plugin_config (id={binding.config.pk}) at the same time, "
            f"but plugin_config (id={plugin_config.pk}) of legacy plugin target is not the same as plugin_config (id={binding.config.pk}) of binding. "
            f"Please review and remove invalid data before migrating."
        )

    def _delete_legacy_models(self, plugin: Plugin, dry_run: bool):
        if dry_run:
            return

        plugin.delete()

    def _patch_legacy_plugin_types(self, dry_run: bool):
        """修复部分早期版本类型映射问题"""
        for legacy_code, current_code in self.legacy_plugin_type_mappings.items():
            legacy = PluginType.objects.filter(code=legacy_code).first()
            current = PluginType.objects.filter(code=current_code).first()

            if not (legacy and current):
                continue

            configs = PluginConfig.objects.filter(type=legacy)

            print(f"patching {configs.count()} plugin configs from legacy type[{legacy_code}] to type[{current_code}]")

            if not dry_run:
                configs.update(type=current)

    def _validate_plugin_config(self, plugin_config: PluginConfig):
        schema = plugin_config.type and plugin_config.type.schema
        if not schema:
            return

        convertor = PluginConvertorFactory.get_convertor(plugin_config.type.code)
        try:
            validate(convertor.convert(plugin_config), schema=schema.schema)
        except SchemaValidationError as err:
            raise CommandError(
                "plugin config is invalid: gateway_id=%s, name=%s, config=%s, err=%s"
                % (
                    plugin_config.api.id,
                    plugin_config.name,
                    plugin_config.config,
                    err,
                )
            )
