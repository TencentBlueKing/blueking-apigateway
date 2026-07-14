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
from django_dynamic_fixture import G

from apigateway.apps.audit.constants import OpObjectTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, StageStatusEnum
from apigateway.core.models import Backend, BackendConfig, Stage


def _ai_config():
    return {
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


class TestStageApi:
    def test_create_with_ai_backend(self, request_view, fake_gateway, fake_default_backend):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        ai_backend = G(Backend, gateway=fake_gateway, kind=BackendKindEnum.AI.value, name="openai-primary")
        response = request_view(
            "POST",
            "stage.list-create",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "name": "ai-stage",
                "description": "AI stage",
                "backends": [
                    {
                        "id": fake_default_backend.id,
                        "config": {
                            "type": "node",
                            "timeout": 30,
                            "loadbalance": "roundrobin",
                            "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
                        },
                    },
                    {"id": ai_backend.id, "config": _ai_config()},
                ],
            },
        )

        assert response.status_code == 201, response.json()
        stage = Stage.objects.get(gateway=fake_gateway, name="ai-stage")
        backend_config = BackendConfig.objects.get(stage=stage, backend=ai_backend)
        assert backend_config.config["instances"][0]["options"] == {
            "model": "gpt-4o",
            "temperature": 0.7,
        }

    def test_list(self, request_view, fake_stage, fake_default_backend):
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

    def test_create(self, request_view, fake_gateway, fake_default_backend):
        data = {
            "name": "stage-test",
            "description": "test",
            "backends": [
                {
                    "id": fake_default_backend.id,
                    "config": {
                        "type": "node",
                        "timeout": 1,
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
        backend_config = BackendConfig.objects.filter(
            gateway=fake_gateway, backend=fake_default_backend, stage=stage
        ).first()
        assert backend_config
        assert backend_config.config == {
            "type": "node",
            "timeout": 1,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 1}],
        }

    def test_retrieve(self, request_view, fake_stage, fake_default_backend):
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
                        "timeout": 1,
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
            "timeout": 1,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.test.com", "weight": 1}],
        }

    def test_update_restores_masked_ai_backend_header(self, request_view, fake_stage, fake_backend):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        ai_backend = G(Backend, gateway=fake_stage.gateway, kind=BackendKindEnum.AI.value, name="openai-primary")
        ai_backend_config = BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            stage=fake_stage,
            backend=ai_backend,
            config=_ai_config(),
        )
        ai_config = _ai_config()
        ai_config["instances"][0]["auth"]["header"]["Authorization"] = "xx****yy"

        response = request_view(
            "PUT",
            "stage.retrieve-update-destroy",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
            data={
                "name": fake_stage.name,
                "description": fake_stage.description,
                "backends": [
                    {
                        "id": fake_backend.id,
                        "config": BackendConfig.objects.get(stage=fake_stage, backend=fake_backend).config,
                    },
                    {"id": ai_backend.id, "config": ai_config},
                ],
            },
        )

        assert response.status_code == 204, response.json()
        ai_backend_config.refresh_from_db()
        assert ai_backend_config.config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer secret"

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

    def test_destroy(self, request_view, fake_stage, fake_backend):
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
    def test_retrieve(self, request_view, fake_stage, fake_default_backend):
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
    def test_list_masks_ai_backend_config(self, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        ai_backend = G(
            Backend,
            gateway=fake_stage.gateway,
            kind=BackendKindEnum.AI.value,
            name="openai-primary",
        )
        BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            stage=fake_stage,
            backend=ai_backend,
            config=_ai_config(),
        )

        response = request_view(
            "GET",
            "stage.backend-list",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
        )

        assert response.status_code == 200
        item = next(item for item in response.json()["data"] if item["id"] == ai_backend.id)
        assert item["kind"] == BackendKindEnum.AI.value
        assert item["config"]["instances"][0]["auth"]["header"]["Authorization"] == "Be****et"

    def test_update_ai_backend_preserves_masked_secret_and_masks_audit(self, request_view, fake_stage):
        fake_stage.gateway.kind = GatewayKindEnum.AI.value
        fake_stage.gateway.save()
        ai_backend = G(
            Backend,
            gateway=fake_stage.gateway,
            kind=BackendKindEnum.AI.value,
            name="openai-primary",
        )
        backend_config = BackendConfig.objects.create(
            gateway=fake_stage.gateway,
            stage=fake_stage,
            backend=ai_backend,
            config=_ai_config(),
        )
        data = _ai_config()
        data["instances"][0]["auth"]["header"]["Authorization"] = "xx****yy"

        response = request_view(
            "PUT",
            "stage.backend-retrieve-update",
            path_params={
                "gateway_id": fake_stage.gateway.id,
                "id": fake_stage.id,
                "backend_id": ai_backend.id,
            },
            gateway=fake_stage.gateway,
            data=data,
        )

        assert response.status_code == 204, response.json()
        backend_config.refresh_from_db()
        assert backend_config.config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer secret"
        audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            op_object_id=backend_config.id,
        )
        assert "Be****et" in audit_log.data_before
        assert "Be****et" in audit_log.data_after
        assert "Bearer secret" not in audit_log.data_before
        assert "Bearer secret" not in audit_log.data_after

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
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.example.com", "weight": 100}],
        }

    def test_update(self, request_view, fake_stage, fake_backend):
        data = {
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "www.test.com", "weight": 100}],
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
        mcp_server = G(
            MCPServer, gateway=fake_stage.gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value
        )
        data = {"status": StageStatusEnum.INACTIVE.value}

        response = request_view(
            "PUT",
            "stage.status-update",
            path_params={"gateway_id": fake_stage.gateway.id, "id": fake_stage.id},
            gateway=fake_stage.gateway,
            data=data,
        )
        assert response.status_code == 204
        stage = Stage.objects.get(id=fake_stage.id)
        assert stage.status == StageStatusEnum.INACTIVE.value

        audit_log = AuditEventLog.objects.filter(op_object_id=str(fake_stage.id)).order_by("-id").first()
        assert audit_log.comment == "下架环境"
        mcp_server.refresh_from_db()
        assert mcp_server.status == MCPServerStatusEnum.INACTIVE.value
        mcp_server_audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.MCP_SERVER.value,
            op_object_id=mcp_server.id,
        )
        assert mcp_server_audit_log.comment == "环境停用，同步停用其 MCP Server"
