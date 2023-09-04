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
from rest_framework.serializers import ValidationError

from apigateway.apis.open.gateway import views
from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.models import JWT, APIRelatedApp, Gateway, Release, Stage
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json

pytestmark = pytest.mark.django_db


@pytest.fixture()
def disable_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.open.gateway.views.GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestAPIViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, meta_schemas):
        self.factory = APIRequestFactory()
        self.api_auth_context = GatewayAuthContext()

    def test_list(self):
        gateway_1 = create_gateway(name="api_1", status=1, is_public=True)
        gateway_2 = create_gateway(name="api_2", status=1, is_public=False)
        create_gateway(name="api_3", status=1, is_public=True)

        self.api_auth_context.save(gateway_1.id, {"user_auth_type": "ieod", "api_type": 10})
        self.api_auth_context.save(gateway_2.id, {"user_auth_type": "ieod", "api_type": 10})

        s1 = G(Stage, gateway=gateway_1, status=1)
        s2 = G(Stage, gateway=gateway_2, status=1)

        G(Release, gateway=gateway_1, stage=s1)
        G(Release, gateway=gateway_2, stage=s2)

        data = [
            {
                "user_auth_type": "ieod",
                "expected": [
                    {
                        "id": gateway_1.id,
                        "name": gateway_1.name,
                        "description": gateway_1.description,
                        "maintainers": gateway_1.maintainers,
                        "api_type": 10,
                        "user_auth_type": "ieod",
                    }
                ],
            },
        ]

        for test in data:
            request = self.factory.get("/api/v1/apis/", data=test)

            view = views.GatewayViewSet.as_view({"get": "list"})
            response = view(request)

            result = get_response_json(response)
            assert result["code"] == 0, result
            assert result["data"] == test["expected"]

    def test_retrieve(self):
        gateway_1 = create_gateway(name="api_1", status=1, is_public=True)
        gateway_2 = create_gateway(name="api_2", status=1, is_public=False)

        data = [
            {
                "id": gateway_1.id,
                "expected": {
                    "id": gateway_1.id,
                    "name": gateway_1.name,
                    "description": gateway_1.description,
                    "maintainers": gateway_1.maintainers,
                },
            },
            {
                "id": gateway_2.id,
                "expected": {
                    "id": gateway_2.id,
                    "name": gateway_2.name,
                    "description": gateway_2.description,
                    "maintainers": gateway_2.maintainers,
                },
            },
        ]

        for test in data:
            gateway_id = test["id"]
            request = self.factory.get(f"/api/v1/apis/{gateway_id}/", data=test)

            view = views.GatewayViewSet.as_view({"get": "retrieve"})
            response = view(request, id=gateway_id)

            result = get_response_json(response)
            assert result["code"] == 0, result
            assert result["data"] == test["expected"]


class TestAPIPublicKeyViewSet:
    def test_get_public_key(self, mocker, settings, request_factory, unique_gateway_name):
        settings.JWT_ISSUER = "foo"

        mocker.patch(
            "apigateway.apis.open.gateway.views.GatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

        gateway = G(Gateway, name=unique_gateway_name)
        G(JWT, gateway=gateway, public_key="test")

        request = request_factory.get(f"/api/v1/apis/{unique_gateway_name}/public_key/")
        request.gateway = gateway

        view = views.GatewayPublicKeyViewSet.as_view({"get": "get_public_key"})
        response = view(request, gateway_name=unique_gateway_name)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"] == {
            "issuer": "foo",
            "public_key": "test",
        }


class TestAPISyncViewSet:
    def test_sync(self, mocker, request_factory, unique_gateway_name):
        mocker.patch(
            "apigateway.apis.open.gateway.views.GatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

        bk_app_code = "test"
        gateway = G(Gateway, name=unique_gateway_name, is_public=False)

        request = request_factory.post(
            f"/api/v1/apis/{unique_gateway_name}/sync/",
            data={
                "name": unique_gateway_name,
                "description": "desc",
                "is_public": True,
            },
        )
        request.gateway = gateway
        request.app = mock.MagicMock(app_code=bk_app_code)

        view = views.GatewaySyncViewSet.as_view({"post": "sync"})
        response = view(request, gateway_name=unique_gateway_name)

        result = get_response_json(response)
        gateway = Gateway.objects.get(name=unique_gateway_name)
        assert result["code"] == 0
        assert gateway.is_public is True


class TestAPIRelatedAppViewSet:
    def test_add_related_apps_ok(self, mocker, request_factory, disable_app_permission):
        request = request_factory.post(
            "/backend/api/v1/demo/related-apps/",
            data={"target_app_codes": ["test1", "test2"]},
        )
        request.gateway = G(Gateway)
        view = views.GatewayRelatedAppViewSet.as_view({"post": "add_related_apps"})

        mocker.patch(
            "apigateway.apis.open.gateway.serializers.BKAppCodeListValidator.__call__",
            return_value=None,
        )
        view = views.GatewayRelatedAppViewSet.as_view({"post": "add_related_apps"})
        response = view(request, gateway_name=request.gateway.name)
        result = get_response_json(response)
        assert result["code"] == 0
        assert APIRelatedApp.objects.filter(gateway=request.gateway).count() == 2

    def test_add_related_apps_error(self, mocker, request_factory, disable_app_permission):
        request = request_factory.post(
            "/backend/api/v1/demo/related-apps/",
            data={"target_app_codes": ["test1", "test2"]},
        )
        request.gateway = G(Gateway)
        view = views.GatewayRelatedAppViewSet.as_view({"post": "add_related_apps"})

        mocker.patch(
            "apigateway.apis.open.gateway.serializers.BKAppCodeListValidator.__call__",
            side_effect=ValidationError(),
        )
        response = view(request, gateway_name=request.gateway.name)
        result = get_response_json(response)
        assert result["code"] != 0
        assert response.status_code != 200
