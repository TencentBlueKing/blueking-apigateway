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
from unittest import mock

from django_dynamic_fixture import G

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Stage
from apigateway.tests.utils.testing import get_response_json


class TestGatewayListApi:
    def test_list(self, request_view, fake_gateway, mocker):
        g1 = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=False)
        G(Release, gateway=g1)
        g2 = G(Gateway, status=GatewayStatusEnum.INACTIVE.value, is_public=True)
        G(Release, gateway=g2)

        _ = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        # released
        g4 = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=True)
        G(Release, gateway=g4)
        G(Release, gateway=fake_gateway)

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.gateway.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) == 2


class TestGatewayRetrieveApi:
    def test_retrieve(self, request_to_view, request_factory, fake_gateway):
        request = request_factory.get("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")
        response = request_to_view(
            request,
            view_name="openapi.v2.open.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"]["name"] == fake_gateway.name


class TestMCPServerAppPermissionApplyCreateApi:
    def test_create_returns_approval_url(self, request_view, fake_gateway, settings):
        """测试创建 MCP Server 权限申请时返回 approval_url"""
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/{gateway_id}/mcp/permission?serverId={mcp_server_id}"
        )

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

        resp = request_view(
            method="POST",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply",
            app=mock.MagicMock(app_code="test"),
            data={
                "bk_app_code": "test_app",
                "mcp_server_ids": [mcp_server.id],
                "reason": "test reason",
                "applied_by": "test_user",
            },
        )

        assert resp.status_code == 200
        result = resp.json()
        assert "data" in result
        assert len(result["data"]) > 0
        # 验证返回的数据包含 approval_url
        for item in result["data"]:
            assert "approval_url" in item
            assert f"/{fake_gateway.id}/mcp/permission?serverId={mcp_server.id}" in item["approval_url"]


class TestMCPServerAppPermissionRecordListApi:
    def test_list_returns_approval_url(self, request_view, fake_gateway, settings):
        """测试获取 MCP Server 权限申请记录时返回 approval_url"""
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/{gateway_id}/mcp/permission?serverId={mcp_server_id}"
        )

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test_app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="test_user",
            reason="test reason",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.app.permissions.apply-records.list",
            app=mock.MagicMock(app_code="test"),
            data={
                "bk_app_code": "test_app",
            },
        )

        assert resp.status_code == 200
        result = resp.json()
        assert "data" in result
        assert len(result["data"]) > 0
        # 验证返回的数据包含 approval_url
        for item in result["data"]:
            assert "approval_url" in item
            assert f"/{fake_gateway.id}/mcp/permission?serverId={mcp_server.id}" in item["approval_url"]


class TestMCPServerRetrieveApi:
    """测试 MCPServerRetrieveApi"""

    def test_retrieve_public_mcp_server(self, request_view, fake_gateway, mocker):
        """测试获取公开的 MCPServer 详情"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="test-mcp-server",
            title="Test MCP Server",
            description="Test Description",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="tool1",
        )

        # Mock MCPServerHandler 方法
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], ["label1"]),
        )
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_prompts_count_map",
            return_value={mcp_server.id: 0},
        )
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_prompts",
            return_value=[],
        )
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_user_custom_doc",
            return_value="",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
            app=mock.MagicMock(app_code="test"),
            user=mock.MagicMock(username="test_user"),
        )

        assert resp.status_code == 200
        result = resp.json()
        assert result["data"]["id"] == mcp_server.id
        assert result["data"]["name"] == "test-mcp-server"
        assert result["data"]["title"] == "Test MCP Server"
        assert result["data"]["is_public"] is True
        assert "guideline" in result["data"]
        assert "tools" in result["data"]
        assert "maintainers" in result["data"]

    def test_retrieve_private_mcp_server_by_maintainer(self, request_view, fake_gateway, mocker):
        """测试网关维护者获取私有的 MCPServer 详情"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["test_user"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="private-mcp-server",
            is_public=False,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        # Mock MCPServerHandler 方法
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], []),
        )
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_prompts_count_map",
            return_value={mcp_server.id: 0},
        )
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_prompts",
            return_value=[],
        )
        mocker.patch(
            "apigateway.apis.v2.open.views.MCPServerHandler.get_user_custom_doc",
            return_value="",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
            app=mock.MagicMock(app_code="test"),
            user=mock.MagicMock(username="test_user"),  # 用户是维护者
        )

        assert resp.status_code == 200
        result = resp.json()
        assert result["data"]["id"] == mcp_server.id
        assert result["data"]["is_public"] is False

    def test_retrieve_private_mcp_server_by_non_maintainer(self, request_view, fake_gateway, mocker):
        """测试非维护者无法获取私有的 MCPServer 详情"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="private-mcp-server",
            is_public=False,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
            app=mock.MagicMock(app_code="test"),
            user=mock.MagicMock(username="other_user"),  # 用户不是维护者
        )

        assert resp.status_code == 404

    def test_retrieve_inactive_mcp_server(self, request_view, fake_gateway, mocker):
        """测试获取未启用的 MCPServer 返回 404"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            is_public=True,
            status=MCPServerStatusEnum.INACTIVE.value,  # 未启用
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
            app=mock.MagicMock(app_code="test"),
            user=mock.MagicMock(username="test_user"),
        )

        assert resp.status_code == 404

    def test_retrieve_mcp_server_with_inactive_gateway(self, request_view, fake_gateway, mocker):
        """测试获取所属网关未启用的 MCPServer 返回 404"""
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value  # 网关未启用
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
            app=mock.MagicMock(app_code="test"),
            user=mock.MagicMock(username="test_user"),
        )

        assert resp.status_code == 404

    def test_retrieve_mcp_server_with_inactive_stage(self, request_view, fake_gateway, mocker):
        """测试获取所属环境未启用的 MCPServer 返回 404"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.INACTIVE.value)  # 环境未启用
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.open.mcp_server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
            app=mock.MagicMock(app_code="test"),
            user=mock.MagicMock(username="test_user"),
        )

        assert resp.status_code == 404
