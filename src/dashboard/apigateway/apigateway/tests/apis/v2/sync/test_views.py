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

import json

import pytest
from ddf import G
from django.conf import settings

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.data_plane.models import DataPlane
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerCategory
from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, ResourceKindEnum
from apigateway.core.models import (
    Backend,
    BackendConfig,
    Gateway,
    GatewayRelatedApp,
    Proxy,
    Resource,
    ResourceVersion,
    Stage,
)
from apigateway.service.gateway_jwt import GatewayJWTHandler
from apigateway.service.resource_version import make_resource_schema_version
from apigateway.utils.yaml import yaml_loads


@pytest.fixture()
def disable_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


def _model_backend(name="openai-primary"):
    return {
        "name": name,
        "config": {
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
        },
    }


class TestSyncApi:
    def test_resource_sync_ai_resource(self, request_view, fake_gateway, disable_app_permission):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        backend = G(Backend, gateway=fake_gateway, name="openai-primary", kind=BackendKindEnum.AI.value)
        content = json.dumps(
            {
                "swagger": "2.0",
                "basePath": "/",
                "info": {"version": "0.1", "title": "AI Gateway"},
                "schemes": ["http"],
                "paths": {
                    "/chat": {
                        "post": {
                            "operationId": "chat",
                            "x-bk-apigateway-resource": {
                                "kind": "ai",
                                "backend": {"name": backend.name},
                            },
                        }
                    }
                },
            }
        )

        response = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.resources.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"content": content, "delete": False},
        )

        assert response.status_code == 200, response.json()
        resource = Resource.objects.get(gateway=fake_gateway, name="chat")
        assert resource.kind == ResourceKindEnum.AI.value
        assert Proxy.objects.get(resource=resource).config == {}

    def test_stage_sync_ai_gateway_with_ai_backends_only(self, request_view, fake_gateway, disable_app_permission):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"name": "prod", "description": "desc", "vars": {}, "ai_backends": [_model_backend()]},
        )

        assert resp.status_code == 200, resp.json()
        backend = Backend.objects.get(gateway=fake_gateway, name="openai-primary")
        assert backend.kind == BackendKindEnum.AI.value
        backend_config = BackendConfig.objects.get(backend=backend, stage__name="prod")
        assert backend_config.config["instances"][0]["auth"]["header"]["Authorization"] == "Bearer secret"
        assert backend_config.config["instances"][0]["options"] == {"model": "gpt-4o", "temperature": 0.7}

    def test_stage_sync_normal_gateway_rejects_ai_backends(self, request_view, fake_gateway, disable_app_permission):
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "backends": [
                    {
                        "name": "default",
                        "config": {
                            "timeout": 30,
                            "loadbalance": "roundrobin",
                            "hosts": [{"host": "http://example.com"}],
                        },
                    }
                ],
                "ai_backends": [_model_backend()],
            },
        )

        assert resp.status_code == 400
        assert not Stage.objects.filter(gateway=fake_gateway, name="prod").exists()

    def test_stage_sync_ai_gateway_omitted_ai_backends_remain_unchanged(
        self, request_view, fake_gateway, disable_app_permission
    ):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        initial = {
            "name": "prod",
            "description": "desc",
            "vars": {},
            "ai_backends": [_model_backend()],
        }
        first = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data=initial,
        )
        assert first.status_code == 200, first.json()
        model_config = BackendConfig.objects.get(backend__name="openai-primary", stage__name="prod")
        stored_config = model_config.config

        second = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "updated",
                "vars": {},
                "backends": [
                    {
                        "name": "service1",
                        "config": {
                            "timeout": 30,
                            "loadbalance": "roundrobin",
                            "hosts": [{"host": "http://example.com"}],
                        },
                    }
                ],
            },
        )

        assert second.status_code == 200, second.json()
        model_config.refresh_from_db()
        assert model_config.config == stored_config

    def test_stage_sync_ai_backend_treats_masked_value_as_plaintext_and_masks_audit(
        self, request_view, fake_gateway, fake_admin_user, disable_app_permission
    ):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        initial = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "ai_backends": [_model_backend()],
            },
            user=fake_admin_user,
        )
        assert initial.status_code == 200, initial.json()
        model_backend = _model_backend()
        model_backend["config"]["instances"][0]["auth"]["header"]["Authorization"] = "xx****yy"
        model_backend["config"]["instances"][0]["options"]["model"] = "gpt-4o-mini"

        updated = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "ai_backends": [model_backend],
            },
            user=fake_admin_user,
        )

        assert updated.status_code == 200, updated.json()
        backend_config = BackendConfig.objects.get(backend__name="openai-primary", stage__name="prod")
        assert backend_config.config["instances"][0]["auth"]["header"]["Authorization"] == "xx****yy"
        audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            comment="OpenAPI 同步更新环境后端配置",
        )
        assert "Be****et" in audit_log.data_before
        assert "xx****yy" in audit_log.data_after
        assert "Bearer secret" not in audit_log.data_before
        assert "Bearer secret" not in audit_log.data_after

    def test_stage_sync_ai_backend_records_secret_change_with_same_mask(
        self, request_view, fake_gateway, fake_admin_user, disable_app_permission
    ):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        initial = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"name": "prod", "description": "desc", "vars": {}, "ai_backends": [_model_backend()]},
            user=fake_admin_user,
        )
        assert initial.status_code == 200, initial.json()
        model_backend = _model_backend()
        model_backend["config"]["instances"][0]["auth"]["header"]["Authorization"] = "Bearer closet"

        updated = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"name": "prod", "description": "desc", "vars": {}, "ai_backends": [model_backend]},
            user=fake_admin_user,
        )

        assert updated.status_code == 200, updated.json()
        audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            comment="OpenAPI 同步更新环境后端配置",
        )
        assert "Be****et" in audit_log.data_before
        assert "Be****et" in audit_log.data_after
        assert "Bearer secret" not in audit_log.data_before
        assert "Bearer closet" not in audit_log.data_after

    def test_stage_sync_ai_gateway_rejects_empty_ai_backends(self, request_view, fake_gateway, disable_app_permission):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"name": "prod", "description": "desc", "vars": {}, "ai_backends": []},
        )

        assert resp.status_code == 400
        assert not Stage.objects.filter(gateway=fake_gateway, name="prod").exists()

    def test_stage_sync_rolls_back_standard_backend_when_model_backend_name_conflicts(
        self, request_view, fake_gateway, disable_app_permission
    ):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        name = "shared-name"

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "backends": [
                    {
                        "name": name,
                        "config": {
                            "timeout": 30,
                            "loadbalance": "roundrobin",
                            "hosts": [{"host": "http://example.com"}],
                        },
                    }
                ],
                "ai_backends": [_model_backend(name)],
            },
        )

        assert resp.status_code == 400
        assert not Stage.objects.filter(gateway=fake_gateway, name="prod").exists()
        assert not Backend.objects.filter(gateway=fake_gateway, name=name).exists()

    def test_gateway_sync_creates_ai_gateway(
        self, mocker, request_view, unique_gateway_name, disable_app_permission, default_data_plane
    ):
        response = request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.sync",
            path_params={"gateway_name": unique_gateway_name},
            data={"kind": "ai"},
            app=mocker.MagicMock(app_code="foo"),
        )

        assert response.status_code == 200, response.json()
        assert Gateway.objects.get(name=unique_gateway_name).kind == GatewayKindEnum.AI.value

    def test_gateway_sync_ai_gateway_rejects_older_default_data_plane(
        self, mocker, request_view, unique_gateway_name, disable_app_permission, default_data_plane
    ):
        DataPlane.objects.filter(id=default_data_plane.id).update(apisix_version="3.13")

        response = request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.sync",
            path_params={"gateway_name": unique_gateway_name},
            data={"kind": "ai"},
            app=mocker.MagicMock(app_code="foo"),
        )

        assert response.status_code == 400
        assert "APISIX 3.16 or later" in response.json()["error"]["message"]
        assert not Gateway.objects.filter(name=unique_gateway_name).exists()

    def test_gateway_sync_ignores_kind_when_updating(
        self, mocker, request_view, fake_gateway, disable_app_permission, default_data_plane
    ):
        fake_gateway.name = "update-ai-kind"
        fake_gateway.save()
        GatewayHandler.save_auth_config(fake_gateway.id, user_auth_type="default")
        response = request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={"kind": "ai"},
            gateway=fake_gateway,
            app=mocker.MagicMock(app_code="foo"),
        )

        assert response.status_code == 200, response.json()
        fake_gateway.refresh_from_db()
        assert fake_gateway.kind == GatewayKindEnum.NORMAL.value

    def test_gateway_public_key_retrieve_from_dashboard_backend(
        self, settings, request_view, fake_gateway, disable_app_permission
    ):
        settings.JWT_ISSUER = "foo"
        jwt = GatewayJWTHandler.create_jwt(fake_gateway)

        resp = request_view(
            method="GET",
            view_name="openapi.v2.sync.gateway.public_key.retrieve",
            path_params={"gateway_name": fake_gateway.name},
            gateway=fake_gateway,
        )

        assert resp.status_code == 200
        assert resp.json()["data"] == {
            "issuer": "foo",
            "public_key": jwt.public_key,
        }

    def test_gateway_related_apps_add_records_related_app_codes_before_and_after(
        self, mocker, request_view, fake_admin_user, fake_gateway, disable_app_permission
    ):
        G(GatewayRelatedApp, gateway=fake_gateway, bk_app_code="app1")
        mocker.patch(
            "apigateway.apis.v2.sync.views.get_app_tenant_info", return_value=("single", fake_gateway.tenant_id)
        )
        record_gateway_op_success = mocker.patch("apigateway.apis.v2.sync.views.Auditor.record_gateway_op_success")

        resp = request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.add_related_apps",
            path_params={"gateway_name": fake_gateway.name},
            data={"related_app_codes": ["app1", "app2"]},
            gateway=fake_gateway,
            user=fake_admin_user,
        )

        assert resp.status_code == 201
        record_gateway_op_success.assert_called_once()
        assert record_gateway_op_success.call_args.kwargs["data_before"] == {"related_app_codes": ["app1"]}
        assert sorted(record_gateway_op_success.call_args.kwargs["data_after"]["related_app_codes"]) == [
            "app1",
            "app2",
        ]

    @pytest.mark.parametrize(
        "gray_stage, expected_count",
        [
            ("start", 2),
            ("done", 1),
            ("not_start", 1),
        ],
    )
    def test_gateway_sync_with_empty_data_planes_use_sync_rule_for_te_bp_gateway(
        self,
        mocker,
        request_view,
        fake_gateway,
        disable_app_permission,
        default_data_plane,
        gray_stage,
        expected_count,
    ):
        settings.EDITION = "te"
        settings.BK_PLUGINS_DATA_PLANE_NAME = "bp"
        settings.BK_PLUGINS_DATA_PLANE_GRAY_STAGE = gray_stage
        bp_data_plane = G(DataPlane, name="bp")
        mock_saver_cls = mocker.patch("apigateway.biz.gateway.gateway.GatewaySaver")
        mock_saver_cls.return_value.save.return_value = fake_gateway

        gateway_name = "bp-sync-gateway"
        resp = request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.sync",
            path_params={"gateway_name": gateway_name},
            data={
                "description": "desc",
                "is_public": True,
                "allow_delete_sensitive_params": False,
            },
            app=mocker.MagicMock(app_code="foo"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result.get("error") is None
        data_plane_ids = mock_saver_cls.call_args.kwargs["data_plane_ids"]
        assert len(data_plane_ids) == expected_count
        if gray_stage == "done":
            assert set(data_plane_ids) == {bp_data_plane.id}
        elif gray_stage == "start":
            assert set(data_plane_ids) == {default_data_plane.id, bp_data_plane.id}
        else:
            assert set(data_plane_ids) == {default_data_plane.id}

    def test_stage_sync_does_not_create_empty_config_for_omitted_backend(
        self, request_view, fake_gateway, disable_app_permission
    ):
        fake_gateway.name = "test-stage-sync"
        fake_gateway.save()
        omitted_backend = G(Backend, gateway=fake_gateway, name="service2")

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "backends": [
                    {
                        "name": "service1",
                        "config": {
                            "timeout": 60,
                            "loadbalance": "roundrobin",
                            "hosts": [{"host": "http://www.a.com"}],
                        },
                    }
                ],
            },
        )

        assert resp.status_code == 200
        stage = Stage.objects.get(gateway=fake_gateway, name="prod")
        assert resp.json()["data"] == {"id": stage.id, "name": stage.name}
        assert not BackendConfig.objects.filter(backend=omitted_backend, stage__name="prod").exists()

    def test_stage_sync_with_empty_backends_returns_error(self, request_view, fake_gateway, disable_app_permission):
        fake_gateway.name = "test-stage-sync-empty-backends"
        fake_gateway.save()

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": "prod",
                "description": "desc",
                "vars": {},
                "backends": [],
            },
        )

        assert resp.status_code == 400
        assert "backends" in str(resp.json()["error"])

    def test_stage_sync_records_stage_backend_audit(
        self, request_view, fake_admin_user, fake_gateway, fake_stage, fake_backend, disable_app_permission
    ):
        fake_gateway.name = "test-stage-sync-stage-backend-audit"
        fake_gateway.save()
        fake_stage.name = "prod"
        fake_stage.save()
        fake_backend.name = "default"
        fake_backend.save()
        backend_config = BackendConfig.objects.get(gateway=fake_gateway, stage=fake_stage, backend=fake_backend)
        data_before = backend_config.config

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.sync",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "name": fake_stage.name,
                "description": "desc",
                "vars": {},
                "backends": [
                    {
                        "name": fake_backend.name,
                        "config": {
                            "timeout": 60,
                            "loadbalance": "roundrobin",
                            "hosts": [{"host": "http://new.example.com"}],
                        },
                    }
                ],
            },
            user=fake_admin_user,
        )

        assert resp.status_code == 200
        audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.STAGE_BACKEND.value,
            comment="OpenAPI 同步更新环境后端配置",
        )
        assert audit_log.username == "admin"
        assert audit_log.op_type == OpTypeEnum.MODIFY.value
        assert audit_log.op_object == "prod:default"
        assert audit_log.op_object_id == str(backend_config.id)
        assert json.loads(audit_log.data_before) == data_before
        assert json.loads(audit_log.data_after) == {
            "type": "node",
            "timeout": 60,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "new.example.com", "weight": 100}],
        }

    def test_resource_version_create_returns_created_info(
        self, mocker, request_view, fake_gateway, fake_admin_user, disable_app_permission
    ):
        resource_version = mocker.Mock(id=123, version="1.1.0")
        create_resource_version_with_artifacts = mocker.patch(
            "apigateway.apis.v2.sync.views.ResourceVersionArtifactHandler.create_resource_version_with_artifacts",
            return_value=resource_version,
        )

        resp = request_view(
            method="POST",
            view_name="openapi.v2.sync.resource_versions.list_create",
            gateway=fake_gateway,
            path_params={"gateway_name": fake_gateway.name},
            data={"version": "1.1.0", "comment": "release comment"},
            user=fake_admin_user,
        )

        assert resp.status_code == 200
        assert resp.json()["data"] == {"id": 123, "version": "1.1.0"}
        create_resource_version_with_artifacts.assert_called_once()

    def test_resource_version_create_with_ai_resource(
        self, request_view, fake_gateway, fake_backend, fake_resource, fake_admin_user, disable_app_permission
    ):
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        fake_backend.kind = BackendKindEnum.AI.value
        fake_backend.save()
        fake_resource.kind = ResourceKindEnum.AI.value
        fake_resource.method = "POST"
        fake_resource.match_subpath = False
        fake_resource.enable_websocket = False
        fake_resource.save()
        proxy = Proxy.objects.get(resource=fake_resource)
        Proxy.objects.filter(id=proxy.id).update(_config="{}")

        resp = request_view(
            method="POST",
            view_name="openapi.v2.sync.resource_versions.list_create",
            gateway=fake_gateway,
            path_params={"gateway_name": fake_gateway.name},
            data={"version": "1.2.0", "comment": "AI resource version"},
            user=fake_admin_user,
        )

        assert resp.status_code == 200
        resource_version = ResourceVersion.objects.get(gateway=fake_gateway, version="1.2.0")
        resource = resource_version.data[0]
        assert resource["kind"] == ResourceKindEnum.AI.value
        assert resource["proxy"]["backend_id"] == fake_backend.id
        assert json.loads(resource["proxy"]["config"]) == {}
        artifact = OpenAPIFileResourceSchemaVersion.objects.get(resource_version=resource_version)
        operation = yaml_loads(artifact.schema)["paths"][fake_resource.path]["post"]
        assert operation["x-bk-apigateway-resource"]["kind"] == ResourceKindEnum.AI.value

    def test_resource_version_release_preserves_stage_id_order(
        self, faker, mocker, request_view, fake_admin_user, fake_gateway, disable_app_permission
    ):
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        stage_1 = G(Stage, gateway=fake_gateway)
        stage_2 = G(Stage, gateway=fake_gateway)
        release_to_stages = mocker.patch("apigateway.apis.v2.sync.views.ReleaseHandler.release_to_stages")
        release_to_stages.return_value = (True, "")
        mocker.patch(
            "apigateway.apis.v2.sync.serializers.ReleaseInputSLZ.to_internal_value",
            return_value={
                "gateway": fake_gateway,
                "stage_ids": [stage_2.id, stage_1.id],
                "resource_version_id": resource_version.id,
                "comment": "",
            },
        )
        mocker.patch(
            "apigateway.apis.v2.sync.views.ResourceVersion.objects.get_object_fields",
            return_value={
                "id": faker.pyint(),
                "name": faker.pystr(),
                "title": faker.pystr(),
                "version": faker.pystr(),
            },
        )

        resp = request_view(
            method="POST",
            view_name="openapi.v2.sync.resource_version.release",
            gateway=fake_gateway,
            path_params={"gateway_name": fake_gateway.name},
            data={"stage_name": ["prod"], "resource_version_name": "test"},
            user=fake_admin_user,
        )

        assert resp.status_code == 200
        release_to_stages.assert_called_once()
        assert release_to_stages.call_args.kwargs["stage_ids"] == [stage_2.id, stage_1.id]

    def test_gateway_sync_with_nonexistent_data_planes_returns_error(
        self, mocker, request_view, unique_gateway_name, disable_app_permission, default_data_plane
    ):
        resp = request_view(
            method="POST",
            view_name="openapi.v2.sync.gateway.sync",
            path_params={"gateway_name": unique_gateway_name},
            data={
                "description": "desc",
                "is_public": True,
                "data_planes": ["not-exists", "default"],
            },
            app=mocker.MagicMock(app_code="foo"),
        )
        result = resp.json()

        assert resp.status_code == 400
        assert "not-exists" in str(result["error"])

    def test_mcp_server_sync_without_release(
        self, request_view, fake_gateway, fake_stage, fake_resource, disable_app_permission
    ):
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1", "tag2"],
                    "name": "server1",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "description",
                    "target_app_codes": ["app1", "app2"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 404

    def test_mcp_server_sync_with_normal_release(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1", "tag2"],
                    "name": "server1",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "description",
                    "status": 1,
                    "target_app_codes": ["app1", "app2"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["data"][0]["name"] == f"{fake_gateway.name}-{fake_stage.name}-server1"
        assert result["data"][0]["action"] == "created"
        assert MCPServerAppPermission.objects.filter(mcp_server_id=result["data"][0]["id"]).count() == 2
        audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.MCP_SERVER.value,
            op_object_id=result["data"][0]["id"],
        )
        assert audit_log.username == settings.GATEWAY_DEFAULT_CREATOR
        assert audit_log.op_type == OpTypeEnum.CREATE.value
        assert audit_log.comment == "同步 MCPServer"
        assert json.loads(audit_log.data_before) == {}
        assert json.loads(audit_log.data_after)["name"] == result["data"][0]["name"]
        permission_audit_logs = AuditEventLog.objects.filter(
            op_object_type=OpObjectTypeEnum.MCP_SERVER_PERMISSION.value,
            comment="同步 MCPServer",
        )
        assert permission_audit_logs.count() == 2
        assert set(permission_audit_logs.values_list("op_object", flat=True)) == {"app1", "app2"}
        assert set(permission_audit_logs.values_list("op_type", flat=True)) == {OpTypeEnum.CREATE.value}

    def test_mcp_server_sync_rejects_ai_resource_from_release_snapshot(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        resources = fake_release_v2.resource_version.data
        resources[0]["kind"] = ResourceKindEnum.AI.value
        fake_release_v2.resource_version.data = resources
        fake_release_v2.resource_version.save()
        make_resource_schema_version(fake_release_v2.resource_version)

        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data={
                "mcp_servers": [
                    {
                        "name": "ai-resource-server",
                        "resource_names": [fake_resource.name],
                        "is_public": True,
                        "description": "AI resource must not become an MCP tool",
                    }
                ]
            },
        )

        assert resp.status_code == 400
        assert not MCPServer.objects.filter(gateway=fake_gateway, stage=fake_stage).exists()

    def test_mcp_server_sync_with_update(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        make_resource_schema_version(fake_release_v2.resource_version)

        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-server1"
        mcp_server.status = 0
        mcp_server.save()
        # 已有的权限不会动
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app1")
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app2")

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1", "tag2"],
                    "name": "server1",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "description",
                    "status": 1,
                    "target_app_codes": ["app1", "app3"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )

        assert resp.status_code == 200
        result = resp.json()
        assert result["data"][0]["name"] == f"{fake_gateway.name}-{fake_stage.name}-server1"
        assert result["data"][0]["action"] == "updated"
        assert MCPServerAppPermission.objects.filter(mcp_server_id=result["data"][0]["id"]).count() == 3
        assert MCPServer.objects.get(id=result["data"][0]["id"]).status == 1
        audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.MCP_SERVER.value,
            op_object_id=result["data"][0]["id"],
        )
        assert audit_log.username == settings.GATEWAY_DEFAULT_CREATOR
        assert audit_log.op_type == OpTypeEnum.MODIFY.value
        assert audit_log.comment == "同步 MCPServer"
        assert json.loads(audit_log.data_before)["status"] == 0
        assert json.loads(audit_log.data_after)["status"] == 1
        permission_audit_logs = AuditEventLog.objects.filter(
            op_object_type=OpObjectTypeEnum.MCP_SERVER_PERMISSION.value,
            comment="同步 MCPServer",
        )
        assert permission_audit_logs.count() == 2
        app_code_to_op_type = {log.op_object: log.op_type for log in permission_audit_logs}
        assert app_code_to_op_type["app1"] == OpTypeEnum.MODIFY.value
        assert app_code_to_op_type["app3"] == OpTypeEnum.CREATE.value

    def test_mcp_server_sync_with_no_schema_resource(
        self, request_view, fake_gateway, fake_stage, fake_resource, fake_release_v2, disable_app_permission
    ):
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-server1"
        mcp_server.status = 0
        mcp_server.save()
        # 已有的权限不会动
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app1")
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app2")

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1", "tag2"],
                    "name": "server1",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "description",
                    "status": 1,
                    "target_app_codes": ["app1", "app3"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 400


class TestSyncApiOAuth2:
    """测试 MCPServer 同步接口的 OAuth2 功能"""

    def test_mcp_server_sync_create_with_oauth2_public_client_enabled(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时开启 OAuth2 公开客户端模式，自动对 bk_app_code=public 的应用进行授权"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1"],
                    "name": "oauth2-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "oauth2 test server",
                    "status": 1,
                    "target_app_codes": ["app1"],
                    "oauth2_public_client_enabled": True,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        mcp_server_id = result["data"][0]["id"]
        assert result["data"][0]["action"] == "created"

        # 验证 oauth2_public_client_enabled 被正确设置
        mcp_server = MCPServer.objects.get(id=mcp_server_id)
        assert mcp_server.oauth2_public_client_enabled is True

        # 验证 bk_app_code=public 已被授权
        assert MCPServerAppPermission.objects.filter(
            mcp_server_id=mcp_server_id,
            bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE,
        ).exists()

        # 验证 target_app_codes 的权限也存在
        assert MCPServerAppPermission.objects.filter(
            mcp_server_id=mcp_server_id,
            bk_app_code="app1",
        ).exists()

    def test_mcp_server_sync_create_without_oauth2(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时不开启 OAuth2 公开客户端模式，不会对 bk_app_code=public 的应用进行授权"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1"],
                    "name": "no-oauth2-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "no oauth2 test server",
                    "status": 1,
                    "target_app_codes": ["app1"],
                    "oauth2_public_client_enabled": False,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        mcp_server_id = result["data"][0]["id"]

        # 验证 bk_app_code=public 没有被授权
        assert not MCPServerAppPermission.objects.filter(
            mcp_server_id=mcp_server_id,
            bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE,
        ).exists()

    def test_mcp_server_sync_update_enable_oauth2(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试更新 MCPServer 时开启 OAuth2 公开客户端模式，自动对 bk_app_code=public 的应用进行授权"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 先创建一个不开启 OAuth2 公开客户端模式的 MCPServer
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, oauth2_public_client_enabled=False)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-update-oauth2"
        mcp_server.status = 0
        mcp_server.save()

        # 确认 public 权限不存在
        assert not MCPServerAppPermission.objects.filter(
            mcp_server=mcp_server,
            bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE,
        ).exists()

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1"],
                    "name": "update-oauth2",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "update enable oauth2",
                    "status": 1,
                    "oauth2_public_client_enabled": True,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["data"][0]["action"] == "updated"

        mcp_server_id = result["data"][0]["id"]
        # 验证 oauth2_public_client_enabled 已更新
        mcp_server.refresh_from_db()
        assert mcp_server.oauth2_public_client_enabled is True

        # 验证 bk_app_code=public 已被授权
        assert MCPServerAppPermission.objects.filter(
            mcp_server_id=mcp_server_id,
            bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE,
        ).exists()

    def test_mcp_server_sync_update_disable_oauth2(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试更新 MCPServer 时关闭 OAuth2，撤销 bk_app_code=public 的权限"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 先创建一个开启 OAuth2 公开客户端模式的 MCPServer，并手动添加 public 权限
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, oauth2_public_client_enabled=True)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-disable-oauth2"
        mcp_server.status = 1
        mcp_server.save()
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE)

        # 确认 public 权限存在
        assert MCPServerAppPermission.objects.filter(
            mcp_server=mcp_server,
            bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE,
        ).exists()

        data = {
            "mcp_servers": [
                {
                    "labels": ["tag1"],
                    "name": "disable-oauth2",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "update disable oauth2",
                    "status": 1,
                    "oauth2_public_client_enabled": False,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["data"][0]["action"] == "updated"

        # 验证 oauth2_public_client_enabled 已更新
        mcp_server.refresh_from_db()
        assert mcp_server.oauth2_public_client_enabled is False

        # 验证 bk_app_code=public 的权限已被撤销
        assert not MCPServerAppPermission.objects.filter(
            mcp_server=mcp_server,
            bk_app_code=settings.MCP_SERVER_OAUTH2_PUBLIC_CLIENT_APP_CODE,
        ).exists()


class TestSyncApiCategory:
    """测试 MCPServer 同步接口的 category_names 功能"""

    def test_mcp_server_sync_create_with_categories(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时同步分类"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 创建分类
        category1, _ = MCPServerCategory.objects.get_or_create(
            name="Official",
            defaults={
                "display_name": "官方资源",
                "description": "蓝鲸官方提供的SRE工具链",
            },
        )
        category2, _ = MCPServerCategory.objects.get_or_create(
            name="Featured",
            defaults={
                "display_name": "精选推荐",
                "description": "专家精选的SRE效能工具",
            },
        )

        data = {
            "mcp_servers": [
                {
                    "name": "category-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "category test server",
                    "status": 1,
                    "category_names": ["Official", "Featured"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        mcp_server_id = result["data"][0]["id"]
        assert result["data"][0]["action"] == "created"

        # 验证分类已关联
        mcp_server = MCPServer.objects.get(id=mcp_server_id)
        assert mcp_server.categories.count() == 2
        assert mcp_server.categories.filter(id=category1.id).exists()
        assert mcp_server.categories.filter(id=category2.id).exists()

    def test_mcp_server_sync_create_with_empty_categories(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时传入空分类列表"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "name": "empty-category-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "empty category test server",
                    "status": 1,
                    "category_names": [],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        mcp_server_id = result["data"][0]["id"]

        # 验证没有分类
        mcp_server = MCPServer.objects.get(id=mcp_server_id)
        assert mcp_server.categories.count() == 0

    def test_mcp_server_sync_create_without_category_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时不传 category_names"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "name": "no-category-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "no category test server",
                    "status": 1,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        mcp_server_id = result["data"][0]["id"]

        # 验证没有分类
        mcp_server = MCPServer.objects.get(id=mcp_server_id)
        assert mcp_server.categories.count() == 0

    def test_mcp_server_sync_create_with_invalid_category_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时传入不存在的分类名，返回错误"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 创建一个存在的分类
        MCPServerCategory.objects.get_or_create(
            name="Official",
            defaults={
                "display_name": "官方资源",
                "description": "蓝鲸官方提供的SRE工具链",
            },
        )

        data = {
            "mcp_servers": [
                {
                    "name": "invalid-category-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": [fake_resource.name],
                    "is_public": True,
                    "description": "invalid category test server",
                    "status": 1,
                    "category_names": ["Official", "NotExists"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 400
        result = resp.json()
        assert "分类不存在" in str(result["error"])

    def test_mcp_server_sync_update_categories(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试更新 MCPServer 时同步分类"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 创建分类
        category1, _ = MCPServerCategory.objects.get_or_create(
            name="Official",
            defaults={
                "display_name": "官方资源",
                "description": "蓝鲸官方提供的SRE工具链",
            },
        )
        category2, _ = MCPServerCategory.objects.get_or_create(
            name="Monitoring",
            defaults={
                "display_name": "监控告警",
                "description": "基础设施与应用性能监控工具",
            },
        )

        # 先创建一个带有分类的 MCPServer
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-update-category"
        mcp_server.status = 1
        mcp_server.save()
        mcp_server.categories.add(category1)

        # 确认初始分类
        assert mcp_server.categories.count() == 1
        assert mcp_server.categories.filter(id=category1.id).exists()

        # 更新分类
        data = {
            "mcp_servers": [
                {
                    "name": "update-category",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "update category",
                    "status": 1,
                    "category_names": ["Monitoring"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["data"][0]["action"] == "updated"

        # 验证分类已更新
        mcp_server.refresh_from_db()
        assert mcp_server.categories.count() == 1
        assert not mcp_server.categories.filter(id=category1.id).exists()
        assert mcp_server.categories.filter(id=category2.id).exists()

    def test_mcp_server_sync_update_without_category_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试更新 MCPServer 时不传 category_names，分类不变"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 创建分类
        category, _ = MCPServerCategory.objects.get_or_create(
            name="Official",
            defaults={
                "display_name": "官方资源",
                "description": "蓝鲸官方提供的SRE工具链",
            },
        )

        # 先创建一个带有分类的 MCPServer
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-keep-category"
        mcp_server.status = 1
        mcp_server.save()
        mcp_server.categories.add(category)

        # 确认初始分类
        assert mcp_server.categories.count() == 1

        # 更新但不传 category_names
        data = {
            "mcp_servers": [
                {
                    "name": "keep-category",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "keep category",
                    "status": 1,
                    # 不传 category_names
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200

        # 验证分类未变化
        mcp_server.refresh_from_db()
        assert mcp_server.categories.count() == 1
        assert mcp_server.categories.filter(id=category.id).exists()

    def test_mcp_server_sync_update_with_invalid_category_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试更新 MCPServer 时传入不存在的分类名，返回错误"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 先创建一个 MCPServer
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-invalid-update-category"
        mcp_server.status = 1
        mcp_server.save()

        # 更新时传入不存在的分类
        data = {
            "mcp_servers": [
                {
                    "name": "invalid-update-category",
                    "resource_names": [fake_resource.name],
                    "is_public": True,
                    "description": "invalid update category",
                    "status": 1,
                    "category_names": ["InvalidCategory"],
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 400
        result = resp.json()
        assert "分类不存在" in str(result["error"])


class TestSyncApiToolNames:
    """测试 MCPServer 同步接口的 tool_names 重命名功能"""

    def test_mcp_server_sync_create_with_tool_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时使用 tool_names 对资源进行重命名"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "name": "rename-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": ["renamed_tool"],
                    "is_public": True,
                    "description": "rename test server",
                    "status": 1,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200
        result = resp.json()
        mcp_server_id = result["data"][0]["id"]

        # 验证 tool_names 已正确设置
        mcp_server = MCPServer.objects.get(id=mcp_server_id)
        assert mcp_server.tool_names == ["renamed_tool"]
        assert mcp_server.resource_names == [fake_resource.name]

    def test_mcp_server_sync_create_with_tool_names_length_mismatch(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时 tool_names 长度与 resource_names 不一致，返回错误"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        data = {
            "mcp_servers": [
                {
                    "name": "mismatch-server",
                    "resource_names": [fake_resource.name],
                    "tool_names": ["tool1", "tool2"],  # 长度不一致
                    "is_public": True,
                    "description": "mismatch test server",
                    "status": 1,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 400

    def test_mcp_server_sync_create_with_duplicate_tool_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试创建 MCPServer 时 tool_names 有重复，返回错误"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 创建另一个资源
        another_resource = G(Resource, gateway=fake_gateway, name="another_resource")

        data = {
            "mcp_servers": [
                {
                    "name": "duplicate-tool-server",
                    "resource_names": [fake_resource.name, another_resource.name],
                    "tool_names": ["same_tool", "same_tool"],  # 重复
                    "is_public": True,
                    "description": "duplicate tool test server",
                    "status": 1,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 400

    def test_mcp_server_sync_update_with_tool_names(
        self,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource,
        fake_resource_schema_with_body,
        fake_release_v2,
        disable_app_permission,
    ):
        """测试更新 MCPServer 时使用 tool_names 对资源进行重命名"""
        make_resource_schema_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 先创建一个 MCPServer
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-update-rename"
        mcp_server.status = 1
        mcp_server.save()

        # 更新 tool_names
        data = {
            "mcp_servers": [
                {
                    "name": "update-rename",
                    "resource_names": [fake_resource.name],
                    "tool_names": ["updated_tool"],
                    "is_public": True,
                    "description": "updated",
                    "status": 1,
                }
            ]
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.stages.mcp_servers.sync",
            path_params={"gateway_name": fake_gateway.name, "stage_name": fake_stage.name},
            data=data,
        )
        assert resp.status_code == 200

        # 验证 tool_names 已更新
        mcp_server.refresh_from_db()
        assert mcp_server.tool_names == ["updated_tool"]


class TestGatewayAppPermissionGrantApi:
    """测试 v2_sync_grant_permission 接口的 grant_dimension 规范化"""

    @pytest.mark.parametrize(
        "grant_dimension, expected_status",
        [
            ("gateway", 201),
            ("api", 201),
        ],
    )
    def test_grant_gateway_permission(
        self, request_view, fake_gateway, disable_app_permission, grant_dimension, expected_status
    ):
        data = {
            "target_app_code": "test-app",
            "expire_days": 360,
            "grant_dimension": grant_dimension,
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.permissions.grant",
            path_params={"gateway_name": fake_gateway.name},
            data=data,
            content_type="application/json",
        )
        assert resp.status_code == expected_status
        assert AppGatewayPermission.objects.filter(
            gateway=fake_gateway,
            bk_app_code="test-app",
        ).exists()

    def test_grant_resource_permission(self, request_view, fake_gateway, fake_resource, disable_app_permission):
        data = {
            "target_app_code": "test-app",
            "expire_days": 180,
            "grant_dimension": "resource",
            "resource_names": [fake_resource.name],
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.permissions.grant",
            path_params={"gateway_name": fake_gateway.name},
            data=data,
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert AppResourcePermission.objects.filter(
            gateway=fake_gateway,
            bk_app_code="test-app",
            resource_id=fake_resource.id,
        ).exists()

    def test_grant_invalid_dimension(self, request_view, fake_gateway, disable_app_permission):
        data = {
            "target_app_code": "test-app",
            "grant_dimension": "invalid",
        }
        resp = request_view(
            method="POST",
            gateway=fake_gateway,
            view_name="openapi.v2.sync.gateway.permissions.grant",
            path_params={"gateway_name": fake_gateway.name},
            data=data,
            content_type="application/json",
        )
        assert resp.status_code == 400
