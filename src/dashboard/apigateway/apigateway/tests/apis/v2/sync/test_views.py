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
from django.conf import settings

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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
            bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE,
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
            bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE,
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
            bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE,
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
            bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE,
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
        fake_gateway.name = "test"
        fake_stage.name = "test"
        fake_gateway.save()
        fake_stage.save()

        # 先创建一个开启 OAuth2 公开客户端模式的 MCPServer，并手动添加 public 权限
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, oauth2_public_client_enabled=True)
        mcp_server.name = f"{fake_gateway.name}-{fake_stage.name}-disable-oauth2"
        mcp_server.status = 1
        mcp_server.save()
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE)

        # 确认 public 权限存在
        assert MCPServerAppPermission.objects.filter(
            mcp_server=mcp_server,
            bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE,
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
            bk_app_code=settings.MCP_SERVER_PUBLIC_APP_CODE,
        ).exists()
