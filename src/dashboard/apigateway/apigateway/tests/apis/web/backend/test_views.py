# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
import logging

import pytest
import requests

from apigateway.core.constants import BackendKindEnum, GatewayKindEnum
from apigateway.core.models import Backend, BackendConfig


def _ai_config(stage_id):
    return {
        "stage_id": stage_id,
        "timeout": 30000,
        "instances": [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 1,
                "auth": {"header": {"Authorization": "Bearer secret"}},
                "options": {"model": "gpt-4o", "temperature": 0.7},
            }
        ],
    }


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
    def test_create_retrieve_and_filter_ai_backend(self, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        response = request_view(
            "POST",
            "backend.list-create",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={
                "name": "openai-primary",
                "description": "OpenAI",
                "kind": BackendKindEnum.AI.value,
                "type": "http",
                "configs": [_ai_config(fake_stage.id)],
            },
        )

        assert response.status_code == 201, response.json()
        backend = Backend.objects.get(gateway=fake_stage.gateway, name="openai-primary")
        assert backend.kind == BackendKindEnum.AI.value
        stored = BackendConfig.objects.get(backend=backend)
        assert stored.config["instances"][0]["auth"]["header"]["Authorization"] == ("Bearer secret")
        assert stored.config["instances"][0]["options"] == {"model": "gpt-4o", "temperature": 0.7}

        response = request_view(
            "GET",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": backend.id},
            gateway=fake_stage.gateway,
        )
        assert response.json()["data"]["kind"] == BackendKindEnum.AI.value
        assert response.json()["data"]["configs"][0]["instances"][0]["auth"]["header"]["Authorization"] == ("Be****et")

        response = request_view(
            "GET",
            "backend.list-create",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"kind": BackendKindEnum.AI.value},
        )
        assert [item["id"] for item in response.json()["data"]["results"]] == [backend.id]

    def test_create_ai_backend_rejects_normal_gateway(self, request_view, fake_stage):
        response = request_view(
            "POST",
            "backend.list-create",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={
                "name": "openai-primary",
                "kind": BackendKindEnum.AI.value,
                "type": "http",
                "configs": [_ai_config(fake_stage.id)],
            },
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        ("incoming_secret", "expected_secret"),
        [("Be****et", "Bearer secret"), ("Bearer new-secret", "Bearer new-secret")],
    )
    def test_update_ai_backend_header(self, request_view, fake_stage, incoming_secret, expected_secret):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        backend = Backend.objects.create(
            gateway=fake_stage.gateway,
            name="openai-primary",
            kind=BackendKindEnum.AI.value,
        )
        BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            backend=backend,
            stage=fake_stage,
            config={key: value for key, value in _ai_config(fake_stage.id).items() if key != "stage_id"},
        )
        config = _ai_config(fake_stage.id)
        config["instances"][0]["auth"]["header"]["Authorization"] = incoming_secret

        response = request_view(
            "PUT",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": backend.id},
            gateway=fake_stage.gateway,
            data={
                "name": backend.name,
                "description": "updated",
                "kind": BackendKindEnum.AI.value,
                "type": "http",
                "configs": [config],
            },
        )

        assert response.status_code == 200, response.json()
        stored = BackendConfig.objects.get(backend=backend)
        assert stored.config["instances"][0]["auth"]["header"]["Authorization"] == expected_secret

    def test_update_ai_backend_does_not_restore_missing_header(self, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        backend = Backend.objects.create(
            gateway=fake_stage.gateway,
            name="openai-compatible",
            kind=BackendKindEnum.AI.value,
        )
        stored_config = _ai_config(fake_stage.id)
        stored_instance = stored_config["instances"][0]
        stored_instance["provider"] = "openai-compatible"
        stored_instance["auth"]["header"] = {"X-Api-Key": "secret"}
        stored_instance["override"] = {"endpoint": "https://example.com/v1"}
        BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            backend=backend,
            stage=fake_stage,
            config={key: value for key, value in stored_config.items() if key != "stage_id"},
        )
        config = _ai_config(fake_stage.id)
        instance = config["instances"][0]
        instance["provider"] = "openai-compatible"
        instance.pop("auth")
        instance["override"] = {"endpoint": "https://example.com/v1"}

        response = request_view(
            "PUT",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": backend.id},
            gateway=fake_stage.gateway,
            data={
                "name": backend.name,
                "description": "updated",
                "kind": BackendKindEnum.AI.value,
                "type": "http",
                "configs": [config],
            },
        )

        assert response.status_code == 200, response.json()
        stored = BackendConfig.objects.get(backend=backend)
        assert "auth" not in stored.config["instances"][0]

    def test_update_rejects_kind_change(self, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        backend = Backend.objects.create(
            gateway=fake_stage.gateway,
            name="openai-primary",
            kind=BackendKindEnum.AI.value,
        )
        BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            backend=backend,
            stage=fake_stage,
            config={key: value for key, value in _ai_config(fake_stage.id).items() if key != "stage_id"},
        )

        response = request_view(
            "PUT",
            "backend.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": backend.id},
            gateway=fake_stage.gateway,
            data={
                "name": backend.name,
                "kind": BackendKindEnum.STANDARD.value,
                "type": "http",
                "configs": [
                    {
                        "stage_id": fake_stage.id,
                        "type": "node",
                        "timeout": 30,
                        "loadbalance": "roundrobin",
                        "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                    }
                ],
            },
        )

        assert response.status_code == 400

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


