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
from typing import Any, Dict, Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from apigateway.apps.stage_item.config.serializers import NodeConfigSLZ, ServiceDiscoverySLZ
from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import (
    BACKEND_SERVICE_NAME_PATTERN,
    MAX_CONNECT_TIMEOUT_IN_SECOND,
    MAX_READ_TIMEOUT_IN_SECOND,
    MAX_SEND_TIMEOUT_IN_SECOND,
    BackendUpstreamTypeEnum,
    LoadBalanceTypeEnum,
    PassHostEnum,
    SchemeEnum,
    SSLCertificateBindingScopeTypeEnum,
)
from apigateway.core.models import BackendService, SslCertificate, SslCertificateBinding, StageItem


class TimeoutSLZ(serializers.Serializer):
    connect = serializers.IntegerField(max_value=MAX_CONNECT_TIMEOUT_IN_SECOND, min_value=1)
    send = serializers.IntegerField(max_value=MAX_SEND_TIMEOUT_IN_SECOND, min_value=1)
    read = serializers.IntegerField(max_value=MAX_READ_TIMEOUT_IN_SECOND, min_value=1)


class ServiceDiscoveryUpstreamConfigSLZ(serializers.Serializer):
    service_name = serializers.CharField()


class BackendServiceSLZ(serializers.ModelSerializer):
    api = serializers.HiddenField(default=CurrentGatewayDefault())
    name = serializers.RegexField(regex=BACKEND_SERVICE_NAME_PATTERN)
    loadbalance = serializers.ChoiceField(choices=LoadBalanceTypeEnum.get_choices())
    upstream_type = serializers.ChoiceField(choices=BackendUpstreamTypeEnum.get_choices())
    stage_item_id = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    upstream_custom_config = serializers.DictField(default=dict)
    upstream_config = serializers.DictField(default=dict)
    pass_host = serializers.ChoiceField(choices=PassHostEnum.get_choices())
    upstream_host = serializers.CharField(allow_blank=True, required=False)
    scheme = serializers.ChoiceField(choices=SchemeEnum.get_choices())
    timeout = TimeoutSLZ()
    ssl_enabled = serializers.BooleanField(default=False)

    class Meta:
        model = BackendService
        fields = (
            "id",
            "api",
            "name",
            "description",
            "loadbalance",
            "upstream_type",
            "stage_item_id",
            "upstream_custom_config",
            "upstream_config",
            "pass_host",
            "upstream_host",
            "scheme",
            "timeout",
            "ssl_enabled",
        )
        lookup_field = "id"

        upstream_custom_config_serializer: Dict[str, serializers.Serializer] = {
            BackendUpstreamTypeEnum.NODE.value: NodeConfigSLZ(),
            BackendUpstreamTypeEnum.SERVICE_DISCOVERY.value: ServiceDiscoverySLZ(),
        }

        upstream_config_serializer: Dict[str, serializers.Serializer] = {
            BackendUpstreamTypeEnum.SERVICE_DISCOVERY.value: ServiceDiscoveryUpstreamConfigSLZ(),
        }

        validators = [
            UniqueTogetherValidator(
                queryset=BackendService.objects.all(),
                fields=["api", "name"],
                message="网关下后端服务名称已存在",
            ),
        ]

    def validate(self, data):
        gateway_id = self._get_gateway_id()
        self._validate_discovery_ssl_certificate_id(gateway_id, self._get_discovery_ssl_certificate_id(data))
        self._validate_stage_item_id(gateway_id, data.get("stage_item_id"))

        data["upstream_custom_config"] = self._validate_upstream_custom_config(
            data.get("stage_item_id"),
            data["upstream_type"],
            data.get("upstream_custom_config"),
        )
        data["upstream_config"] = self._validate_upstream_config(
            data["upstream_type"],
            data.get("upstream_config", {}),
        )

        data["upstream_host"] = self._validate_upstream_host(data["pass_host"], data.get("upstream_host"))

        return data

    def _validate_upstream_custom_config(
        self,
        stage_item_id: Optional[int],
        upstream_type: str,
        upstream_custom_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        if stage_item_id:
            return {}

        serializer = self.Meta.upstream_custom_config_serializer[upstream_type]
        try:
            return serializer.run_validation(upstream_custom_config)  # type: ignore
        except ValidationError as err:
            raise ValidationError({"upstream_custom_config": err.detail})

    def _validate_upstream_config(
        self,
        upstream_type: str,
        upstream_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        serializer = self.Meta.upstream_config_serializer.get(upstream_type)
        if not serializer:
            return {}

        try:
            return serializer.run_validation(upstream_config)
        except ValidationError as err:
            raise ValidationError({"upstream_config": err.detail})

    def _validate_upstream_host(self, pass_host: str, upstream_host: Optional[str]):
        if pass_host != PassHostEnum.REWRITE.value:
            return ""

        if not upstream_host:
            raise ValidationError("upstream_host is required")

        return upstream_host

    def create(self, validated_data):
        # 因包含 nested serializer, 因此不能使用父类的 create 方法
        instance = self.Meta.model.objects.create(**validated_data)

        ssl_certificate_id = self._get_discovery_ssl_certificate_id(validated_data)
        if ssl_certificate_id:
            SslCertificateBinding.objects.sync_binding(
                gateway_id=validated_data["api"].id,
                scope_type=SSLCertificateBindingScopeTypeEnum.BACKEND_SERVICE_DISCOVERY_CONFIG,
                scope_id=instance.id,
                ssl_certificate_id=ssl_certificate_id,
            )

        return instance

    def update(self, instance, validated_data):
        # 因包含 nested serializer, 因此不能使用父类的 update 方法
        instance.__dict__.update(validated_data)
        instance.save()

        ssl_certificate_id = self._get_discovery_ssl_certificate_id(validated_data)
        SslCertificateBinding.objects.sync_binding(
            gateway_id=validated_data["api"].id,
            scope_type=SSLCertificateBindingScopeTypeEnum.BACKEND_SERVICE_DISCOVERY_CONFIG,
            scope_id=instance.id,
            ssl_certificate_id=ssl_certificate_id,
        )

        return instance

    def _get_discovery_ssl_certificate_id(self, validated_data) -> Optional[int]:
        if validated_data.get("stage_item_id"):
            return None

        upstream_type = validated_data["upstream_type"]
        if upstream_type != BackendUpstreamTypeEnum.SERVICE_DISCOVERY.value:
            return None

        return validated_data["upstream_custom_config"]["discovery_config"].get("ssl_certificate_id")

    def _validate_discovery_ssl_certificate_id(self, gateway_id: int, ssl_certificate_id: Optional[int]):
        """校验 ssl_certificate_id 是否有效"""
        if not ssl_certificate_id:
            return

        if not SslCertificate.objects.filter(id=ssl_certificate_id, api_id=gateway_id).exists():
            raise ValidationError(f"ssl_certificate_id [{ssl_certificate_id}] does not exist")

    def _validate_stage_item_id(self, gateway_id: int, stage_item_id: Optional[int]):
        """校验 stage_item_id 是否有效"""
        if not stage_item_id:
            return

        if not StageItem.objects.filter(id=stage_item_id, api_id=gateway_id).exists():
            raise ValidationError(f"stage_item_id [{stage_item_id}] does not exist")

    def _get_gateway_id(self) -> int:
        return self.context["api"].id


class QueryBackendServiceSLZ(serializers.Serializer):
    query = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "upstream_type", "-upstream_type", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class ListBackendServiceSLZ(serializers.ModelSerializer):
    class Meta:
        model = BackendService
        fields = (
            "id",
            "name",
            "description",
            "loadbalance",
            "upstream_type",
            "updated_time",
        )
        lookup_field = "id"
