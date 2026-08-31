#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from typing import Any, ClassVar, Dict, List

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.plugin.constants import (
    PluginBindingScopeEnum,
    PluginBindingSourceEnum,
    PluginTypeScopeEnum,
)
from apigateway.apps.plugin.managers import PluginBindingManager, PluginTypeManager
from apigateway.common.i18n.field import I18nProperty
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway
from apigateway.schema.models import Schema
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
    description_i18n = I18nProperty(models.TextField(default="", blank=True, help_text="plugin type description"))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en", default=None, blank=True, null=True)
    is_public = models.BooleanField(default=False)
    schema = models.ForeignKey(
        Schema,
        blank=True,
        null=True,
        help_text="plugin config json schema",
        on_delete=models.SET_NULL,
    )
    # stage/resource/stage_and_resource
    scope = models.CharField(
        max_length=32,
        choices=PluginTypeScopeEnum.get_choices(),
        default=PluginTypeScopeEnum.STAGE_AND_RESOURCE.value,
    )
    priority = models.IntegerField("优先级", default=-1, blank=True, null=True)
    # there would not be so many tags
    _tags = models.CharField(db_column="tags", max_length=256, default="", blank=True, null=True)

    objects: ClassVar[PluginTypeManager] = PluginTypeManager()

    def __str__(self) -> str:
        return f"<PluginType {self.pk}/{self.name}>"

    def natural_key(self):
        return (self.code,)

    @property
    def tags(self) -> List[str]:
        return self._tags.split(",") if self._tags else []

    @tags.setter
    def tags(self, tags: List[str]):
        _tags = [tag.strip() for tag in tags if tag.strip()]
        self._tags = ",".join(_tags)

    class Meta:
        db_table = "plugin_type"
        verbose_name = _("插件类型")
        verbose_name_plural = _("插件类型")


class PluginConfig(OperatorModelMixin, TimestampedModelMixin):
    """网关开启的插件及其配置"""

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    name = models.CharField(max_length=64, blank=True, null=True)
    type = models.ForeignKey(PluginType, null=True, on_delete=models.PROTECT)
    description_i18n = I18nProperty(models.TextField(default=None, blank=True, null=True))
    description = description_i18n.default_field()
    description_en = description_i18n.field("en")
    yaml = models.TextField(blank=True, default=None, null=True)

    class Meta:
        db_table = "plugin_config"
        verbose_name = _("插件配置")
        verbose_name_plural = _("插件配置")

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
        return f"<PluginConfig {self.pk}/{self.type.code}>"


class PluginBinding(TimestampedModelMixin, OperatorModelMixin):
    """插件绑定

    同一个插件，只能绑定到一个同类型的对象，比如环境、资源
    """

    gateway = models.ForeignKey(Gateway, db_column="api_id", on_delete=models.CASCADE)
    scope_type = models.CharField(
        max_length=32,
        choices=PluginBindingScopeEnum.get_choices(),
    )
    scope_id = models.IntegerField()
    config = models.ForeignKey(PluginConfig, on_delete=models.PROTECT, null=True)
    source = models.CharField(
        max_length=32,
        choices=PluginBindingSourceEnum.get_choices(),
        default=PluginBindingSourceEnum.USER_CREATE.value,
        null=True,
    )

    objects: ClassVar[PluginBindingManager] = PluginBindingManager()

    class Meta:
        verbose_name = _("插件绑定")
        verbose_name_plural = _("插件绑定")
        db_table = "plugin_binding"
        unique_together = ("scope_id", "scope_type", "config")

    def get_config(self):
        return self.config.config

    def get_type(self):
        return self.config.type.code

    def snapshot(self):
        return {
            "id": self.id,
            "type": self.get_type(),
            "name": self.config.type.name,
            "config": self.get_config(),
        }

    def __str__(self) -> str:
        return f"<PluginBinding {self.pk}/{self.scope_type}/{self.scope_id}/{self.config.type}>"
