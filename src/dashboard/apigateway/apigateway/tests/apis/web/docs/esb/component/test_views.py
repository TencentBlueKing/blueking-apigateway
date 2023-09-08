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


class TestComponentSearchApi:
    def test_search(self, mocker, mock_board, request_view):
        mocker.patch(
            "apigateway.apis.web.docs.esb.component.views.ESBChannel.objects.filter_public_components",
            return_value=[
                {
                    "id": 1,
                    "name": "t1",
                    "description": "l1",
                    "system": {
                        "name": "s1",
                    },
                },
            ],
        )

        resp = request_view(
            method="GET",
            view_name="docs.esb.component.search",
            path_params={
                "board": mock_board,
                "system_name": "-",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert isinstance(result["data"], list)


class TestComponentListApi:
    def test_list(self, mocker, mock_board, request_view):
        mock_component = mocker.MagicMock()
        mock_component.configure_mock(
            **{
                "id": 1,
                "name": "t1",
                "description": "l1",
                "permission_level": "normal",
            }
        )

        mocker.patch(
            "apigateway.apis.web.docs.esb.component.views.ESBChannel.objects.filter_public_components",
            return_value=[mock_component],
        )

        resp = request_view(
            method="GET",
            view_name="docs.esb.component.list",
            path_params={
                "board": mock_board,
                "system_name": "foo",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"] == [
            {
                "id": 1,
                "name": "t1",
                "description": "l1",
                "verified_app_required": True,
                "verified_user_required": True,
                "component_permission_required": True,
            }
        ]
