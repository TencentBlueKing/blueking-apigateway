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
from ddf import G

from apigateway.core.models import SslCertificateBinding, Stage


class TestSSLCertificateBindScopesViewSet:
    def test_bind(self, request_view, fake_ssl_certificate):
        fake_gateway = fake_ssl_certificate.gateway
        s1 = G(Stage, gateway=fake_gateway)
        s2 = G(Stage, gateway=fake_gateway)

        response = request_view(
            "POST",
            "ssl_certificates.binding.scope",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"scope_type": "stage", "scope_ids": [s1.id, s2.id], "ssl_certificate_id": fake_ssl_certificate.id},
        )
        result = response.json()
        assert result["code"] == 0
        assert (
            SslCertificateBinding.objects.filter(gateway=fake_gateway, ssl_certificate=fake_ssl_certificate).count()
            == 2
        )

    def test_unbind(self, request_view, fake_ssl_certificate):
        fake_gateway = fake_ssl_certificate.gateway
        s1 = G(Stage, gateway=fake_gateway)
        s2 = G(Stage, gateway=fake_gateway)
        G(
            SslCertificateBinding,
            gateway=fake_gateway,
            ssl_certificate=fake_ssl_certificate,
            scope_type="stage",
            scope_id=s1.id,
        )
        G(
            SslCertificateBinding,
            gateway=fake_gateway,
            ssl_certificate=fake_ssl_certificate,
            scope_type="stage",
            scope_id=s2.id,
        )

        response = request_view(
            "DELETE",
            "ssl_certificates.binding.scope",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"scope_type": "stage", "scope_ids": [s2.id], "ssl_certificate_id": fake_ssl_certificate.id},
        )
        result = response.json()
        assert result["code"] == 0
        assert (
            SslCertificateBinding.objects.filter(gateway=fake_gateway, ssl_certificate=fake_ssl_certificate).count()
            == 1
        )

    def test_list(self, request_view, fake_ssl_certificate_binding):
        fake_gateway = fake_ssl_certificate_binding.gateway
        fake_ssl_certificate = fake_ssl_certificate_binding.ssl_certificate

        response = request_view(
            "GET",
            "ssl_certificates.binding",
            path_params={"gateway_id": fake_gateway.id},
            data={
                "scope_type": "stage",
                "ssl_certificate_id": fake_ssl_certificate.id,
            },
        )

        result = response.json()
        assert result["code"] == 0
        assert len(result["data"]["results"]) == 1


class TestScopeBindSSLCertificateViewSet:
    def test_bind(self, request_view, fake_ssl_certificate):
        fake_gateway = fake_ssl_certificate.gateway
        s = G(Stage, gateway=fake_gateway)

        response = request_view(
            "POST",
            "ssl_certificates.binding.ssl_certificate",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"scope_type": "stage", "scope_id": s.id, "ssl_certificate_ids": [fake_ssl_certificate.id]},
        )
        result = response.json()
        assert result["code"] == 0
        assert (
            SslCertificateBinding.objects.filter(gateway=fake_gateway, ssl_certificate=fake_ssl_certificate).count()
            == 1
        )

    def test_unbind(self, request_view, fake_ssl_certificate):
        fake_gateway = fake_ssl_certificate.gateway
        s = G(Stage, gateway=fake_gateway)
        G(
            SslCertificateBinding,
            gateway=fake_gateway,
            ssl_certificate=fake_ssl_certificate,
            scope_type="stage",
            scope_id=s.id,
        )

        response = request_view(
            "DELETE",
            "ssl_certificates.binding.ssl_certificate",
            gateway=fake_gateway,
            path_params={"gateway_id": fake_gateway.id},
            data={"scope_type": "stage", "scope_id": s.id, "ssl_certificate_ids": [fake_ssl_certificate.id]},
        )
        result = response.json()
        assert result["code"] == 0
        assert (
            SslCertificateBinding.objects.filter(gateway=fake_gateway, ssl_certificate=fake_ssl_certificate).count()
            == 0
        )


class TestCheckCertViewSet:
    def test_check_cert(self, request_view, fake_gateway, fake_tls_key, fake_tls_cert, fake_tls_cacert):
        response = request_view(
            "POST",
            "ssl_certificates.check_cert",
            path_params={"gateway_id": fake_gateway.id},
            data={
                "key": fake_tls_key,
                "cert": fake_tls_cert,
                "cacert": fake_tls_cacert,
            },
        )

        result = response.json()
        assert result["code"] == 0
        assert result["data"]["snis"] == ["bkapi.example.com"]
