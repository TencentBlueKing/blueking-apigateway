# -*- coding: utf-8 -*-
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

from django.utils.translation import gettext as _
from jsonschema import ValidationError as SchemaValidationError
from jsonschema import validate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.plugin.models import PluginConfig, PluginForm, PluginType
from apigateway.apps.plugin.plugin.checker import PluginConfigYamlChecker
from apigateway.apps.plugin.plugin.convertor import PluginConfigYamlConvertor
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.controller.crds.release_data.plugin import PluginConvertorFactory


class PluginConfigSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    type_id = serializers.PrimaryKeyRelatedField(queryset=PluginType.objects.all())
    type_code = serializers.CharField(source="type.code", read_only=True)
    type_name = serializers.CharField(source="type.name_i18n", read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True)

    class Meta:
        model = PluginConfig
        fields = [
            "id",
            "gateway",
            "name",
            "description",
            "yaml",
            "type_id",
            "updated_by",
            "created_time",
            "updated_time",
            "type_code",
            "type_name",
        ]
        read_only_fields = [
            "id",
            "updated_by",
            "created_time",
            "updated_time",
            "type_code",
            "type_name",
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
        plugin.description_i18n = validated_data["description"]

        try:
            plugin.config = validated_data["yaml"]
            # 转换数据, 校验apisix schema
            schema = plugin.type and plugin.type.schema
            if schema:
                convertor = PluginConvertorFactory.get_convertor(plugin.type.code)
                _data = convertor.convert(plugin)
                validate(_data, schema=schema.schema)
        except SchemaValidationError as err:
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: f"{err.message}, path {list(err.absolute_path)}"}
            )

        checker = PluginConfigYamlChecker(plugin.type.code)
        try:
            checker.check(validated_data["yaml"])
        except Exception as err:
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: f"{err}"})

        plugin.save()
        return plugin

    def create(self, validated_data):
        plugin_type = validated_data["type_id"]
        if not plugin_type.is_public:
            raise ValidationError(_("此插件类型未公开，不能用于启用插件。"))

        return self._update_plugin(
            PluginConfig(gateway=validated_data["gateway"], type=validated_data["type_id"]), validated_data
        )

    def update(self, instance, validated_data):
        if instance.type.code != validated_data["type_id"].code:
            raise ValidationError(_("插件类型不允许更改。"))

        return self._update_plugin(instance, validated_data)


class PluginTypeSLZ(serializers.ModelSerializer):
    name = serializers.CharField(source="name_i18n")

    class Meta:
        model = PluginType
        fields = (
            "id",
            "name",
            "code",
            "is_public",
        )


class PluginFormSLZ(serializers.ModelSerializer):
    type_code = serializers.CharField(source="type.code", read_only=True)
    type_name = serializers.CharField(source="type.name_i18n", read_only=True)
    config = serializers.DictField()

    class Meta:
        model = PluginForm
        fields = (
            "id",
            "language",
            "notes",
            "style",
            "default_value",
            "config",
            "type_id",
            "type_code",
            "type_name",
        )


class PluginConfigFilterSLZ(serializers.Serializer):
    type_code = serializers.ListField(
        child=serializers.CharField(),
        source="type__code__in",
        required=False,
        allow_empty=True,
        help_text="类型代号",
    )
    type = serializers.ListField(
        child=serializers.IntegerField(),
        source="type_id__in",
        required=False,
        allow_empty=True,
        help_text="类型 ID",
    )
