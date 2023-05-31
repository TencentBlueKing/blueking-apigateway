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
from typing import Any, Dict, Optional, cast

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apigateway.core.constants import (
    HOST_WITHOUT_SCHEME_PATTERN,
    EtcdSecureTypeEnum,
    ServiceDiscoveryTypeEnum,
    SSLCertificateBindingScopeTypeEnum,
    StageItemTypeEnum,
)
from apigateway.core.models import SslCertificate, SslCertificateBinding, StageItemConfig


class NodeSLZ(serializers.Serializer):
    host = serializers.RegexField(HOST_WITHOUT_SCHEME_PATTERN)
    weight = serializers.IntegerField(min_value=1, max_value=10000)


class NodeConfigSLZ(serializers.Serializer):
    nodes = serializers.ListField(child=NodeSLZ(), allow_empty=False)


class EtcdDiscoveryConfigSLZ(serializers.Serializer):
    addresses = serializers.ListField(child=serializers.RegexField(HOST_WITHOUT_SCHEME_PATTERN))
    secure_type = serializers.ChoiceField(choices=EtcdSecureTypeEnum.get_choices(), allow_blank=True)
    ssl_certificate_id = serializers.IntegerField(required=False, allow_null=True)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        data["ssl_certificate_id"] = self._validate_ssl_certificate_id(
            data["secure_type"], data.get("ssl_certificate_id")
        )
        data.update(self._validate_password(data["secure_type"], data.get("username"), data.get("password")))

        return data

    def _validate_ssl_certificate_id(self, secure_type: str, ssl_certificate_id: Optional[int]) -> Optional[int]:
        if secure_type != EtcdSecureTypeEnum.SSL.value:
            return None

        if not ssl_certificate_id:
            raise ValidationError("ssl_certificate_id is required")

        return ssl_certificate_id

    def _validate_password(self, secure_type: str, username: Optional[str], password: Optional[str]) -> Dict[str, Any]:
        if secure_type != EtcdSecureTypeEnum.PASSWORD.value:
            return {"username": "", "password": ""}

        if not (username and password):
            raise ValidationError("username + password are required")

        return {"username": username, "password": password}


class ServiceDiscoverySLZ(serializers.Serializer):
    discovery_type = serializers.ChoiceField(choices=ServiceDiscoveryTypeEnum.get_choices())
    discovery_config = serializers.DictField(allow_empty=False)

    class Meta:
        discovery_config_serializer = {
            ServiceDiscoveryTypeEnum.GO_MICRO_ETCD.value: EtcdDiscoveryConfigSLZ(),
        }

    def validate(self, data):
        data["discovery_config"] = self._validate_discovery_config(data["discovery_type"], data["discovery_config"])
        return data

    def _validate_discovery_config(self, discovery_type: str, discovery_config: Dict[str, Any]) -> Dict[str, Any]:
        serializer = self.Meta.discovery_config_serializer[discovery_type]
        try:
            return serializer.run_validation(discovery_config)
        except ValidationError as err:
            raise ValidationError({"discovery_config": err.detail})


class StageItemConfigSLZ(serializers.ModelSerializer):
    config = serializers.DictField(allow_empty=False)

    class Meta:
        model = StageItemConfig
        config_serializer: Dict[str, serializers.Serializer] = {
            "node": NodeConfigSLZ(),
            "service_discovery": ServiceDiscoverySLZ(),
        }
        fields = [
            "config",
        ]

    def validate(self, data):
        data["config"] = self._validate_config(self._get_stage_item_type(), data["config"])

        # 校验 ssl_certificate_id 应放在校验 config 之后，因类型非 ssl 时，校验 config 会将 ssl_certificate_id 置空
        self._validate_ssl_certificate_id(self._get_api_id(), self._get_ssl_certificate_id(data))

        return data

    def _get_ssl_certificate_id(self, validated_data) -> Optional[int]:
        if self._get_stage_item_type() != StageItemTypeEnum.SERVICE_DISCOVERY.value:
            return None

        return validated_data["config"]["discovery_config"].get("ssl_certificate_id")

    def _validate_ssl_certificate_id(self, gateway_id: int, ssl_certificate_id: Optional[int]):
        """校验 ssl_certificate_id 是否有效"""
        if not ssl_certificate_id:
            return

        if not SslCertificate.objects.filter(api_id=gateway_id, id=ssl_certificate_id).exists():
            raise ValidationError(f"ssl_certificate_id [id={ssl_certificate_id}] does not exist")

    def _validate_config(self, type_: str, config: Dict[str, Any]) -> Dict[str, Any]:
        serializer = self.Meta.config_serializer[type_]
        try:
            return cast(Dict[str, Any], serializer.run_validation(config))
        except ValidationError as err:
            raise ValidationError({"config": err.detail})

    def create(self, validated_data):
        instance = super().create(
            {
                "api": self.context["api"],
                "stage": self.context["stage"],
                "stage_item": self.context["stage_item"],
                **validated_data,
            }
        )

        if self._get_ssl_certificate_id(validated_data):
            SslCertificateBinding.objects.sync_binding(
                gateway_id=self._get_api_id(),
                scope_type=SSLCertificateBindingScopeTypeEnum.STAGE_ITEM_CONFIG,
                scope_id=instance.id,
                ssl_certificate_id=self._get_ssl_certificate_id(validated_data),
            )

        return instance

    def update(self, instance, validated_data):
        validated_data.pop("created_by", None)
        instance = super().update(instance, validated_data)

        SslCertificateBinding.objects.sync_binding(
            gateway_id=self._get_api_id(),
            scope_type=SSLCertificateBindingScopeTypeEnum.STAGE_ITEM_CONFIG,
            scope_id=instance.id,
            ssl_certificate_id=self._get_ssl_certificate_id(validated_data),
        )

        return instance

    def _get_api_id(self):
        return self.context["api"].id

    def _get_stage_item_type(self):
        return self.context["stage_item"].type
