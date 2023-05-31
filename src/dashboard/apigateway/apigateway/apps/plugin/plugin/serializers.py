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
from typing import Any, ClassVar, Dict

from attr import define
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from jsonschema import ValidationError as SchemaValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.plugin.models import PluginConfig, PluginForm, PluginType
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.utils.yaml import yaml_dumps, yaml_loads


class RateLimitYamlConvertor:
    """
    前端传入的数据样例
    rates:
      default:
        period: 1
        tokens: 1
      specials:
        - period: 1
          bk_app_code: test
          tokens: 10

    存储的数据样例
    rates:
      __default:
        - period: 1
          tokens: 1
      test:
        - period: 1
          tokens: 10
    """

    def to_internal_value(self, data):
        loaded_data = yaml_loads(data)

        result = {"rates": {}}
        # 特殊应用频率
        for item in loaded_data["rates"].get("specials", []):
            bk_app_code = item["bk_app_code"]
            if bk_app_code in result["rates"]:
                raise ValidationError({"bk_app_code": _(f"蓝鲸应用ID重复: {bk_app_code}").format(bk_app_code=bk_app_code)})

            result["rates"][bk_app_code] = [{"period": item["period"], "tokens": item["tokens"]}]

        # 蓝鲸应用默认频率
        default_rate = loaded_data["rates"]["default"]
        result["rates"]["__default"] = [{"period": default_rate["period"], "tokens": default_rate["tokens"]}]

        return yaml_dumps(result)

    def to_representation(self, value):
        loaded_data = yaml_loads(value)

        result = {"rates": {"default": {}, "specials": []}}
        for bk_app_code, rates in loaded_data["rates"].items():
            # 目前仅支持单个频率配置
            rate = rates[0]

            if bk_app_code == "__default":
                result["rates"]["default"] = {"period": rate["period"], "tokens": rate["tokens"]}
            else:
                result["rates"]["specials"].append(
                    {
                        "period": rate["period"],
                        "tokens": rate["tokens"],
                        "bk_app_code": bk_app_code,
                    }
                )

        return yaml_dumps(result)


@define(slots=False)
class PluginConfigYamlConvertor:
    type_code: str
    type_code_to_convertor: ClassVar[Dict[str, Any]] = {
        "bk-rate-limit": RateLimitYamlConvertor(),
    }

    def to_internal_value(self, data):
        convertor = self.type_code_to_convertor.get(self.type_code)
        if not convertor:
            return data
        return convertor.to_internal_value(data)

    def to_representation(self, value):
        convertor = self.type_code_to_convertor.get(self.type_code)
        if not convertor:
            return value
        return convertor.to_representation(value)


class PluginConfigSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    type_id = serializers.PrimaryKeyRelatedField(queryset=PluginType.objects.all())
    type_code = serializers.CharField(source="type.code", read_only=True)
    type_name = serializers.CharField(source="type.name_i18n", read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True)

    class Meta:
        model = PluginConfig
        fields = [
            "id",
            "api",
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
        validators = [
            UniqueTogetherValidator(
                queryset=PluginConfig.objects.all(),
                fields=("api", "name", "type_id"),
                message=gettext_lazy("网关下插件名称+类型已经存在，请检查。"),
            )
        ]

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)

        # TODO: bk-rate-limit 前端表单插件生成数据的格式，暂与实际需要不一致，待升级后，可删除此转换
        yaml_convertor = PluginConfigYamlConvertor(internal_data["type_id"].code)
        internal_data["yaml"] = yaml_convertor.to_internal_value(internal_data["yaml"])

        return internal_data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # TODO: bk-rate-limit 前端表单插件生成数据的格式，暂与实际需要不一致，待升级后，可删除此转换
        yaml_convertor = PluginConfigYamlConvertor(instance.type.code)
        data["yaml"] = yaml_convertor.to_representation(instance.yaml)

        return data

    def _update_plugin(self, plugin: PluginConfig, validated_data: Dict[str, Any]):
        plugin.name = validated_data["name"]
        plugin.description_i18n = validated_data["description"]

        try:
            plugin.config = validated_data["yaml"]
        except SchemaValidationError as err:
            raise ValidationError(f"{err.message}, path {list(err.absolute_path)}")

        plugin.save()
        return plugin

    def create(self, validated_data):
        plugin_type = validated_data["type_id"]
        if not plugin_type.is_public:
            raise ValidationError(_("此插件类型未公开，不能用于启用插件。"))

        return self._update_plugin(
            PluginConfig(api=validated_data["api"], type=validated_data["type_id"]), validated_data
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
