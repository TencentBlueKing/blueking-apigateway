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

from apigateway.apis.open.released import views
from apigateway.core.models import Stage
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


class TestReleasedResourceRetrieveApi:
    @pytest.mark.parametrize(
        "mocked_resource_version_id, mocked_resource,mocked_resource_schema_version, will_error, expected",
        [
            (
                1,
                {
                    "is_public": True,
                    "id": 1,
                    "name": "test",
                    "method": "GET",
                    "path": "/test/",
                },
                {},
                False,
                {"id": 1, "name": "test", "method": "GET", "path": "/test/", "schema": {}},
            ),
            (
                1,
                {"is_public": True, "id": 1, "name": "test", "method": "GET", "path": "/test/"},
                {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "description": "Status values that need to be considered for filter",
                            "required": False,
                            "explode": True,
                            "schema": {"type": "string", "default": "available", "enum": ["test"], "example": "test"},
                        },
                        {
                            "name": "api_key",
                            "in": "header",
                            "description": "",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                    ],
                },
                False,
                {
                    "id": 1,
                    "name": "test",
                    "method": "GET",
                    "path": "/test/",
                    "schema": {
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "description": "Status values that need to be considered for filter",
                                "required": False,
                                "explode": True,
                                "schema": {
                                    "type": "string",
                                    "default": "available",
                                    "enum": ["test"],
                                    "example": "test",
                                },
                            },
                            {
                                "name": "api_key",
                                "in": "header",
                                "description": "",
                                "required": True,
                                "schema": {"type": "string"},
                            },
                        ],
                    },
                },
            ),
            # resource_version_id is None
            (
                None,
                {
                    "is_public": True,
                    "id": 1,
                    "name": "test",
                    "method": "GET",
                    "path": "/test/",
                },
                {},
                True,
                None,
            ),
            # resource is None
            (
                1,
                None,
                {},
                True,
                None,
            ),
            # resource is not public
            (
                1,
                {
                    "is_public": False,
                    "id": 1,
                    "name": "test",
                    "method": "GET",
                    "path": "/test/",
                },
                {},
                True,
                None,
            ),
        ],
    )
    def test_retrieve(
        self,
        mocker,
        request_factory,
        fake_gateway,
        mocked_resource_version_id,
        mocked_resource,
        mocked_resource_schema_version,
        will_error,
        expected,
    ):
        get_released_resource_version_id_mock = mocker.patch(
            "apigateway.apis.open.released.views.Release.objects.get_released_resource_version_id",
            return_value=mocked_resource_version_id,
        )
        get_released_resource_mock = mocker.patch(
            "apigateway.apis.open.released.views.ReleasedResource.objects.get_released_resource",
            return_value=mocked_resource,
        )

        get_released_resource_schema_version_mock = mocker.patch(
            "apigateway.apis.open.released.views.ResourceVersionHandler.get_resource_schema",
            return_value=mocked_resource_schema_version,
        )

        request = request_factory.get("/backend/api/v1/demo/")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")
        stage_name = "prod"
        resource_name = mocked_resource and mocked_resource["name"]

        view = views.ReleasedResourceRetrieveApi.as_view()
        response = view(request, gateway_name=fake_gateway.name, stage_name=stage_name, resource_name=resource_name)
        result = get_response_json(response)

        if will_error:
            assert response.status_code == 404
            assert result["code"] == 40000
            return
        assert result["code"] == 0
        assert result["data"] == expected

        get_released_resource_version_id_mock.assert_called_once_with(
            fake_gateway.id,
            stage_name,
        )
        get_released_resource_mock.assert_called_once_with(
            fake_gateway.id,
            mocked_resource_version_id,
            resource_name,
        )


class TestReleasedResourceListByGatewayNameApi:
    @pytest.mark.parametrize(
        "stage_name, mocked_resources, expected",
        [
            (
                "prod",
                [
                    {
                        "id": 1,
                        "name": "test",
                        "description": "test",
                        "method": "GET",
                        "path": "/test/",
                        "match_subpath": False,
                        "enable_websocket": False,
                        "app_verified_required": True,
                        "resource_perm_required": True,
                        "user_verified_required": True,
                    },
                    {
                        "id": 2,
                        "name": "test",
                        "description": "test",
                        "method": "POST",
                        "path": "/test/",
                        "match_subpath": False,
                        "enable_websocket": False,
                        "app_verified_required": False,
                        "resource_perm_required": False,
                        "user_verified_required": False,
                    },
                ],
                {
                    "count": 2,
                    "has_next": False,
                    "has_previous": False,
                    "results": [
                        {
                            "id": 1,
                            "name": "test",
                            "description": "test",
                            "method": "GET",
                            "url": "http://bkapi.example.com/test/",
                            "match_subpath": False,
                            "enable_websocket": False,
                            "app_verified_required": True,
                            "resource_perm_required": True,
                            "user_verified_required": True,
                        },
                        {
                            "id": 2,
                            "name": "test",
                            "description": "test",
                            "method": "POST",
                            "url": "http://bkapi.example.com/test/",
                            "match_subpath": False,
                            "enable_websocket": False,
                            "app_verified_required": False,
                            "resource_perm_required": False,
                            "user_verified_required": False,
                        },
                    ],
                },
            )
        ],
    )
    def test_list_by_gateway_name(
        self,
        settings,
        mocker,
        request_to_view,
        request_factory,
        fake_gateway,
        stage_name,
        mocked_resources,
        expected,
    ):
        settings.API_RESOURCE_URL_TMPL = "http://bkapi.example.com/{resource_path}"

        get_released_public_resources_mock = mocker.patch(
            "apigateway.apis.open.released.views.ResourceVersionHandler.get_released_public_resources",
            return_value=mocked_resources,
        )

        # fake a stage with name => for get_resource_url_tmpl
        G(Stage, gateway=fake_gateway, status=1, name=stage_name, description="fake description")

        request = request_factory.get("/backend/api/v1/demo/")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request=request,
            view_name="openapi.released.stage_resources_by_gateway_name",
            path_params={"gateway_name": fake_gateway.name, "stage_name": stage_name},
        )
        result = get_response_json(response)

        assert result["code"] == 0, result
        assert result["data"] == expected

        get_released_public_resources_mock.assert_called_once_with(
            fake_gateway.id,
            stage_name=stage_name,
        )
