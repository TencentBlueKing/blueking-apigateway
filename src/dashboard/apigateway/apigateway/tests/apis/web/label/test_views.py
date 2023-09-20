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
from ddf import G

from apigateway.apps.label.models import APILabel


class TestGatewayLabelListCreateApi:
    def test_list(self, request_view, fake_gateway):
        G(APILabel, gateway=fake_gateway)
        G(APILabel, gateway=fake_gateway)

        resp = request_view(
            method="GET",
            view_name="label.list_create",
            path_params={"gateway_id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 2

    def test_create(self, request_view, faker, fake_gateway):
        resp = request_view(
            method="POST",
            view_name="label.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data={"name": faker.pystr(min_chars=3)},
        )

        assert resp.status_code == 201


class GatewayLabelRetrieveUpdateDestroyApi:
    def test_retrieve(self, request_view, fake_gateway):
        label = G(APILabel, gateway=fake_gateway)

        resp = request_view(
            method="GET",
            view_name="label.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "id": label.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == label.id

    def test_update(self, request_view, faker, fake_gateway):
        label = G(APILabel, gateway=fake_gateway)

        new_name = faker.pystr(min_chars=3)

        resp = request_view(
            method="PUT",
            view_name="label.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "id": label.id},
            data={"name": new_name},
        )

        assert resp.status_code == 204
        assert APILabel.objects.filter(gateway=fake_gateway, name=new_name).exists()

    def test_destroy(self, request_view, fake_gateway):
        label = G(APILabel, gateway=fake_gateway)

        resp = request_view(
            method="DELETE",
            view_name="label.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id, "id": label.id},
        )

        assert resp.status_code == 204
        assert not APILabel.objects.filter(gateway=fake_gateway).exists()
