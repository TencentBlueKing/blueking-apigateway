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
from unittest.mock import MagicMock

import pytest

from apigateway.apps.docs.esb.component import views
from apigateway.tests.utils.testing import get_response_json


class TestAPIViewSet:
    @pytest.mark.parametrize(
        "mocked_components, board, params, expected",
        [
            (
                [
                    {
                        "id": 1,
                        "name": "t1",
                        "description": "l1",
                        "system": {
                            "name": "s1",
                        },
                    },
                ],
                "open",
                {
                    "query": "t",
                },
                [
                    {
                        "id": 1,
                        "name": "t1",
                        "description": "l1",
                        "system_name": "s1",
                    },
                ],
            ),
        ],
    )
    def test_search(
        self,
        settings,
        mocker,
        request_factory,
        mocked_components,
        board,
        params,
        expected,
    ):
        settings.ESB_BOARD_CONFIGS = {board: {}}

        mocked_filter_public_components = mocker.patch(
            "apigateway.apps.docs.esb.component.views.ESBChannel.objects.filter_public_components",
            return_value=mocked_components,
        )

        request = request_factory.get("", data=params)
        view = views.ComponentViewSet.as_view({"get": "search"})
        response = view(request, board)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_filter_public_components.assert_called_once_with(
            board,
            query=params.get("query"),
            order_by=("system_id", "name"),
        )

    @pytest.mark.parametrize(
        "mocked_components, board, system_name, expected",
        [
            (
                [
                    {
                        "id": 1,
                        "name": "t1",
                        "description": "l1",
                        "permission_level": "normal",
                    },
                ],
                "open",
                "system-test",
                [
                    {
                        "id": 1,
                        "name": "t1",
                        "description": "l1",
                        "app_verified_required": True,
                        "user_verified_required": True,
                        "component_permission_required": True,
                    },
                ],
            ),
        ],
    )
    def test_list(
        self,
        settings,
        mocker,
        request_factory,
        mocked_components,
        board,
        system_name,
        expected,
    ):
        settings.ESB_BOARD_CONFIGS = {board: {}}

        # mock 数据为字典且包含字段 name，需进行转换，以便 serializer 处理
        # https://docs.python.org/3/library/unittest.mock.html
        new_mocked_components = []
        for c in mocked_components:
            mock = MagicMock()
            mock.configure_mock(**c)
            new_mocked_components.append(mock)

        mocked_filter_public_components = mocker.patch(
            "apigateway.apps.docs.esb.component.views.ESBChannel.objects.filter_public_components",
            return_value=new_mocked_components,
        )

        request = request_factory.get("")
        view = views.ComponentViewSet.as_view({"get": "list"})
        response = view(request, board, system_name)
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"] == expected

        mocked_filter_public_components.assert_called_once_with(
            board,
            system_name=system_name,
            order_by=("name",),
        )
