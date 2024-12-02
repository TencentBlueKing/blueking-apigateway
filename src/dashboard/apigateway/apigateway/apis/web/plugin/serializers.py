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

from typing import Any, Dict

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings

from apigateway.apis.web.plugin.convertor import PluginConfigYamlConvertor
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginConfig, PluginForm, PluginType
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.plugin.validator import PluginConfigYamlValidator


class PluginTypeOutputSLZ(serializers.ModelSerializer):
    name = serializers.CharField(source="name_i18n", help_text="插件类型名称")

    notes = serializers.SerializerMethodField(help_text="插件类型备注")
    related_scope_count = serializers.SerializerMethodField(help_text="插件类型绑定的环境及资源数量")
    is_bound = serializers.SerializerMethodField(help_text="插件类型是否已绑定到当前环境或资源")

    class Meta:
        model = PluginType
        fields = (
            "id",
            "name",
            "code",
            "is_public",
            "notes",
            "related_scope_count",
            "is_bound",
        )

    def get_notes(self, obj):
        notes = self.context.get("plugin_type_notes", {})
        return notes.get(obj.id, "")

    def get_related_scope_count(self, obj):
        related_scope_count = self.context.get("type_related_scope_count", {})
        return related_scope_count.get(obj.id, {"stage": 0, "resource": 0})

    def get_is_bound(self, obj):
        is_bound_map = self.context.get("type_is_bound_to_current_scope", {})
        return is_bound_map.get(obj.id, False)


class PluginTypeQueryInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(required=False, help_text="名称关键字")
    scope_type = serializers.ChoiceField(
        choices=PluginBindingScopeEnum.get_choices(), required=True, help_text="范围类型：stage or resource"
    )
    scope_id = serializers.IntegerField(required=True, help_text="范围 id: stage_id or resource_id")


class PluginFormOutputSLZ(serializers.ModelSerializer):
    type_code = serializers.CharField(source="type.code", read_only=True, help_text="插件类型编码")
    type_name = serializers.CharField(source="type.name_i18n", read_only=True, help_text="插件类型名称")
    config = serializers.DictField(help_text="插件配置")

    class Meta:
        model = PluginForm
        fields = (
            "id",
            "language",
            "notes",
            "example",
            "style",
            "default_value",
            "config",
            "type_id",
            "type_code",
            "type_name",
        )


class PluginConfigBaseSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault(), help_text="网关")
    type_id = serializers.PrimaryKeyRelatedField(queryset=PluginType.objects.all(), help_text="插件类型")
    # description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, help_text="描述")

    class Meta:
        model = PluginConfig
        fields = [
            "id",
            "gateway",
            "name",
            # "description",
            "yaml",
            "type_id",
        ]
        read_only_fields = [
            "id",
        ]
        lookup_field = "id"

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)

        yaml_convertor = PluginConfigYamlConvertor(internal_data["type_id"].code)
        internal_data["yaml"] = yaml_convertor.to_internal_value(internal_data["yaml"])

        return internal_data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        yaml_convertor = PluginConfigYamlConvertor(instance.type.code)
        data["yaml"] = yaml_convertor.to_representation(instance.yaml)

        return data

    def _update_plugin(self, plugin: PluginConfig, validated_data: Dict[str, Any]):
        plugin.name = validated_data["name"]
        # plugin.description_i18n = validated_data["description"]

        validator = PluginConfigYamlValidator()
        try:
            schema = plugin.type and plugin.type.schema and plugin.type.schema.schema
            validator.validate(plugin.type.code, validated_data["yaml"], schema)
        except Exception as err:
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: f"{err}"})

        plugin.config = validated_data["yaml"]
        plugin.save()
        return plugin


class PluginConfigRetrieveUpdateInputSLZ(PluginConfigBaseSLZ):
    def update(self, instance, validated_data):
        if instance.type.code != validated_data["type_id"].code:
            raise ValidationError(_("插件类型不允许更改。"))

        return self._update_plugin(instance, validated_data)


class PluginConfigCreateInputSLZ(PluginConfigBaseSLZ):
    def create(self, validated_data):
        plugin_type = validated_data["type_id"]
        if not plugin_type.is_public:
            raise ValidationError(_("此插件类型未公开，不能用于绑定插件。"))

        if (
            settings.ENABLE_MULTI_TENANT_MODE
            and plugin_type.code == PluginTypeCodeEnum.BK_VERIFIED_USER_EXEMPTED_APPS.value
        ):
            raise ValidationError(_("多租户模式，不支持免用户认证应用白名单插件。"))

        return self._update_plugin(
            PluginConfig(gateway=validated_data["gateway"], type=validated_data["type_id"]), validated_data
        )


class BindingScopeObjectSLZ(serializers.Serializer):
    id = serializers.IntegerField(help_text="id")
    name = serializers.CharField(help_text="名称")


class PluginBindingListOutputSLZ(serializers.Serializer):
    stages = serializers.ListField(child=BindingScopeObjectSLZ(), help_text="环境列表")
    resources = serializers.ListField(child=BindingScopeObjectSLZ(), help_text="资源列表")


class ScopePluginConfigListOutputSLZ(serializers.Serializer):
    code = serializers.CharField(help_text="插件类型编码")
    name = serializers.CharField(help_text="插件类型名称")
    config = serializers.DictField(help_text="插件配置")
    config_id = serializers.IntegerField(help_text="插件配置 id")
    related_scope_count = serializers.SerializerMethodField(help_text="插件类型绑定的环境及资源数量")

    def get_related_scope_count(self, obj):
        related_scope_count = self.context.get("type_related_scope_count", {})
        return related_scope_count.get(obj["code"], {"stage": 0, "resource": 0})
