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

from apigateway.apps.docs.gateway.gateway import views
from apigateway.tests.utils.testing import get_response_json


class TestGatewayViewSet:
    @pytest.mark.parametrize(
        "mocked_apis, params, expected",
        [
            (
                [
                    {
                        "id": 2,
                        "api_type": 10,
                        "name": "t1",
                        "description": "d1",
                        "maintainers": ["admin"],
                        "user_auth_type": "open",
                    },
                    {
                        "id": 3,
                        "api_type": 1,
                        "name": "t2",
                        "description": "d2",
                        "maintainers": ["admin", "admin2"],
                        "user_auth_type": "open",
                    },
                ],
                {
                    "user_auth_type": "open",
                    "query": "test",
                },
                {
                    "count": 2,
                    "has_next": False,
                    "has_previous": False,
                    "results": [
                        {
                            "id": 3,
                            "name": "t2",
                            "description": "d2",
                            "maintainers": ["admin", "admin2"],
                            "name_prefix": "[官方]",
                            "user_auth_type": "open",
                            "user_auth_type_display": "open",
                            "api_url": "http://t2.example.com",
                        },
                        {
                            "id": 2,
                            "name": "t1",
                            "description": "d1",
                            "maintainers": ["admin"],
                            "name_prefix": "",
                            "user_auth_type": "open",
                            "user_auth_type_display": "open",
                            "api_url": "http://t1.example.com",
                        },
                    ],
                },
            ),
        ],
    )
    def test_list(
        self,
        settings,
        mocker,
        request_factory,
        mocked_apis,
        params,
        expected,
    ):
        settings.BK_API_URL_TMPL = "http://{api_name}.example.com"

        mocked_get_apis = mocker.patch(
            "apigateway.apps.docs.gateway.gateway.views.support_helper.get_gateways",
            return_value=mocked_apis,
        )

        request = request_factory.get("", data=params)
        view = views.GatewayViewSet.as_view({"get": "list"})
        response = view(request)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_get_apis.assert_called_once_with(
            user_auth_type=params.get("user_auth_type"),
            query=params.get("query"),
            fuzzy=True,
        )

    @pytest.mark.parametrize(
        "mocked_api, api_name, will_error, expected",
        [
            (
                {
                    "id": 1,
                    "api_type": 10,
                    "name": "test",
                    "description": "desc",
                    "maintainers": ["admin"],
                    "user_auth_type": "open",
                },
                "test",
                False,
                {
                    "id": 1,
                    "name": "test",
                    "description": "desc",
                    "maintainers": ["admin"],
                    "name_prefix": "",
                    "user_auth_type": "open",
                    "user_auth_type_display": "open",
                    "api_url": "http://test.example.com",
                },
            ),
            (
                {},
                "test",
                True,
                None,
            ),
        ],
    )
    def test_retrieve(
        self,
        settings,
        mocker,
        request_factory,
        mocked_api,
        api_name,
        will_error,
        expected,
    ):
        settings.BK_API_URL_TMPL = "http://{api_name}.example.com"

        mocked_get_gateway_by_name = mocker.patch(
            "apigateway.apps.docs.gateway.gateway.views.support_helper.get_gateway_by_name",
            return_value=mocked_api,
        )

        request = request_factory.get("")
        view = views.GatewayViewSet.as_view({"get": "retrieve"})
        response = view(request, api_name)
        result = get_response_json(response)

        mocked_get_gateway_by_name.assert_called_once_with(api_name)

        if will_error:
            assert response.status_code == 404
            return

        assert response.status_code == 200
        assert result["data"] == expected
