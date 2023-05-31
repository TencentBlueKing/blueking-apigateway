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
from typing import List, Optional

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.biz.gateway import GatewayHandler
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.core.constants import (
    API_NAME_PATTERN,
    APIHostingTypeEnum,
    APIStatusEnum,
    APITypeEnum,
    UserAuthTypeEnum,
)
from apigateway.core.models import Gateway, ReleaseHistory
from apigateway.core.validators import BKAppCodeListValidator


class GatewayQueryV1SLZ(serializers.Serializer):
    user_auth_type = serializers.ChoiceField(choices=UserAuthTypeEnum.choices(), allow_blank=True, required=False)
    query = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)


class GatewayV1SLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True)
    description_en = serializers.CharField(required=False, write_only=True)
    maintainers = serializers.SerializerMethodField()
    api_type = serializers.SerializerMethodField()
    user_auth_type = serializers.SerializerMethodField()

    def get_api_type(self, obj):
        return self.context["api_auth_contexts"][obj.id]["api_type"]

    def get_user_auth_type(self, obj):
        return self.context["api_auth_contexts"][obj.id]["user_auth_type"]

    def get_maintainers(self, obj):
        recent_releasers = ReleaseHistory.objects.get_recent_releasers(obj.id)
        return list(set(recent_releasers) & set(obj.maintainers)) or obj.maintainers


class GatewayV1DetailSLZ(GatewayV1SLZ):
    api_type = None
    user_auth_type = None


class UserConfigSLZ(serializers.Serializer):
    """
    目前仅支持开源版的用户配置字段，如果需要支持其他版本，可直接添加对应字段
    """

    from_bk_token = serializers.BooleanField(required=False)
    from_username = serializers.BooleanField(required=False)


class GatewaySyncSLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    name = serializers.RegexField(API_NAME_PATTERN, label="网关名称", max_length=64)
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    status = serializers.ChoiceField(choices=APIStatusEnum.choices(), default=APIStatusEnum.ACTIVE.value)
    # 只允许指定为普通网关或官方网关，不能指定为超级官方网关，超级官方网关会传递敏感参数到后端接口
    api_type = serializers.ChoiceField(
        choices=[APITypeEnum.OFFICIAL_API.value, APITypeEnum.CLOUDS_API.value], required=False
    )
    user_auth_type = serializers.ChoiceField(
        choices=UserAuthTypeEnum.choices(),
        default=settings.DEFAULT_USER_AUTH_TYPE,
    )
    user_config = UserConfigSLZ(required=False)
    hosting_type = serializers.IntegerField(
        required=False,
        default=settings.DEFAULT_GATEWAY_HOSTING_TYPE,
    )

    class Meta:
        model = Gateway
        fields = [
            "name",
            "description",
            "description_en",
            "maintainers",
            "status",
            "is_public",
            "api_type",
            "user_auth_type",
            "user_config",
            "hosting_type",
        ]
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }
        non_model_fields = ["user_auth_type", "user_config"]

    def to_internal_value(self, data):
        data.setdefault("maintainers", [])
        data.setdefault("hosting_type", APIHostingTypeEnum(settings.DEFAULT_GATEWAY_HOSTING_TYPE).value)
        data.setdefault("user_auth_type", UserAuthTypeEnum(settings.DEFAULT_USER_AUTH_TYPE).value)
        return super().to_internal_value(data)

    def validate(self, data):
        self._validate_api_type(data["name"], data.get("api_type"))
        return data

    def create(self, validated_data):
        # 1. save api
        api_type = validated_data.pop("api_type", None)
        instance = super().create(validated_data)

        # 2. save related data
        GatewayHandler().save_related_data(
            gateway=instance,
            user_auth_type=validated_data["user_auth_type"],
            username=validated_data.get("created_by", ""),
            related_app_code=self.context.get("bk_app_code"),
            user_config=validated_data.get("user_config"),
            unfiltered_sensitive_keys=self._get_api_unfiltered_sensitive_keys(instance.name),
            api_type=None if api_type is None else APITypeEnum(api_type),
        )

        # 3. record audit log
        GatewayHandler().add_create_audit_log(instance, validated_data.get("created_by", ""))

        return instance

    def update(self, instance, validated_data):
        # 1. 更新网关数据
        validated_data.pop("name", None)
        validated_data.pop("status", None)
        validated_data.pop("created_by", None)

        api_type = validated_data.pop("api_type", None)
        validated_data["maintainers"] = sorted(set(validated_data["maintainers"] + instance.maintainers))

        instance = super().update(instance, validated_data)

        # 2. 更新网关配置
        GatewayHandler().save_auth_config(
            instance.id,
            user_auth_type=validated_data["user_auth_type"],
            user_conf=validated_data.get("user_config"),
            unfiltered_sensitive_keys=self._get_api_unfiltered_sensitive_keys(instance.name),
            api_type=None if api_type is None else APITypeEnum(api_type),
        )

        # 3. 记录操作日志
        GatewayHandler().add_update_audit_log(instance, validated_data.get("updated_by", ""))

        return instance

    def _get_api_unfiltered_sensitive_keys(self, gateway_name: str) -> Optional[List[str]]:
        api_auth_configs = getattr(settings, "SPECIAL_API_AUTH_CONFIGS", None) or {}
        if gateway_name not in api_auth_configs:
            return None

        return api_auth_configs[gateway_name].get("unfiltered_sensitive_keys")

    def _validate_api_type(self, name: str, api_type: Optional[int]):
        if not (api_type is not None and api_type != APITypeEnum.CLOUDS_API.value):
            return

        for prefix in settings.OFFICIAL_GATEWAY_NAME_PREFIXES:
            if not name.startswith(prefix):
                raise serializers.ValidationError(
                    {
                        "api_type": _("api_type 为 {api_type} 时，网关名 name 需以 {prefix} 开头。").format(
                            api_type=api_type, prefix=prefix
                        )
                    }
                )


class AddRelatedAppsSLZ(serializers.Serializer):
    target_app_codes = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=True,
        max_length=10,
        validators=[BKAppCodeListValidator()],
    )


class GatewayUpdateStatusSLZ(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=APIStatusEnum.choices())

    class Meta:
        model = Gateway
        fields = [
            "status",
        ]
