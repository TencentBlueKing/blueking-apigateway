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
from django.conf import settings
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.apps.gateway.utils import get_gateway_feature_flags
from apigateway.biz.gateway_app_binding import GatewayAppBindingHandler
from apigateway.common.contexts import APIAuthContext, APIFeatureFlagContext
from apigateway.core.constants import (
    API_NAME_PATTERN,
    APP_CODE_PATTERN,
    APIHostingTypeEnum,
    APITypeEnum,
    UserAuthTypeEnum,
)
from apigateway.core.models import Gateway
from apigateway.core.validators import NameValidator, ReservedAPINameValidator
from apigateway.utils.crypto import calculate_fingerprint


class GatewayCreateSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(
        API_NAME_PATTERN,
        label="网关名称",
        max_length=64,
        validators=[ReservedAPINameValidator(), NameValidator()],
    )
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    developers = serializers.ListField(child=serializers.CharField(), allow_empty=True, default=list)
    user_auth_type = serializers.ChoiceField(
        choices=UserAuthTypeEnum.choices(),
        default=settings.DEFAULT_USER_AUTH_TYPE,
    )
    hosting_type = serializers.ChoiceField(
        choices=APIHostingTypeEnum.get_choices(),
        default=settings.DEFAULT_GATEWAY_HOSTING_TYPE,
    )
    bk_app_codes = serializers.ListField(
        child=serializers.RegexField(APP_CODE_PATTERN),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Gateway
        fields = (
            "name",
            "description",
            "maintainers",
            "developers",
            "status",
            "is_public",
            "user_auth_type",
            "hosting_type",
            "bk_app_codes",
        )
        no_write_fields = ["user_auth_type", "bk_app_codes"]
        lookup_field = "id"

        # 使用 UniqueTogetherValidator，方便错误提示信息统一处理
        # 使用 UniqueValidator，错误提示中包含了字段名："参数校验失败: Name: 网关名称已经存在"
        validators = [
            UniqueTogetherValidator(
                queryset=Gateway.objects.all(),
                fields=["name"],
                message=gettext_lazy("网关名称已经存在。"),
            )
        ]

    def _add_creator_to_maintainers(self, data):
        # 创建者无网关权限，仅作为标记，维护人员有权限
        # 因此，如果创建者不在维护人中，默认添加到维护人中
        username = self.context["request"].user.username
        if username not in data["maintainers"]:
            data["maintainers"].append(username)
        return data

    def to_internal_value(self, data):
        data.setdefault("hosting_type", APIHostingTypeEnum(settings.DEFAULT_GATEWAY_HOSTING_TYPE).value)
        data.setdefault("user_auth_type", UserAuthTypeEnum(settings.DEFAULT_USER_AUTH_TYPE).value)
        data = super().to_internal_value(data)
        return self._add_creator_to_maintainers(data)

    def create(self, validated_data):
        for field in self.Meta.no_write_fields:
            validated_data.pop(field, None)
        return super().create(validated_data)


class GatewayUpdateSLZ(serializers.ModelSerializer):
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    developers = serializers.ListField(child=serializers.CharField(), allow_empty=True, default=list)
    bk_app_codes = serializers.ListField(
        child=serializers.RegexField(APP_CODE_PATTERN),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Gateway
        fields = (
            "description",
            "maintainers",
            "developers",
            "is_public",
            "bk_app_codes",
        )
        lookup_field = "id"


class GatewayUpdateStatusSLZ(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = ("status",)
        lookup_field = "id"


class GatewayDetailSLZ(serializers.ModelSerializer):
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    developers = serializers.ListField(child=serializers.CharField(), allow_empty=True, default=list)
    public_key = serializers.CharField(label="网关公钥", source="jwt.public_key")
    user_auth_type = serializers.SerializerMethodField()
    allow_update_api_auth = serializers.SerializerMethodField()
    domain = serializers.CharField(label="访问域名", read_only=True)
    docs_url = serializers.CharField(label="文档地址", read_only=True)
    public_key_fingerprint = serializers.SerializerMethodField()
    feature_flags = serializers.SerializerMethodField()
    is_official = serializers.SerializerMethodField()
    description = SerializerTranslatedField(
        default_field="description_i18n",
        allow_blank=True,
        allow_null=True,
        max_length=512,
        required=False,
    )
    bk_app_codes = serializers.SerializerMethodField()

    class Meta:
        model = Gateway
        fields = (
            "id",
            "name",
            "description",
            "description_en",
            "maintainers",
            "developers",
            "status",
            "is_public",
            "hosting_type",
            "created_by",
            "created_time",
            "public_key",
            "user_auth_type",
            "allow_update_api_auth",
            "domain",
            "docs_url",
            "public_key_fingerprint",
            "feature_flags",
            "is_official",
            "bk_app_codes",
        )
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        read_only_fields = [
            "created_by",
        ]
        lookup_field = "id"

    def get_public_key_fingerprint(self, obj):
        return calculate_fingerprint(obj.jwt.public_key)

    def get_user_auth_type(self, obj):
        return self.context["auth_config"]["user_auth_type"]

    def get_allow_update_api_auth(self, obj):
        return self.context["auth_config"].get("allow_update_api_auth", False)

    def get_feature_flags(self, obj):
        feature_flags = get_gateway_feature_flags(APIHostingTypeEnum(obj.hosting_type))
        feature_flags.update(self.context["feature_flags"])
        return feature_flags

    def get_is_official(self, obj):
        api_type = self.context["auth_config"]["api_type"]
        return APITypeEnum.is_official(api_type)

    def get_bk_app_codes(self, obj):
        return self.context.get("bk_app_codes", [])

    @classmethod
    def from_instance(cls, instance: Gateway):
        # 根据网关实例创建，简化调用
        return cls(
            instance,
            context={
                "auth_config": APIAuthContext().get_config(instance.pk),
                "feature_flags": APIFeatureFlagContext().get_config(instance.pk, {}),
                "bk_app_codes": GatewayAppBindingHandler.get_bound_app_codes(instance),
            },
        )


class GatewayQuerySLZ(serializers.Serializer):
    name = serializers.CharField(label="网关名称", allow_blank=True, required=False)


class GatewayListSLZ(serializers.ModelSerializer):
    resource_count = serializers.SerializerMethodField()
    stages = serializers.SerializerMethodField()
    is_official = serializers.SerializerMethodField()
    description = SerializerTranslatedField(
        default_field="description_i18n",
        allow_blank=True,
        allow_null=True,
        max_length=512,
        required=False,
    )
    hosting_type = serializers.SerializerMethodField()

    class Meta:
        model = Gateway
        fields = (
            "id",
            "name",
            "description",
            "description_en",
            "status",
            "is_public",
            "hosting_type",
            "created_by",
            "stages",
            "resource_count",
            "is_official",
            "created_time",
            "updated_time",
        )
        extra_kwargs = {
            "description_en": {
                "required": False,
            },
            "created_time": {
                "read_only": True,
            },
            "updated_time": {
                "read_only": True,
            },
        }

    def get_resource_count(self, obj):
        return self.context["api_resource_count"].get(obj.id, 0)

    def get_stages(self, obj):
        return self.context["api_stages"].get(obj.id, [])

    def get_is_official(self, obj):
        if obj.id not in self.context["api_auth_contexts"]:
            return False

        api_type = self.context["api_auth_contexts"][obj.id]["api_type"]
        return APITypeEnum.is_official(api_type)

    def get_hosting_type(self, obj):
        micro_gateway_count = self.context["micro_gateway_count"].get(obj.id, 0)
        if micro_gateway_count > 0:
            return APIHostingTypeEnum.MICRO.value
        return APIHostingTypeEnum.DEFAULT.value
