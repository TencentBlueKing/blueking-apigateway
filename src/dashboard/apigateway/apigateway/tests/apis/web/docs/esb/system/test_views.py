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
class TestSystemListApi:
    def test_list(self, mocker, faker, request_view):
        mocker.patch(
            "apigateway.apis.web.docs.esb.system.views.SystemDocCategoryHandler.get_system_doc_categories",
            return_value=[
                {
                    "board": "default",
                    "board_label": faker.pystr(),
                    "categories": [
                        {
                            "id": faker.pystr(),
                            "name": faker.pystr(),
                            "systems": [
                                {
                                    "name": faker.pystr(),
                                    "description": faker.pystr(),
                                }
                            ],
                        }
                    ],
                }
            ],
        )

        resp = request_view(
            method="GET",
            view_name="docs.esb.system.list",
            path_params={
                "board": "-",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]


class TestSystemRetrieveApi:
    def test_retrieve(self, mocker, mock_board, request_view):
        mocker.patch(
            "apigateway.apis.web.docs.esb.system.views.ComponentSystem.objects.get_by_name",
            return_value={
                "name": "system-test",
                "description": "desc",
                "comment": "comment",
            },
        )

        resp = request_view(
            method="GET",
            view_name="docs.esb.system.retrieve",
            path_params={
                "board": mock_board,
                "system_name": "foo",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]
