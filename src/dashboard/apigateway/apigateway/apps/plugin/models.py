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
from typing import Any, Dict, Optional

from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from tencent_apigateway_common.i18n.field import I18nProperty

from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginStyleEnum, PluginTypeEnum
from apigateway.apps.plugin.managers import (
    PluginBindingManager,
    PluginConfigManager,
    PluginFormManager,
    PluginTypeManager,
)
from apigateway.common.mixins.models import ConfigModelMixin, OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway
from apigateway.schema.models import Schema
from apigateway.utils.django import JSONField
from apigateway.utils.yaml import yaml_loads

logger = logging.getLogger(__name__)


class PluginType(models.Model):
    """
    插件类型，表示所有网关可以使用的插件

    后面可能会增加可选的网关字段，表示某个网关启用的自定义插件
    """

    code = models.CharField(max_length=64, help_text="apisix plugin name", db_index=True, unique=True)
    name_i18n = I18nProperty(models.CharField(max_length=128, help_text="dashboard display name"))
    name = name_i18n.default_field()
    name_en = name_i18n.field("en", default=None, blank=True, null=True)
    is_public = models.BooleanField(default=False)
    schema = models.ForeignKey(
        Schema,
        blank=True,
        null=True,
        help_text="plugin config json schema",
        on_delete=models.SET_NULL,
    )

    objects = PluginTypeManager()

    def __str__(self) -> str:
        return f"<PluginType {self.name}({self.pk})>"

    def natural_key(self):
        return (self.code,)

    class Meta:
        db_table = "plugin_type"
        verbose_name = _("插件类型")
        verbose_name_plural = _("插件类型")


class PluginForm(models.Model):
    """
    插件表单配置
    专用于插件配置页面，描述了配置时的表单布局，对应的默认值和注意事项。
    因为是 UI 相关的模型，因此针对不同语言应该提供不同版本的配置。
    对于动态生成的表单，config 字段保存了整体表单结构，default_value 字段为 json
    对于使用 YAML 配置的插件（自定义插件等），config 保持为空，default_value 字段为 YAML，方便添加注释
    """

    language = models.CharField(max_length=16, blank=True)
    type = models.ForeignKey(PluginType, on_delete=models.CASCADE)
    notes = models.TextField(help_text="notes for this plugin", default="", blank=True)
    style = models.CharField(max_length=32, choices=PluginStyleEnum.get_choices(), help_text="表单样式")
    default_value = models.TextField(help_text="default value", default=None, blank=True, null=True)
    config = JSONField(
        default=dict,
        dump_kwargs={"indent": 2, "ensure_ascii": False},
        null=True,
        blank=True,
        help_text="ui schema for config form",
    )

    objects = PluginFormManager()

    class Meta:
        db_table = "plugin_form"
        verbose_name = _("插件表单")
        verbose_name_plural = _("插件表单")
        unique_together = ("language", "type")

    def __str__(self) -> str:
        return f"<PluginForm {self.type.name}({self.pk})>"

    def natural_key(self):
        return (self.language, self.type.code)

    @classmethod
    def fake_object(cls, type: PluginType):
        return cls(
            pk=None,
            language="",
            type=type,
            notes="",
            style=PluginStyleEnum.RAW.value,
            default_value="",
            config={},
        )


class PluginConfig(OperatorModelMixin, TimestampedModelMixin):
    """网关开启的插件及其配置"""

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, db_index=True)
    type = models.ForeignKey(PluginType, null=True, on_delete=models.PROTECT)
    description_i18n = I18nProperty(models.TextField(default=None, blank=True, null=True))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en")
    yaml = models.TextField(blank=True, default=None, null=True)

    objects = PluginConfigManager()

    class Meta:
        db_table = "plugin_config"
        verbose_name = _("插件配置")
        verbose_name_plural = _("插件配置")
        unique_together = ("api", "name", "type")

    @property
    def config(self) -> Dict[str, Any]:
        """
        Return the apisix plugin configuration.
        YAML is a superset of JSON, so we loads the config by yaml directly.
        """

        return yaml_loads(self.yaml)

    @config.setter
    def config(self, yaml_: str):
        self.yaml = yaml_

    def __str__(self) -> str:
        return f"<PluginConfig {self.name}({self.pk})>"