class TestBackendConnectivityApi:
    @pytest.mark.parametrize(
        ("provider", "expected_url"),
        [
            ("openai", "https://api.openai.com/v1/models"),
            ("deepseek", "https://api.deepseek.com/models"),
        ],
    )
    def test_builtin_provider_returns_model_ids(self, mocker, request_view, fake_stage, provider, expected_url):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        config = _ai_config(fake_stage.id)
        config["instances"][0]["provider"] = provider
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {
            "data": [
                {"id": "model-b"},
                {"id": "model-a"},
            ]
        }

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": config},
        )

        assert response.status_code == 200, response.json()
        assert response.json()["data"] == {"models": ["model-b", "model-a"]}
        request_get.assert_called_once_with(
            expected_url,
            headers={"Authorization": "Bearer secret"},
            timeout=(10, 30.0),
            allow_redirects=False,
        )

    def test_openai_compatible_uses_custom_models_endpoint(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        config = _ai_config(fake_stage.id)
        instance = config["instances"][0]
        instance["provider"] = "openai-compatible"
        instance["auth"]["header"] = {
            "X-Api-Key": "secret",
            "Host": "internal.example",
            "Content-Length": "999",
        }
        instance["override"] = {"endpoint": "https://models.example.com/v1/chat/completions?api-version=2026-01-01"}
        mocker.patch(
            "socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("8.8.8.8", 443))],
        )
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {"data": [{"id": "custom-model"}]}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": config},
        )

        assert response.status_code == 200, response.json()
        request_get.assert_called_once_with(
            "https://models.example.com/v1/models?api-version=2026-01-01",
            headers={"X-Api-Key": "secret"},
            timeout=(10, 30.0),
            allow_redirects=False,
        )

    def test_custom_provider_rejects_link_local_resolved_address(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        config = _ai_config(fake_stage.id)
        instance = config["instances"][0]
        instance["provider"] = "openai-compatible"
        instance["override"] = {"endpoint": "https://models.example.com/v1/chat/completions"}
        mocker.patch(
            "socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("169.254.169.254", 443))],
        )
        request_get = mocker.patch("requests.get")

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": config},
        )

        assert response.status_code == 500
        request_get.assert_not_called()

    def test_custom_provider_allows_private_resolved_address(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        config = _ai_config(fake_stage.id)
        instance = config["instances"][0]
        instance["provider"] = "openai-compatible"
        instance["override"] = {"endpoint": "https://models.internal.example/v1/chat/completions"}
        mocker.patch(
            "socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("10.0.0.1", 443))],
        )
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {"data": [{"id": "internal-model"}]}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": config},
        )

        assert response.status_code == 200, response.json()
        request_get.assert_called_once()

    def test_custom_provider_allows_public_ipv6_address(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        config = _ai_config(fake_stage.id)
        instance = config["instances"][0]
        instance["provider"] = "openai-compatible"
        instance["override"] = {"endpoint": "https://models.example.com/v1/chat/completions"}
        mocker.patch(
            "socket.getaddrinfo",
            return_value=[(10, 1, 6, "", ("2001:4860:4860::abcd", 443, 0, 0))],
        )
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {"data": [{"id": "ipv6-model"}]}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": config},
        )

        assert response.status_code == 200, response.json()
        request_get.assert_called_once()

    def test_connectivity_timeout_is_capped(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        config = _ai_config(fake_stage.id)
        config["timeout"] = 300000
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {"data": []}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": config},
        )

        assert response.status_code == 200, response.json()
        assert request_get.call_args.kwargs["timeout"] == (10, 30)

    def test_existing_backend_restores_masked_header(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        backend = Backend.objects.create(
            gateway=fake_stage.gateway,
            name="openai-primary",
            kind=BackendKindEnum.AI.value,
        )
        BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            backend=backend,
            stage=fake_stage,
            config={key: value for key, value in _ai_config(fake_stage.id).items() if key != "stage_id"},
        )
        config = _ai_config(fake_stage.id)
        config["instances"][0]["auth"]["header"]["Authorization"] = "Be****et"
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {"data": [{"id": "gpt-4o"}]}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"backend_id": backend.id, "config": config},
        )

        assert response.status_code == 200, response.json()
        assert request_get.call_args.kwargs["headers"] == {"Authorization": "Bearer secret"}

    def test_existing_backend_reports_corrupted_config(self, caplog, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        backend = Backend.objects.create(
            gateway=fake_stage.gateway,
            name="openai-primary",
            kind=BackendKindEnum.AI.value,
        )
        ciphertext = "backend-connectivity-ciphertext-sentinel"
        BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            backend=backend,
            stage=fake_stage,
            _config={"encrypted": ciphertext},
        )

        with caplog.at_level(logging.ERROR):
            response = request_view(
                "POST",
                "backend.test-connectivity",
                path_params={"gateway_id": fake_stage.gateway.id},
                gateway=fake_stage.gateway,
                data={"backend_id": backend.id, "config": _ai_config(fake_stage.id)},
            )

        assert response.status_code == 400
        assert "已有后端配置无法读取" in str(response.json())
        assert ciphertext not in caplog.text

    def test_rejects_normal_gateway_without_requesting_provider(self, mocker, request_view, fake_stage):
        request_get = mocker.patch("requests.get")

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": _ai_config(fake_stage.id)},
        )

        assert response.status_code == 400
        request_get.assert_not_called()

    def test_provider_failure_does_not_expose_credentials(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        request_get = mocker.patch(
            "requests.get",
            side_effect=requests.ConnectionError("Authorization: Bearer secret"),
        )

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": _ai_config(fake_stage.id)},
        )

        assert response.status_code == 500
        assert "Bearer secret" not in str(response.json())
        request_get.assert_called_once()

    def test_provider_redirect_is_rejected(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 302
        request_get.return_value.json.return_value = {"data": [{"id": "redirected-model"}]}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": _ai_config(fake_stage.id)},
        )

        assert response.status_code == 500

    def test_rejects_malformed_provider_response(self, mocker, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        request_get = mocker.patch("requests.get")
        request_get.return_value.status_code = 200
        request_get.return_value.json.return_value = {"data": [{"name": "missing-id"}]}

        response = request_view(
            "POST",
            "backend.test-connectivity",
            path_params={"gateway_id": fake_stage.gateway.id},
            gateway=fake_stage.gateway,
            data={"config": _ai_config(fake_stage.id)},
        )

        assert response.status_code == 500


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
                        "active": {
                            "type": "http",
                            "http_path": "/health",
                            "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
                        },
                        "passive": {
                            "type": "http",
                            "healthy": {"successes": 2, "http_statuses": [200]},
                            "unhealthy": {"http_failures": 3, "http_statuses": [500, 502]},
                        },
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
