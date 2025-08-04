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

import pytest
from ddf import G

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission
from apigateway.biz.resource import ResourceOpenAPISchemaVersionHandler


@pytest.fixture()
def disable_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.v2.sync.views.OpenAPIV2GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestSyncApi:
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)

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
