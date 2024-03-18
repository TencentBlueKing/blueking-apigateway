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
from apigateway.core.models import BackendConfig, Stage


class TestStageApi:
    def test_list(self, request_view, fake_stage):
        fake_gateway = fake_stage.gateway

        response = request_view(
            "GET",
            "stage.list-create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    def test_create(self, request_view, fake_gateway, fake_backend):
        data = {
            "name": "stage-test",
            "description": "test",
            "backends": [
                {
                    "id": fake_backend.id,
                    "config": {
                        "type": "node",
                        "timeout": {"connect": 1, "read": 1, "send": 1},
                        "loadbalance": "roundrobin",
                        "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                    },
                }
            ],
        }

        response = request_view(
            "POST",
            "stage.list-create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data=data,
        )
        assert response.status_code == 201
        stage = Stage.objects.filter(gateway=fake_gateway, name="stage-test").first()
        assert stage
        backend_config = BackendConfig.objects.filter(gateway=fake_gateway, backend=fake_backend, stage=stage).first()
        assert backend_config
        assert backend_config.config == {
            "type": "node",
            "timeout": {"connect": 1, "read": 1, "send": 1},
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
            "retries": 0,
            "retry_timeout": 0,
        }

    def test_retrieve(self, request_view, fake_stage):
        response = request_view(
            "GET",
            "stage.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == fake_stage.name

    def test_update(self, request_view, fake_stage, fake_backend):
        data = {
            "name": "stage-update",
            "description": "test",
            "backends": [
                {
                    "id": fake_backend.id,
                    "config": {
                        "type": "node",
                        "timeout": {"connect": 1, "read": 1, "send": 1},
                        "loadbalance": "roundrobin",
                        "hosts": [{"scheme": "http", "host": "www.test.com", "weight": 1}],
                    },
                }
            ],
        }

        response = request_view(
            "PUT",
            "stage.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
            data=data,
        )
        assert response.status_code == 204
        stage = Stage.objects.get(id=fake_stage.id)
        backend_config = BackendConfig.objects.get(stage=stage)
        assert backend_config.config == {
            "type": "node",
            "timeout": {"connect": 1, "read": 1, "send": 1},
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.test.com", "weight": 1}],
            "retries": 0,
            "retry_timeout": 0,
        }

    def partial_update(self, request_view, fake_stage):
        data = {"description": "partial_update"}

        response = request_view(
            "PATCH",
            "stage.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
            data=data,
        )
        assert response.status_code == 200
        stage = Stage.objects.get(id=fake_stage.id)
        assert stage.description == "partial_update"

    def test_destroy(self, request_view, fake_stage):
        response = request_view(
            "DELETE",
            "stage.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
        )
        assert response.status_code == 400
        fake_stage.status = 0
        fake_stage.save()
        response = request_view(
            "DELETE",
            "stage.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
        )
        assert response.status_code == 204
        assert not Stage.objects.filter(id=fake_stage.id).exists()


class TestStageVarsApi:
    def test_retrieve(self, request_view, fake_stage):
        fake_stage.vars = {
            "key1": "value1",
        }
        fake_stage.save()

        response = request_view(
            "GET",
            "stage.vars-retrieve-update",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["vars"] == {
            "key1": "value1",
        }

    def test_update(self, request_view, fake_stage):
        data = {
            "vars": {
                "key1": "value1",
                "key2": "value2",
            }
        }

        response = request_view(
            "PUT",
            "stage.vars-retrieve-update",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
            data=data,
        )
        assert response.status_code == 204
        stage = Stage.objects.get(id=fake_stage.id)
        assert stage.vars == {
            "key1": "value1",
            "key2": "value2",
        }


class TestStageBackendApi:
    def test_list(self, request_view, fake_stage, fake_backend):
        response = request_view(
            "GET",
            "stage.backend-list",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1

    def test_retrieve(self, request_view, fake_stage, fake_backend):
        response = request_view(
            "GET",
            "stage.backend-retrieve-update",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id, "backend_id": fake_backend.id},
            gateway=fake_stage.gateway,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["config"] == {
            "type": "node",
            "timeout": {"connect": 30, "read": 30, "send": 30},
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
            "retries": 0,
            "retry_timeout": 0,
        }

    def test_update(self, request_view, fake_stage, fake_backend):
        data = {
            "type": "node",
            "timeout": {"connect": 30, "read": 30, "send": 30},
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.test.com", "weight": 100}],
            "retries": 0,
            "retry_timeout": 0,
        }

        response = request_view(
            "PUT",
            "stage.backend-retrieve-update",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id, "backend_id": fake_backend.id},
            gateway=fake_stage.gateway,
            data=data,
        )
        assert response.status_code == 204
        backend_config = BackendConfig.objects.get(stage=fake_stage, backend=fake_backend)
        assert backend_config.config == data


class TestStageStatusUpdateApi:
    def test_update(self, request_view, fake_stage):
        data = {"status": 0}

        response = request_view(
            "PUT",
            "stage.status-update",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
            data=data,
        )
        assert response.status_code == 204
        stage = Stage.objects.get(id=fake_stage.id)
        assert stage.status == 0
