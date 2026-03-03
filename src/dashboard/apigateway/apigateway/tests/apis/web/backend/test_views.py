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
            "bound_stages": [{"id": fake_stage.id, "name": fake_stage.name}],
            "updated_stages": [],
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


class TestBackendHealthCheckApi:
    """Test backend CRUD operations with health check configuration"""

    def test_create_with_active_health_check(self, request_view, fake_stage):
        """Test creating a backend with active health check"""
        fake_gateway = fake_stage.gateway
        data = {
            "name": "backend-health-chk",
            "description": "test health check",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "type": "node",
                    "timeout": 30,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                    "checks": {
                        "active": {
                            "type": "http",
                            "http_path": "/health",
                            "timeout": 5,
                            "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
                            "unhealthy": {"interval": 5, "http_failures": 3, "http_statuses": [500, 502]},
                        }
                    },
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

        # Verify backend was created with health check config
        backend = Backend.objects.filter(gateway=fake_gateway, name="backend-health-chk").first()
        assert backend is not None

    def test_retrieve_with_health_check(self, request_view, fake_stage):
        """Test retrieving a backend with health check returns checks field"""
        fake_gateway = fake_stage.gateway

        # Create backend with health check
        data = {
            "name": "backend-retrieve",
            "description": "test",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "type": "node",
                    "timeout": 30,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                    "checks": {
                        "passive": {
                            "type": "http",
                            "healthy": {"successes": 2, "http_statuses": [200]},
                            "unhealthy": {"http_failures": 3, "http_statuses": [500, 502]},
                        }
                    },
                }
            ],
        }

        create_response = request_view(
            "POST",
            "backend.list-create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data=data,
        )
        assert create_response.status_code == 201

        backend = Backend.objects.filter(gateway=fake_gateway, name="backend-retrieve").first()
        assert backend is not None

        # Retrieve the backend
        response = request_view(
            "GET",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
        )
        assert response.status_code == 200

        # Verify response contains checks field
        response_data = response.json()
        assert response_data["data"]["id"] == backend.id
        assert len(response_data["data"]["configs"]) == 1

        config = response_data["data"]["configs"][0]
        assert "checks" in config
        assert "passive" in config["checks"]
        assert config["checks"]["passive"]["type"] == "http"
        assert config["checks"]["passive"]["healthy"]["successes"] == 2
        assert config["checks"]["passive"]["unhealthy"]["http_failures"] == 3

    def test_update_health_check(self, request_view, fake_stage):
        """Test updating a backend's health check configuration"""
        fake_gateway = fake_stage.gateway

        # Create backend without health check
        data = {
            "name": "backend-update-check",
            "description": "test",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "type": "node",
                    "timeout": 30,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                }
            ],
        }

        create_response = request_view(
            "POST",
            "backend.list-create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data=data,
        )
        assert create_response.status_code == 201

        backend = Backend.objects.filter(gateway=fake_gateway, name="backend-update-check").first()
        assert backend is not None

        # Update backend to add health check
        update_data = {
            "name": "backend-update-check",
            "description": "test with health check",
            "type": "http",
            "configs": [
                {
                    "stage_id": fake_stage.id,
                    "type": "node",
                    "timeout": 30,
                    "loadbalance": "roundrobin",
                    "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
                    "checks": {
                        "active": {
                            "type": "http",
                            "http_path": "/healthz",
                            "timeout": 3,
                            "healthy": {"interval": 5, "successes": 1},
                        }
                    },
                }
            ],
        }

        update_response = request_view(
            "PUT",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
            data=update_data,
        )
        assert update_response.status_code == 200

        # Retrieve and verify health check was added
        retrieve_response = request_view(
            "GET",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_gateway.id, "id": backend.id},
            gateway=fake_gateway,
        )
        assert retrieve_response.status_code == 200

        response_data = retrieve_response.json()
        config = response_data["data"]["configs"][0]
        assert "checks" in config
        assert "active" in config["checks"]
        assert config["checks"]["active"]["http_path"] == "/healthz"
        assert config["checks"]["active"]["timeout"] == 3
