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

import pytest
from django_dynamic_fixture import G

from apigateway.apis.open.gateway import views
from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.core.models import Gateway, GatewayRelatedApp, Release


@pytest.fixture()
def disable_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.open.gateway.views.GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestGatewayListApi:
    def test_list(self, request_view, fake_gateway, mocker):
        mocker.patch(
            "apigateway.apis.open.gateway.views.GatewayListApi._filter_list_queryset",
            return_value=Gateway.objects.filter(id=fake_gateway),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.gateway.list",
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

        queryset = view._filter_list_queryset(name=fake_gateway, fuzzy=False)
        assert list(queryset.values_list("id", flat=True)) == [fake_gateway.id]

        queryset = view._filter_list_queryset(user_auth_type="not-exist")
        assert queryset.count() == 0


class TestGatewayRetrieveApi:
    def test_retrieve(self, request_view, fake_gateway):
        resp = request_view(
            method="GET",
            view_name="openapi.gateway.retrieve",
            path_params={"id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert result["data"]


class TestGatewayPublicKeyRetrieveApi:
    def test_get(self, settings, request_view, fake_gateway):
        settings.JWT_ISSUER = "foo"

        jwt = GatewayJWTHandler.create_jwt(fake_gateway)

        resp = request_view(
            method="GET",
            view_name="openapi.gateway.get_public_key",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert result["data"] == {
            "issuer": "foo",
            "public_key": jwt.public_key,
        }


class TestGatewaySyncApi:
    def test_post(self, mocker, request_view, fake_gateway, disable_app_permission):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "description": "desc",
                "is_public": True,
            },
            app=mocker.MagicMock(app_code="foo"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert result["data"]["id"] == fake_gateway.id


class TestGatewayUpdateStatusApi:
    def test_post(self, request_view, fake_gateway, disable_app_permission):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.update_status",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "status": 0,
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert Gateway.objects.get(id=fake_gateway.id).status == 0


class TestGatewayRelatedAppAddApi:
    def test_post(self, request_view, fake_gateway, disable_app_permission):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.add_related_app",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "target_app_codes": ["test1", "test2"],
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert GatewayRelatedApp.objects.filter(gateway=fake_gateway).count() == 2
