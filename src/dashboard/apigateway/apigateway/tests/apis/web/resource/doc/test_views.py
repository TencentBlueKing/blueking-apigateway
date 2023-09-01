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
class TestDocListCreateApi:
    def test_list(self, request_view, fake_resource_doc):
        fake_gateway = fake_resource_doc.gateway

        resp = request_view(
            method="GET",
            view_name="resource_doc.list_create",
            path_params={"gateway_id": fake_gateway.id, "resource_id": fake_resource_doc.resource_id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 2

    def test_create(self, request_view, fake_resource, faker):
        fake_gateway = fake_resource.api

        resp = request_view(
            method="POST",
            view_name="resource_doc.list_create",
            path_params={"gateway_id": fake_gateway.id, "resource_id": fake_resource.id},
            data={
                "language": "zh",
                "content": faker.pystr(),
            },
        )
        result = resp.json()

        assert resp.status_code == 201
        assert result["data"]["id"] != 0


class TestDocUpdateDestroyApi:
    def test_update(self, request_view, fake_resource_doc, faker):
        fake_gateway = fake_resource_doc.gateway

        resp = request_view(
            method="PUT",
            view_name="resource_doc.update_destroy",
            path_params={
                "gateway_id": fake_gateway.id,
                "resource_id": fake_resource_doc.resource_id,
                "id": fake_resource_doc.id,
            },
            data={
                "language": "zh",
                "content": faker.pystr(),
            },
        )
        assert resp.status_code == 200

    def test_destroy(self, request_view, fake_resource_doc):
        fake_gateway = fake_resource_doc.gateway

        resp = request_view(
            method="DELETE",
            view_name="resource_doc.update_destroy",
            path_params={
                "gateway_id": fake_gateway.id,
                "resource_id": fake_resource_doc.resource_id,
                "id": fake_resource_doc.id,
            },
        )
        assert resp.status_code == 204
