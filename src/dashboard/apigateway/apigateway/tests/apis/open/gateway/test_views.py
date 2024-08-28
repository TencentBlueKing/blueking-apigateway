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
from unittest import mock

import pytest
from django_dynamic_fixture import G

from apigateway.apis.open.gateway import views
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.core.models import Gateway, GatewayRelatedApp, Release
from apigateway.tests.utils.testing import get_response_json


@pytest.fixture()
def disable_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.open.gateway.views.OpenAPIGatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestGatewayListApi:
    def test_list(self, request_view, fake_gateway, mocker):
        mocker.patch(
            "apigateway.apis.open.gateway.views.GatewayListApi._filter_list_queryset",
            return_value=Gateway.objects.filter(id=fake_gateway.id),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.gateway.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()
        assert resp.status_code == 200
        assert result["code"] == 0
        assert len(result["data"]) >= 1

    def test_filter_list_queryset(self, fake_gateway):
        G(Release, gateway=fake_gateway)

        view = views.GatewayListApi()

        queryset = view._filter_list_queryset()
        assert queryset.filter(id=fake_gateway.id).exists()

        queryset = view._filter_list_queryset(name=fake_gateway.name, fuzzy=False)
        assert list(queryset.values_list("id", flat=True)) == [fake_gateway.id]

        queryset = view._filter_list_queryset(user_auth_type="not-exist")
        assert queryset.count() == 0


class TestGatewayRetrieveApi:
    def test_retrieve(self, request_to_view, request_factory, fake_gateway):
        request = request_factory.get("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")
        response = request_to_view(
            request,
            view_name="openapi.gateway.retrieve",
            path_params={"id": fake_gateway.id},
        )
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["code"] == 0
        assert result["data"]


class TestGatewayPublicKeyRetrieveApi:
    def test_get(self, settings, request_to_view, request_factory, fake_gateway):
        request = request_factory.get("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        settings.JWT_ISSUER = "foo"

        jwt = GatewayJWTHandler.create_jwt(fake_gateway)

        response = request_to_view(
            request,
            # method="GET",
            view_name="openapi.gateway.get_public_key",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["code"] == 0
        assert result["data"] == {
            "issuer": "foo",
            "public_key": jwt.public_key,
        }


class TestGatewaySyncApi:
    def test_post(self, mocker, request_view, unique_gateway_name, disable_app_permission):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.sync",
            path_params={"gateway_name": unique_gateway_name},
            data={
                "description": "desc",
                "is_public": True,
                "allow_delete_sensitive_params": False,
            },
            app=mocker.MagicMock(app_code="foo"),
        )
        result = resp.json()

        gateway = Gateway.objects.get(name=unique_gateway_name)
        assert resp.status_code == 200
        assert result["code"] == 0
        assert result["data"]["id"] == gateway.id

        auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
        assert auth_config["allow_auth_from_params"] is True
        assert auth_config["allow_delete_sensitive_params"] is False


class TestGatewayUpdateStatusApi:
    def test_post(self, request_view, fake_gateway, disable_app_permission):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.update_status",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "status": 0,
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert Gateway.objects.get(id=fake_gateway.id).status == 0


class TestGatewayRelatedAppAddApi:
    def test_post(self, request_view, fake_gateway, disable_app_permission):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.add_related_apps",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "target_app_codes": ["test1", "test2"],
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert GatewayRelatedApp.objects.filter(gateway=fake_gateway).count() == 2