class Plugin(ConfigModelMixin):
    """废弃模型，保留是为了迁移数据"""

    # 是否允许通过信号同步到 PluginConfig
    disable_syncing = False

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, db_index=True)
    description = models.TextField(blank=True, default="")
    type = models.CharField(max_length=32, choices=PluginTypeEnum.get_choices())

    target = models.ForeignKey(PluginConfig, on_delete=models.SET_NULL, null=True)
    schema = models.ForeignKey(Schema, blank=True, null=True, on_delete=models.PROTECT)
    # config from ConfigModelMixin

    def __str__(self):
        return f"<Plugin: {self.api}/{self.name}/{self.type}>"

    class Meta:
        db_table = "plugin"
        verbose_name = _("插件")
        verbose_name_plural = _("插件")
        unique_together = ("api", "name", "type")


class PluginBinding(TimestampedModelMixin, OperatorModelMixin):
    """插件绑定

    同一个插件，只能绑定到一个同类型的对象，比如环境、资源
    """

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    scope_type = models.CharField(
        max_length=32,
        choices=PluginBindingScopeEnum.get_choices(),
        db_index=True,
    )
    scope_id = models.IntegerField(db_index=True)

    # TODO: 删除旧模型后可直接删除下面两个废弃字段
    type = models.CharField(max_length=32, choices=PluginTypeEnum.get_choices(), null=True)
    plugin = models.ForeignKey(Plugin, on_delete=models.SET_NULL, null=True)

    config = models.ForeignKey(PluginConfig, on_delete=models.PROTECT, null=True)

    objects = PluginBindingManager()

    class Meta:
        verbose_name = _("插件绑定")
        verbose_name_plural = _("插件绑定")
        db_table = "plugin_binding"

    def get_config(self):
        if self.config is not None:
            return self.config.config

        return self.plugin.config

    def get_type(self):
        if self.config is not None:
            return self.config.type.code

        return self.plugin.type


# 处理特殊插件映射，暂无需增加
legacy_plugin_type_mappings = {
    PluginTypeEnum.IP_RESTRICTION.value: "bk-ip-restriction",
    PluginTypeEnum.CORS.value: "bk-cors",
    PluginTypeEnum.RATE_LIMIT.value: "bk-rate-limit",
}


def _get_plugin_type_by_plugin_instance(instance: Plugin) -> Optional[PluginType]:
    """迁移模型后可删除"""
    return PluginType.objects.filter(code=legacy_plugin_type_mappings.get(instance.type, instance.type)).last()


@receiver(pre_save, sender=Plugin)
def _sync_plugin_config(sender, instance: Plugin, **kwargs):
    """同步插件配置更新，迁移模型后可删除"""
    if instance.disable_syncing:
        return

    plugin_config = instance.target
    if plugin_config is None:
        plugin_type = _get_plugin_type_by_plugin_instance(instance)
        if plugin_type is None:
            logger.error("plugin type %s not found, you should initial it first", instance.type)
            return

        plugin_config, _ = PluginConfig.objects.get_or_create(
            api_id=instance.api_id,
            name=instance.name,
            type=plugin_type,
            defaults={"created_by": instance.created_by},
        )
        instance.target = plugin_config

    plugin_config.name = instance.name
    plugin_config.description = instance.description
    plugin_config.updated_by = instance.updated_by
    plugin_config.config = instance._config

    plugin_config.save()


@receiver(post_delete, sender=Plugin)
def _delete_plugin_config(sender, instance: Plugin, **kwargs):
    """同步删除关联插件配置，数据迁移时需要先删除这个的钩子，迁移模型后可删除"""
    if instance.disable_syncing:
        return

    if instance.target is None:
        return

    instance.target.delete()


@receiver(pre_save, sender=PluginBinding)
def _sync_plugin_binding(sender, instance: PluginBinding, **kwargs):
    """同步绑定插件配置，迁移模型后可删除"""

    if instance.plugin is None:
        return

    if instance.plugin.disable_syncing:
        return

    if instance.plugin.target is None:
        instance.config = None
    elif PluginConfig.objects.filter(pk=instance.plugin.target.pk).exists():
        instance.config_id = instance.plugin.target.pk
    else:
        instance.config = None
