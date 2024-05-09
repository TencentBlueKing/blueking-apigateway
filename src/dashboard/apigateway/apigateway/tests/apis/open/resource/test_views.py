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


class TestResourceSyncApi:
    def test_sync(
        self, request_view, fake_gateway, fake_backend, mocker, fake_resource_swagger, ignore_related_app_permission
    ):
        mocker.patch(
            "apigateway.apis.open.resource.views.ResourcesImporter.from_resources",
            return_value=mocker.MagicMock(
                get_selected_resource_data_list=mocker.MagicMock(
                    return_value=[
                        mocker.MagicMock(
                            resource=mocker.MagicMock(id=1),
                            metadata={"is_created": True},
                        ),
                        mocker.MagicMock(
                            resource=mocker.MagicMock(id=2),
                            metadata={"is_created": False},
                        ),
                    ]
                ),
                get_deleted_resources=mocker.MagicMock(return_value=[{"id": 3}]),
            ),
        )

        resp = request_view(
            method="POST",
            view_name="openapi.resource.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "content": fake_resource_swagger,
                "delete": True,
            },
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
        assert result["data"] == {
            "added": [{"id": 1}],
            "updated": [{"id": 2}],
            "deleted": [{"id": 3}],
        }
