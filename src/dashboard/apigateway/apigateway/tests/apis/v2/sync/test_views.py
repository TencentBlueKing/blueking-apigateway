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

from apigateway.apps.data_plane.models import DataPlane
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerCategory
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.biz.resource import ResourceOpenAPISchemaVersionHandler
from apigateway.core.models import Resource


@pytest.fixture()
def disable_app_permission(mocker):
    mocker.patch(
        "apigateway.apis.v2.sync.views.OpenAPIV2GatewayRelatedAppPermission.has_permission",
        return_value=True,
    )


class TestSyncApi:
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
        mock_saver_cls = mocker.patch("apigateway.apis.v2.sync.views.GatewaySaver")
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
        ResourceOpenAPISchemaVersionHandler.make_new_version(fake_release_v2.resource_version)
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
