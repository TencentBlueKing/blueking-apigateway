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

from apigateway.apps.docs.gateway.resource_doc import views
from apigateway.tests.utils.testing import get_response_json


class TestResourceDocViewSet:
    @pytest.mark.parametrize(
        "mocked_api, mocked_resource_doc, mocked_doc, api_name, stage_name, resource_name, expected, will_error",
        [
            (
                {
                    "id": 1,
                    "maintainers": ["admin"],
                },
                {
                    "resource": {
                        "id": 8241,
                        "name": "echo",
                        "description": "",
                        "method": "GET",
                        "path": "/echo/",
                        "match_subpath": False,
                        "is_public": True,
                        "allow_apply_permission": True,
                        "app_verified_required": False,
                        "resource_perm_required": False,
                        "user_verified_required": False,
                    },
                    "doc": {
                        "resource_id": 8241,
                        "type": "markdown",
                        "content": "test",
                        "created_time": "2020-06-10 23:17:00+0800",
                        "updated_time": "2020-11-06 16:11:59+0800",
                    },
                    "resource_url": "http://bking.com/prod/echo/",
                },
                {
                    "type": "markdown",
                    "content": "test",
                    "updated_time": "2020-11-06 16:11:59+0800",
                },
                "api-test",
                "prod",
                "resource_test",
                {
                    "type": "markdown",
                    "content": "test",
                    "updated_time": "2020-11-06 16:11:59",
                },
                False,
            ),
            (
                {
                    "id": 1,
                    "maintainers": ["admin"],
                },
                {
                    "resource": {},
                    "doc": {},
                    "resource_url": "",
                },
                {},
                "api-test",
                "prod",
                "resource_test",
                {},
                True,
            ),
        ],
    )
    def test_list(
        self,
        mocker,
        request_factory,
        mocked_api,
        mocked_resource_doc,
        mocked_doc,
        api_name,
        stage_name,
        resource_name,
        expected,
        will_error,
    ):
        mocked_get_gateway_by_name = mocker.patch(
            "apigateway.apps.docs.gateway.resource_doc.views.support_helper.get_gateway_by_name",
            return_value=mocked_api,
        )
        mocked_get_resource_doc = mocker.patch(
            "apigateway.apps.docs.gateway.resource_doc.views.support_helper.get_resource_doc",
            return_value=mocked_resource_doc,
        )
        mocked_get_doc = mocker.patch(
            "apigateway.apps.docs.gateway.resource_doc.views.ResourceDocHelper.get_doc",
            return_value=mocked_doc,
        )

        request = request_factory.get("")
        view = views.ResourceDocViewSet.as_view({"get": "retrieve"})
        response = view(request, api_name, stage_name, resource_name)
        result = get_response_json(response)

        if will_error:
            assert result["code"] != 0
            return

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_get_gateway_by_name.assert_called_once_with(api_name)
        mocked_get_resource_doc.assert_called_once()
        mocked_get_doc.assert_called_once()
