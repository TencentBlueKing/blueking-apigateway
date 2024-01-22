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
from typing import Optional

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.apis.web.gateway.constants import GATEWAY_NAME_PATTERN
from apigateway.biz.validators import BKAppCodeListValidator
from apigateway.common.django.validators import NameValidator
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.core.constants import (
    GatewayStatusEnum,
    GatewayTypeEnum,
)
from apigateway.core.models import Gateway


class GatewayListV1InputSLZ(serializers.Serializer):
    user_auth_type = serializers.ChoiceField(choices=UserAuthTypeEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)


class GatewayListV1OutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    api_type = serializers.SerializerMethodField()
    user_auth_type = serializers.SerializerMethodField()

    def get_api_type(self, obj):
        return self.context["gateway_auth_configs"][obj.id].gateway_type

    def get_user_auth_type(self, obj):
        return self.context["gateway_auth_configs"][obj.id].user_auth_type

    def get_maintainers(self, obj):
        # TODO: 网关对外的维护者（助手号），便于用户咨询网关问题，需要单独使用一个新字段去维护？
        return obj.maintainers


class GatewayRetrieveV1OutputSLZ(GatewayListV1OutputSLZ):
    api_type = None
    user_auth_type = None


class UserConfigSLZ(serializers.Serializer):
    """
    目前仅支持开源版的用户配置字段，如果需要支持其他版本，可直接添加对应字段
    """

    from_bk_token = serializers.BooleanField(required=False)
    from_username = serializers.BooleanField(required=False)


class GatewaySyncInputSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(
        GATEWAY_NAME_PATTERN,
        label="网关名称",
        max_length=64,
        validators=[NameValidator()],
    )
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True, required=False)
    status = serializers.ChoiceField(choices=GatewayStatusEnum.get_choices(), default=GatewayStatusEnum.ACTIVE.value)
    # 只允许指定为普通网关或官方网关，不能指定为超级官方网关，超级官方网关会传递敏感参数到后端接口
    api_type = serializers.ChoiceField(
        choices=[GatewayTypeEnum.OFFICIAL_API.value, GatewayTypeEnum.CLOUDS_API.value], required=False
    )
    user_config = UserConfigSLZ(required=False)
    allow_auth_from_params = serializers.BooleanField(default=True)
    allow_delete_sensitive_params = serializers.BooleanField(default=True)

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
            "user_config",
            "allow_auth_from_params",
            "allow_delete_sensitive_params",
        ]
        extra_kwargs = {
            "description_en": {
                "required": False,
            }
        }

    def validate(self, data):
        self._validate_name(data["name"], data.get("api_type"))

        data["gateway_type"] = data.pop("api_type", None)

        return data

    def _validate_name(self, name: str, api_type: Optional[int]):
        if api_type is None or api_type == GatewayTypeEnum.CLOUDS_API.value:
            return

        for prefix in settings.OFFICIAL_GATEWAY_NAME_PREFIXES:
            if name.startswith(prefix):
                return

        raise serializers.ValidationError(
            {
                "name": _("api_type 为 {api_type} 时，网关名 name 需以 {prefix} 开头。").format(
                    api_type=api_type, prefix=", ".join(settings.OFFICIAL_GATEWAY_NAME_PREFIXES)
                )
            }
        )


class GatewayUpdateStatusInputSLZ(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=GatewayStatusEnum.get_choices())

    class Meta:
        model = Gateway
        fields = [
            "status",
        ]
        ref_name = "apigateway.apis.open.gateway.serializers.GatewayUpdateStatusInputSLZ"


class GatewayRelatedAppsAddInputSLZ(serializers.Serializer):
    target_app_codes = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=True,
        max_length=10,
        validators=[BKAppCodeListValidator()],
    )
