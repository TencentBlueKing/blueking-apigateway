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
from ddf import G

from apigateway.apis.open.permission import views
from apigateway.apis.open.permission.helpers import AppPermissionHelper
from apigateway.apps.permission import models
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def disable_api_related_app_permission_check(mocker):
    mocker.patch(
        "apigateway.apis.open.permission.views.GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestResourceViewSet:
    @pytest.mark.parametrize(
        "is_active_and_public, mocked_resources, mocked_resource_permissions, expected",
        [
            # is_active_and_public is False
            (
                False,
                None,
                None,
                [],
            ),
            # is_active_and_public is true, but data is empty
            (
                True,
                [],
                [],
                [],
            ),
            # allow_apply_permission is filtered
            (
                True,
                [
                    {
                        "id": 1,
                        "name": "test",
                        "description": "desc",
                        "doc_link": "",
                        "resource_perm_required": True,
                        "allow_apply_permission": False,
                    },
                    {
                        "id": 2,
                        "name": "test",
                        "api_name": "test",
                        "description": "desc",
                        "doc_link": "",
                        "resource_perm_required": True,
                        "allow_apply_permission": True,
                    },
                ],
                None,
                [
                    {
                        "id": 2,
                        "name": "test",
                        "api_name": "test",
                        "description": "desc",
                        "description_en": None,
                        "doc_link": "",
                        "permission_status": "need_apply",
                        "permission_action": "apply",
                        "permission_level": "normal",
                        "expires_in": None,
                    },
                ],
            ),
            (
                True,
                [],
                [
                    {
                        "id": 1,
                        "name": "test",
                        "api_name": "test",
                        "doc_link": "test",
                        "description": "desc",
                        "permission_status": "owned",
                        "permission_level": "normal",
                        "expires_in": 10,
                    }
                ],
                [
                    {
                        "id": 1,
                        "name": "test",
                        "api_name": "test",
                        "description": "desc",
                        "description_en": None,
                        "doc_link": "test",
                        "permission_status": "owned",
                        "permission_action": "renew",
                        "permission_level": "normal",
                        "expires_in": 10,
                    }
                ],
            ),
        ],
    )
    def test_list(
        self,
        mocker,
        fake_gateway,
        request_factory,
        is_active_and_public,
        mocked_resources,
        mocked_resource_permissions,
        expected,
    ):
        fake_gateway.name = "test"

        mocker.patch(
            "apigateway.core.models.Gateway.is_active_and_public",
            new_callable=mock.PropertyMock(return_value=is_active_and_public),
        )

        if mocked_resources is not None:
            mocker.patch(
                "apigateway.apis.open.permission.views.ResourceVersionHandler.get_released_public_resources",
                return_value=mocked_resources,
            )

        if mocked_resource_permissions is not None:
            mocker.patch(
                "apigateway.apis.open.permission.views.ResourcePermissionBuilder.build",
                return_value=mocked_resource_permissions,
            )

        request = request_factory.get(
            f"/api/v1/apis/{fake_gateway.id}/permissions/resources/",
            data={"target_app_code": "test"},
        )
        request.gateway = fake_gateway

        view = views.ResourceViewSet.as_view({"get": "list"})
        response = view(request)

        result = get_response_json(response)
        assert result["data"] == expected


class TestAppPermissionViewSet:
    def test_list(self, mocker, request_factory):
        mocker.patch(
            "apigateway.apis.open.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.open.permission.views.AppPermissionBuilder.build",
            return_value=[
                {
                    "id": 1,
                    "name": "test",
                    "api_name": "test",
                    "description": "desc",
                    "description_en": "desc_en",
                    "expires_in": 10,
                    "permission_level": "normal",
                    "permission_status": "owned",
                    "permission_action": "",
                    "doc_link": "",
                },
            ],
        )

        params = {
            "target_app_code": "test",
        }

        request = request_factory.get("/", data=params)

        view = views.AppPermissionViewSet.as_view({"get": "list"})
        response = view(request)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"] == [
            {
                "id": 1,
                "name": "test",
                "api_name": "test",
                "description": "desc",
                "description_en": "desc_en",
                "expires_in": 10,
                "permission_level": "normal",
                "permission_status": "owned",
                "permission_action": "renew",
                "doc_link": "",
            },
        ]


class TestAppPermissionRecordViewSet:
    def test_list(self, mocker, request_factory, unique_id, fake_gateway):
        mocker.patch(
            "apigateway.apis.open.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        params = {
            "target_app_code": unique_id,
        }

        record = G(models.AppPermissionRecord, bk_app_code=unique_id, gateway=fake_gateway)

        request = request_factory.get("/", data=params)

        view = views.AppPermissionRecordViewSet.as_view({"get": "list"})
        response = view(request)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"]["count"] == 1
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["id"] == record.id

    def test_retrieve(self, mocker, request_factory, unique_id, fake_gateway):
        mocker.patch(
            "apigateway.apis.open.permission.serializers.BKAppCodeValidator.__call__",
            return_value=None,
        )
        params = {
            "target_app_code": unique_id,
        }

        record = G(models.AppPermissionRecord, bk_app_code=unique_id, gateway=fake_gateway)

        request = request_factory.get("/", data=params)

        view = views.AppPermissionRecordViewSet.as_view({"get": "retrieve"})
        response = view(request, record.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"]["id"] == record.id


class TestAppPermissionGrantViewSet:
    def test_grant(self, mocker, request_factory, fake_gateway):
        mocker.patch(
            "apigateway.apis.open.permission.views.GatewayRelatedAppPermission.has_permission",
            return_value=True,
        )
        request = request_factory.post(
            "",
            data={
                "target_app_code": "test",
                "grant_dimension": "api",
            },
        )
        request.app = mock.MagicMock(app_code="test")
        request.gateway = fake_gateway

        view = views.AppPermissionGrantViewSet.as_view({"post": "grant"})
        response = view(request, gateway_name=fake_gateway.name)

        result = get_response_json(response)
        assert result["code"] == 0, result

        permission_model = AppPermissionHelper().get_permission_model("api")
        assert permission_model.objects.filter(gateway=fake_gateway, bk_app_code="test").exists()


class TestRevokeAppPermissionViewSet:
    def test_revoke(self, request_factory, fake_gateway):
        G(models.AppAPIPermission, gateway=fake_gateway, bk_app_code="app1")
        G(models.AppAPIPermission, gateway=fake_gateway, bk_app_code="app2")
        G(models.AppAPIPermission, gateway=fake_gateway, bk_app_code="app3")

        request = request_factory.delete(
            "",
            data={
                "target_app_codes": ["app1", "app2"],
                "grant_dimension": "api",
            },
        )
        request.gateway = fake_gateway

        view = views.RevokeAppPermissionViewSet.as_view({"delete": "revoke"})
        response = view(request, gateway_name=fake_gateway.name)

        result = get_response_json(response)
        assert result["code"] == 0, result

        permission_model = AppPermissionHelper().get_permission_model("api")
        assert not permission_model.objects.filter(gateway=fake_gateway, bk_app_code__in=["app1", "app2"]).exists()
        assert permission_model.objects.filter(gateway=fake_gateway, bk_app_code__in=["app3"]).exists()
