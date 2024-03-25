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
import uuid

from django.conf import settings
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.micro_gateway.constants import MicroGatewayCreateWayEnum
from apigateway.apps.micro_gateway.handlers import MicroGatewayHandlerFactory
from apigateway.common.factories import SchemaFactory
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.common.mixins.serializers import ExtensibleFieldMixin
from apigateway.controller.micro_gateway_config import (
    MicroGatewayBcsInfo,
    MicroGatewayHTTPInfo,
    MicroGatewayJWTAuth,
)
from apigateway.core.constants import MICRO_GATEWAY_NAME_PATTERN
from apigateway.core.models import MicroGateway
from apigateway.utils.string import generate_unique_id
from apigateway.utils.time import now_datetime


class BcsInfoSLZ(serializers.Serializer):
    project_name = serializers.CharField(max_length=64, required=True)
    project_id = serializers.CharField(max_length=64, required=True)
    cluster_id = serializers.CharField(max_length=64, required=True)
    namespace = serializers.CharField(max_length=64, required=True)
    release_name = serializers.CharField(max_length=64, required=True)
    chart_name = serializers.CharField(max_length=64, required=True)
    chart_version = serializers.CharField(max_length=32, required=True)


class HttpInfoSLZ(serializers.Serializer):
    http_url = serializers.URLField(max_length=512, required=True)


class JwtAuthInfo(serializers.Serializer):
    secret_key = serializers.CharField(read_only=True)


class MicroGatewaySLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    create_way = serializers.ChoiceField(
        choices=MicroGatewayCreateWayEnum.get_choices(), label="创建方式", write_only=True
    )
    id = serializers.UUIDField(read_only=True)
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(MICRO_GATEWAY_NAME_PATTERN, required=True)
    bcs_info = BcsInfoSLZ()
    http_info = HttpInfoSLZ()
    jwt_auth_info = JwtAuthInfo(read_only=True)
    bk_apigateway_api_url = serializers.SerializerMethodField()

    class Meta:
        model = MicroGateway
        non_model_fields = ["create_way", "bcs_info", "http_info", "jwt_auth_info"]
        fields = [
            "id",
            "gateway",
            "name",
            "description",
            "bk_apigateway_api_url",
        ] + non_model_fields
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=MicroGateway.objects.all(),
                fields=["gateway", "name"],
                message=gettext_lazy("该网关下，同名微网关实例已存在。"),
            )
        ]

    def to_internal_value(self, data):
        create_way = MicroGatewayCreateWayEnum(data.get("create_way", ""))
        data["bcs_info"].update(MicroGatewayHandlerFactory.get_handler(create_way).get_initial_bcs_info())
        return super().to_internal_value(data)

    def to_representation(self, instance):
        instance.bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(instance.config)
        instance.http_info = MicroGatewayHTTPInfo.from_micro_gateway_config(instance.config)
        instance.jwt_auth_info = MicroGatewayJWTAuth.from_micro_gateway_config(instance.config)
        return super().to_representation(instance)

    def get_bk_apigateway_api_url(self, obj):
        return settings.BK_APIGATEWAY_API_URL

    def create(self, validated_data):
        create_way = MicroGatewayCreateWayEnum(validated_data["create_way"])
        status = MicroGatewayHandlerFactory.get_handler(create_way).get_initial_status()
        validated_data.update(
            {
                "id": str(uuid.uuid4()),
                "is_shared": False,
                "status": status.value,
                "status_updated_time": now_datetime(),
                "config": {
                    "bcs": validated_data["bcs_info"],
                    "http": validated_data["http_info"],
                    "jwt_auth": {
                        "secret_key": generate_unique_id(),
                    },
                },
                "schema": SchemaFactory().get_micro_gateway_schema(),
            }
        )

        return super().create(validated_data)


class UpdateMicroGatewaySLZ(ExtensibleFieldMixin, serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(MICRO_GATEWAY_NAME_PATTERN, required=True)
    need_deploy = serializers.BooleanField(default=True)
    http_info = HttpInfoSLZ()

    class Meta:
        model = MicroGateway
        non_model_fields = ["http_info", "need_deploy"]
        fields = [
            "gateway",
            "name",
            "description",
        ] + non_model_fields
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=MicroGateway.objects.all(),
                fields=["gateway", "name"],
                message=gettext_lazy("该网关下，同名微网关实例已存在。"),
            )
        ]

    def update(self, instance, validated_data):
        # 仅更新“访问地址”
        config = instance.config
        config.update(
            {
                "http": validated_data["http_info"],
            }
        )

        validated_data["config"] = config
        return super().update(instance, validated_data)


class QueryMicroGatewaySLZ(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "status", "-status", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class ListMicroGatewaySLZ(serializers.ModelSerializer):
    chart_version = serializers.SerializerMethodField()
    release_name = serializers.SerializerMethodField()
    stage_name = serializers.SerializerMethodField()

    class Meta:
        model = MicroGateway
        fields = [
            "id",
            "name",
            "description",
            "status",
            "comment",
            "updated_time",
            "chart_version",
            "release_name",
            "stage_name",
        ]
        read_only_fields = fields
        lookup_field = "id"

    def get_chart_version(self, obj) -> str:
        return obj.config.get("bcs", {}).get("chart_version", "")

    def get_release_name(self, obj) -> str:
        return obj.config.get("bcs", {}).get("release_name", "")

    def get_stage_name(self, obj) -> str:
        return self.context["micro_gateway_id_to_stage_fields"].get(obj.id, {}).get("name", "")
