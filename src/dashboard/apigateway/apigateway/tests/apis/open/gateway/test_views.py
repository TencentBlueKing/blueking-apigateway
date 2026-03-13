# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.models import Gateway, GatewayRelatedApp, Release
from apigateway.service.gateway_jwt import GatewayJWTHandler
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
            path_params={"gateway_id": fake_gateway.id},
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
    def test_post(self, mocker, request_view, unique_gateway_name, disable_app_permission, default_data_plane):
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

        assert gateway.tenant_mode == "single"
        assert gateway.tenant_id == "default"

        auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
        assert auth_config["allow_delete_sensitive_params"] is False

    def test_post_with_multi_tenant_mode(
        self, mocker, request_view, unique_gateway_name, disable_app_permission, default_data_plane
    ):
        mocker.patch(
            "apigateway.apis.open.gateway.views.get_app_tenant_info",
            return_value=("global", "abc"),
        )

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
        assert gateway.tenant_mode == "global"
        assert gateway.tenant_id == "abc"

    @pytest.mark.parametrize(
        "gray_stage, expected_count",
        [
            ("start", 2),
            ("done", 1),
            ("not_start", 1),
        ],
    )
    def test_post_with_empty_data_planes_use_sync_rule_for_te_bp_gateway(
        self,
        mocker,
        settings,
        request_view,
        unique_gateway_name,
        disable_app_permission,
        default_data_plane,
        gray_stage,
        expected_count,
    ):
        settings.EDITION = "te"
        settings.BK_PLUGINS_DATA_PLANE_NAME = "bp"
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = gray_stage
        bp_data_plane = G(DataPlane, name="bp")

        gateway_name = f"bp-{unique_gateway_name}"
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.sync",
            path_params={"gateway_name": gateway_name},
            data={
                "description": "desc",
                "is_public": True,
                "allow_delete_sensitive_params": False,
            },
            app=mocker.MagicMock(app_code="foo"),
        )

        result = resp.json()
        gateway = Gateway.objects.get(name=gateway_name)
        binding_ids = set(
            GatewayDataPlaneBinding.objects.filter(gateway=gateway).values_list("data_plane_id", flat=True)
        )

        assert resp.status_code == 200
        assert result["code"] == 0
        assert len(binding_ids) == expected_count
        if gray_stage == "done":
            assert binding_ids == {bp_data_plane.id}
        elif gray_stage == "start":
            assert binding_ids == {default_data_plane.id, bp_data_plane.id}
        else:
            assert binding_ids == {default_data_plane.id}

    def test_post_with_nonexistent_data_planes_returns_error(
        self, mocker, request_view, unique_gateway_name, disable_app_permission, default_data_plane
    ):
        resp = request_view(
            method="POST",
            view_name="openapi.gateway.sync",
            path_params={"gateway_name": unique_gateway_name},
            data={
                "description": "desc",
                "is_public": True,
                "data_planes": ["not-exists", "default"],
            },
            app=mocker.MagicMock(app_code="foo"),
        )
        result = resp.json()

        assert resp.status_code == 400
        assert result["code"] != 0
        assert "not-exists" in str(result["message"])


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
    def test_post(self, request_view, fake_gateway, disable_app_permission, mocker):
        # mock call bkauth api result
        mocker.patch(
            "apigateway.apis.open.gateway.views.get_app_tenant_info",
            return_value=("single", "default"),
        )

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
