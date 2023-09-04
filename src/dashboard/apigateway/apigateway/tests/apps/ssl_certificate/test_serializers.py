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
import datetime

import pytest
from rest_framework.exceptions import ValidationError

from apigateway.apps.ssl_certificate import serializers
from apigateway.core.constants import SSLCertificateTypeEnum
from apigateway.core.models import SslCertificate

pytestmark = pytest.mark.django_db


class TestSSLCertificateSLZ:
    def test_validate(self, fake_gateway, fake_tls_key, fake_tls_cert, fake_tls_cacert):
        slz = serializers.SSLCertificateSLZ(
            data={
                "type": SSLCertificateTypeEnum.CLIENT.value,
                "name": "foo",
                "key": fake_tls_key,
                "cert": fake_tls_cert,
                "ca_cert": fake_tls_cacert,
            },
            context={
                "gateway": fake_gateway,
            },
        )
        slz.is_valid(raise_exception=True)

        assert slz.validated_data["snis"] == ["bkapi.example.com"]
        assert isinstance(slz.validated_data["expires"], datetime.datetime)

        slz.save()
        instance = SslCertificate.objects.get(gateway=fake_gateway, id=slz.instance.id)
        assert instance.snis == ["bkapi.example.com"]


class TestBindOrUnbindScopesSLZ:
    def test_validate(self, fake_ssl_certificate_binding):
        fake_gateway = fake_ssl_certificate_binding.gateway
        fake_ssl_certificate = fake_ssl_certificate_binding.ssl_certificate

        slz = serializers.BindOrUnbindScopesSLZ(
            data={
                "ssl_certificate_id": fake_ssl_certificate.id,
                "scope_type": "stage",
                "scope_ids": [fake_ssl_certificate_binding.scope_id, 0],
            },
            context={"gateway_id": fake_gateway.id},
        )
        slz.is_valid(raise_exception=True)
        assert slz.validated_data == {
            "ssl_certificate_id": fake_ssl_certificate.id,
            "scope_type": "stage",
            "scope_ids": [fake_ssl_certificate_binding.scope_id],
        }

        slz = serializers.BindOrUnbindScopesSLZ(
            data={
                "ssl_certificate_id": fake_ssl_certificate.id + 1,
                "scope_type": "stage",
                "scope_ids": [1],
            },
            context={"gateway_id": fake_gateway.id},
        )
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)


class TestBindOrUnbindSSLCertificatesSLZ:
    def test_validate(self, fake_ssl_certificate_binding):
        fake_gateway = fake_ssl_certificate_binding.gateway
        fake_ssl_certificate = fake_ssl_certificate_binding.ssl_certificate

        slz = serializers.BindOrUnbindSSLCertificatesSLZ(
            data={
                "scope_type": "stage",
                "scope_id": fake_ssl_certificate_binding.scope_id,
                "ssl_certificate_ids": [fake_ssl_certificate.id, 0],
            },
            context={"gateway_id": fake_gateway.id},
        )
        slz.is_valid(raise_exception=True)
        assert slz.validated_data == {
            "scope_type": "stage",
            "scope_id": fake_ssl_certificate_binding.scope_id,
            "ssl_certificate_ids": [fake_ssl_certificate.id],
        }

        slz = serializers.BindOrUnbindSSLCertificatesSLZ(
            data={
                "ssl_certificate_ids": [fake_ssl_certificate.id],
                "scope_type": "stage",
                "scope_id": 0,
            },
            context={"gateway_id": fake_gateway.id},
        )
        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)
