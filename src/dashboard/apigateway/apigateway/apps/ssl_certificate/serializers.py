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
from typing import List

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apigateway.common.fields import CurrentGatewayDefault
from apigateway.core.constants import SSLCertificateBindingScopeTypeEnum, SSLCertificateTypeEnum
from apigateway.core.models import SslCertificate, SslCertificateBinding
from apigateway.utils.crypto import CertificateChecker
from apigateway.utils.time import utctime


class SSLCertificateSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    snis = serializers.ListField(child=serializers.CharField(), allow_empty=True, read_only=True)
    expires = serializers.DateTimeField(read_only=True)

    class Meta:
        model = SslCertificate
        fields = (
            "id",
            "gateway",
            "type",
            "name",
            "snis",
            "cert",
            "key",
            "ca_cert",
            "expires",
        )
        lookup_field = "id"

        validators = [
            UniqueTogetherValidator(
                queryset=SslCertificate.objects.all(),
                fields=["gateway", "type", "name"],
                message=gettext_lazy("网关下证书名称已存在。"),
            ),
        ]

    def validate(self, data):
        checker = CertificateChecker(key=data["key"], cert=data["cert"], ca_cert=data.get("ca_cert"))
        cert_info = checker.check()
        data.update(
            expires=utctime(cert_info["validity_end"]).datetime,
            snis=cert_info["snis"],
        )
        return data

    def validate_type(self, value):
        if self.instance and self.instance.type != value:
            raise serializers.ValidationError(_("证书类型不能修改。"))
        return value


class QuerySSLCertificateSLZ(serializers.Serializer):
    type = serializers.ChoiceField(choices=SSLCertificateTypeEnum.get_choices())
    keyword = serializers.CharField(allow_blank=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "expires", "-expires", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class ListSSLCertificateSLZ(serializers.ModelSerializer):
    snis = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    class Meta:
        model = SslCertificate
        fields = (
            "id",
            "name",
            "snis",
            "expires",
            "updated_time",
        )
        lookup_field = "id"


class BindOrUnbindScopesSLZ(serializers.Serializer):
    """证书绑定、解绑 scope 对象"""

    ssl_certificate_id = serializers.IntegerField()
    scope_type = serializers.ChoiceField(choices=SSLCertificateBindingScopeTypeEnum.get_choices())
    scope_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)

    def validate_ssl_certificate_id(self, value) -> int:
        valid_id = SslCertificate.objects.get_valid_id(gateway_id=self.context["gateway_id"], id_=value)
        if not valid_id:
            raise serializers.ValidationError(
                _("证书【id={ssl_certificate_id}】不存在。").format(ssl_certificate_id=value)
            )
        return valid_id

    def validate(self, data):
        data["scope_ids"] = self._get_valid_scope_ids(data["scope_type"], data["scope_ids"])
        return data

    def _get_valid_scope_ids(self, scope_type: str, scope_ids: List[int]) -> List[int]:
        return SslCertificateBinding.objects.get_valid_scope_ids(self.context["gateway_id"], scope_type, scope_ids)


class BindOrUnbindSSLCertificatesSLZ(serializers.Serializer):
    """scope 对象绑定、解绑证书"""

    scope_type = serializers.ChoiceField(choices=SSLCertificateBindingScopeTypeEnum.get_choices())
    scope_id = serializers.IntegerField()
    ssl_certificate_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)

    def validate_ssl_certificate_ids(self, value: List[int]) -> List[int]:
        return SslCertificate.objects.get_valid_ids(self.context["gateway_id"], value)

    def validate(self, data):
        data["scope_id"] = self._validate_scope_id(data["scope_type"], data["scope_id"])
        return data

    def _validate_scope_id(self, scope_type: str, scope_id: int) -> int:
        valid_scope_id = SslCertificateBinding.objects.get_valid_scope_id(
            self.context["gateway_id"], scope_type, scope_id
        )
        if not valid_scope_id:
            raise serializers.ValidationError(
                {"scope_id": _("scope【id={scope_id}】不存在。").format(scope_id=scope_id)}
            )

        return valid_scope_id


class QuerySSLCertificateBindingSLZ(serializers.Serializer):
    ssl_certificate_id = serializers.IntegerField(required=False, allow_null=True)
    scope_type = serializers.ChoiceField(choices=SSLCertificateBindingScopeTypeEnum.get_choices())
    scope_id = serializers.IntegerField(required=False, allow_null=True)


class ListSSLCertificateBindingSLZ(serializers.ModelSerializer):
    class Meta:
        model = SslCertificateBinding
        fields = [
            "ssl_certificate_id",
            "scope_type",
            "scope_id",
        ]


class CheckCertSLZ(serializers.Serializer):
    key = serializers.CharField()
    cert = serializers.CharField()
    ca_cert = serializers.CharField(required=False, allow_blank=True)
