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
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from tencent_apigateway_common.i18n.field import SerializerTranslatedField

from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import (
    GATEWAY_NAME_PATTERN,
    GatewayStatusEnum,
    GatewayTypeEnum,
)
from apigateway.core.models import Gateway
from apigateway.core.validators import ReservedGatewayNameValidator
from apigateway.utils.crypto import calculate_fingerprint


class GatewayListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(allow_blank=True, default_field="description_i18n", read_only=True)
    status = serializers.ChoiceField(choices=GatewayStatusEnum.get_choices(), read_only=True)
    is_public = serializers.BooleanField(read_only=True)
    created_by = serializers.CharField(allow_blank=True, allow_null=True, read_only=True)
    created_time = serializers.DateTimeField(allow_null=True, read_only=True)
    updated_time = serializers.DateTimeField(allow_null=True, read_only=True)
    is_official = serializers.SerializerMethodField()
    resource_count = serializers.SerializerMethodField()
    stages = serializers.SerializerMethodField()

    def get_is_official(self, obj):
        if obj.id not in self.context["gateway_auth_configs"]:
            return False

        return GatewayTypeEnum.is_official(self.context["gateway_auth_configs"][obj.id].gateway_type)

    def get_resource_count(self, obj):
        return self.context["resource_count"].get(obj.id, 0)

    def get_stages(self, obj):
        return self.context["stages"].get(obj.id, [])


class GatewayCreateInputSLZ(serializers.ModelSerializer):
    name = serializers.RegexField(
        GATEWAY_NAME_PATTERN,
        label="网关名称",
        max_length=64,
        validators=[ReservedGatewayNameValidator()],
    )
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = Gateway
        fields = (
            "name",
            "description",
            "maintainers",
            "is_public",
        )
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
        if self.context["username"] not in data["maintainers"]:
            data["maintainers"].append(self.context["username"])
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return self._add_creator_to_maintainers(data)


class GatewayRetrieveOutputSLZ(serializers.ModelSerializer):
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    public_key = serializers.CharField(label="网关公钥", source="jwt.public_key")
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, allow_null=True)
    is_official = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    docs_url = serializers.SerializerMethodField()
    public_key_fingerprint = serializers.SerializerMethodField()
    feature_flags = serializers.SerializerMethodField()
    allow_update_gateway_auth = serializers.SerializerMethodField()

    class Meta:
        model = Gateway
        fields = (
            "id",
            "name",
            "description",
            "maintainers",
            "status",
            "is_public",
            "created_by",
            "created_time",
            "public_key",
            "is_official",
            "allow_update_gateway_auth",
            "domain",
            "docs_url",
            "public_key_fingerprint",
            "feature_flags",
        )
        read_only_fields = fields
        lookup_field = "id"

    def get_domain(self, obj):
        return GatewayHandler.get_domain(obj)

    def get_docs_url(self, obj):
        return GatewayHandler.get_docs_url(obj)

    def get_public_key_fingerprint(self, obj):
        return calculate_fingerprint(obj.jwt.public_key)

    def get_allow_update_gateway_auth(self, obj):
        return self.context["auth_config"].allow_update_gateway_auth

    def get_feature_flags(self, obj):
        return self.context["feature_flags"]

    def get_is_official(self, obj):
        return GatewayTypeEnum.is_official(self.context["auth_config"].gateway_type)


class GatewayUpdateInputSLZ(serializers.ModelSerializer):
    maintainers = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = Gateway
        fields = (
            "description",
            "maintainers",
            "is_public",
        )
        lookup_field = "id"


class GatewayUpdateStatusInputSLZ(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = ("status",)
        lookup_field = "id"
