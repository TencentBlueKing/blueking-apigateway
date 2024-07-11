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
from apigateway.core.models import Backend


def _create(request_view, fake_stage):
    fake_gateway = fake_stage.gateway
    data = {
        "name": "backend-test",
        "description": "test",
        "type": "http",
        "configs": [
            {
                "stage_id": fake_stage.id,
                "type": "node",
                "timeout": 1,
                "loadbalance": "roundrobin",
                "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
            }
        ],
    }

    response = request_view(
        "POST",
        "backend.list-create",
        path_params={"gateway_id": fake_gateway.id},
        gateway=fake_gateway,
        data=data,
    )
    assert response.status_code == 201


class TestBackendApi:
    def test_create(self, request_view, fake_stage):
        _create(request_view, fake_stage)
        backend = Backend.objects.filter(gateway=fake_stage.gateway).first()
        assert backend

    def test_list(self, request_view, fake_stage):
        fake_gateway = fake_stage.gateway

        _create(request_view, fake_stage)

        response = request_view(
            "GET",
            "backend.list-create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["count"] == 1

    def test_retrieve(self, request_view, fake_stage):
        fake_gateway = fake_stage.gateway

        _create(request_view, fake_stage)
        backend = Backend.objects.filter(gateway=fake_stage.gateway).first()
        assert backend

        response = request_view(
            "GET",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == backend.id
        assert len(data["data"]["configs"]) == 1

    def test_update(self, request_view, fake_stage):
        fake_gateway = fake_stage.gateway
        _create(request_view, fake_stage)
        backend = Backend.objects.filter(gateway=fake_stage.gateway).first()
        assert backend
        data = {
            "name": "backend-update",
            "description": "update",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "type": "node",
                    "timeout": 1,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                }
            ],
        }
        response = request_view(
            "PUT",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
            data=data,
        )
        assert response.status_code == 200

        data1 = {
            "name": "backend-update",
            "description": "update",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "type": "node",
                    "timeout": 1,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "https", "host": "www.example1.com", "weight": 1}],
                }
            ],
        }
        response = request_view(
            "PUT",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
            data=data1,
        )
        result = response.json()
        assert result["data"] == {
            "bound_stages": {"id": fake_stage.id, "names": fake_stage.name},
            "updated_stages": {"id": fake_stage.id, "names": fake_stage.name},
        }

    def test_delete(self, request_view, fake_stage):
        fake_gateway = fake_stage.gateway

        _create(request_view, fake_stage)
        backend = Backend.objects.filter(gateway=fake_stage.gateway).first()
        assert backend

        response = request_view(
            "DELETE",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
        )
        assert response.status_code == 204
