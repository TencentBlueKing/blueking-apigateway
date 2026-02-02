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
import time
from unittest import mock

from django.utils import timezone
from django_dynamic_fixture import G

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.models import AppPermissionRecord
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
            view_name="openapi.v2.inner.gateway.list",
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
            view_name="openapi.v2.inner.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"]["name"] == fake_gateway.name


class TestMCPServerPermissionListApi:
    def test_list_with_protocol_type(self, request_view, fake_gateway, fake_stage):
        """测试 MCP Server 权限列表包含协议类型数据"""
        # 创建 MCP Server
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            title="Test MCP Server",
            description="Test Description",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="tool1",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.list",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        mcp_server_data = result["data"][0]["mcp_server"]
        assert mcp_server_data["id"] == mcp_server.id
        assert mcp_server_data["name"] == "test-mcp-server"
        assert mcp_server_data["title"] == "Test MCP Server"
        assert mcp_server_data["protocol_type"] == MCPServerProtocolTypeEnum.SSE.value

    def test_list_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试 MCP Server 权限列表包含审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            title="Test MCP Server",
            description="Test Description",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="tool1;tool2",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.list",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        permission_data = result["data"][0]["permission"]
        assert "approval_url" in permission_data
        assert (
            f"/gateways/{fake_gateway.id}/mcp-servers/{mcp_server.id}/permissions/" in permission_data["approval_url"]
        )

    def test_list_basic_functionality(self, request_view, fake_gateway, fake_stage):
        """测试 MCP Server 基本功能"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-basic",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.list",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        mcp_server_data = result["data"][0]["mcp_server"]
        assert mcp_server_data["protocol_type"] == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value


class TestMCPServerAppPermissionApplyCreateApi:
    def test_create_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试创建 MCP Server 权限申请并返回审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 确保 gateway 和 stage 状态正确
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        resp = request_view(
            method="POST",
            view_name="openapi.v2.inner.mcp_server.permission.apply",
            data={
                "target_app_code": "test-app",
                "mcp_server_ids": [mcp_server.id],
                "applied_by": "test-user",
                "reason": "Test reason",
            },
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        apply_record = result["data"][0]
        assert apply_record["bk_app_code"] == "test-app"
        assert apply_record["mcp_server_id"] == mcp_server.id
        assert "approval_url" in apply_record
        assert f"/gateways/{fake_gateway.id}/mcp-servers/{mcp_server.id}/permissions/" in apply_record["approval_url"]


class TestMCPServerAppPermissionListApi:
    def test_list_with_protocol_type(self, request_view, fake_gateway, fake_stage):
        """测试已申请权限列表包含协议类型数据"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        # 创建已批准的申请记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            handled_by="admin",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.app-permissions",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        mcp_server_data = result["data"][0]["mcp_server"]
        assert mcp_server_data["protocol_type"] == MCPServerProtocolTypeEnum.SSE.value

    def test_list_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试已申请权限列表包含审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        # 创建已批准的申请记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            handled_by="admin",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.app-permissions",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        permission_data = result["data"][0]["permission"]
        assert "approval_url" in permission_data
        assert (
            f"/gateways/{fake_gateway.id}/mcp-servers/{mcp_server.id}/permissions/" in permission_data["approval_url"]
        )


class TestMCPServerAppPermissionRecordListApi:
    def test_list_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试申请记录列表包含审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value,
        )

        apply_record = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="test-user",
            reason="Test reason",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.apply-records",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 1

        record_data = result["data"][0]["record"]
        assert record_data["id"] == apply_record.id
        assert "approval_url" in record_data
        assert f"/gateways/{fake_gateway.id}/mcp-servers/{mcp_server.id}/permissions/" in record_data["approval_url"]


class TestMCPServerAppPermissionRecordRetrieveApi:
    def test_retrieve_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试申请记录详情包含审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        apply_record = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            applied_by="test-user",
            handled_by="admin",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.apply-record-detail",
            path_params={"record_id": apply_record.id},
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200

        record_data = result["data"]["record"]
        assert record_data["id"] == apply_record.id
        assert "approval_url" in record_data
        assert f"/gateways/{fake_gateway.id}/mcp-servers/{mcp_server.id}/permissions/" in record_data["approval_url"]


class TestAppPermissionRecordListApi:
    """测试申请记录列表 API 分页响应"""

    def test_list_with_pagination(self, request_view, fake_gateway):
        """测试申请记录列表返回分页参数"""
        # 创建申请记录
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="test-user",
            applied_time=timezone.now(),
            handled_time=timezone.now(),
            status="approved",
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.permission.apply-records",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证分页参数存在
        assert "count" in result["data"]
        assert "results" in result["data"]
        # 验证数据
        assert result["data"]["count"] == 1
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["id"] == record.id

    def test_list_empty_with_pagination(self, request_view, fake_gateway):
        """测试空列表返回分页参数"""
        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.permission.apply-records",
            data={"target_app_code": "non-existent-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 验证分页参数存在
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []


class TestMCPServerListApi:
    """测试 MCPServerListApi - 获取全量的 MCPServer 列表"""

    def test_list_public_active_mcp_servers(self, request_view, fake_gateway, mocker):
        """测试获取活跃的 MCPServer 列表"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        # 创建公开且活跃的 MCPServer
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="test-mcp-server",
            title="Test MCP Server",
            description="Test Description",
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="tool1",
        )

        # Mock GatewayAuthContext
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=None)},
        )
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayTypeHandler.is_official",
            return_value=True,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "results" in result["data"]
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["id"] == mcp_server.id
        assert result["data"]["results"][0]["name"] == "test-mcp-server"
        assert result["data"]["results"][0]["protocol_type"] == MCPServerProtocolTypeEnum.SSE.value

    def test_list_includes_all_active_mcp_servers(self, request_view, fake_gateway, mocker):
        """测试返回所有活跃的 MCPServer（包括公开和非公开）"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        # 使用唯一的时间戳作为名称后缀
        suffix = str(int(time.time() * 1000))

        # 创建一个公开的 MCPServer 和一个非公开的 MCPServer
        public_name = f"public-mcp-{suffix}"
        private_name = f"private-mcp-{suffix}"

        MCPServer.objects.create(
            gateway=fake_gateway,
            stage=stage,
            name=public_name,
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )
        MCPServer.objects.create(
            gateway=fake_gateway,
            stage=stage,
            name=private_name,
            is_public=False,  # 非公开
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        # Mock GatewayAuthContext
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=None)},
        )
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayTypeHandler.is_official",
            return_value=True,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # Inner API 返回所有活跃的 MCPServer（包括公开和非公开）
        result_names = [item["name"] for item in result["data"]["results"]]
        assert public_name in result_names
        assert private_name in result_names

    def test_list_excludes_inactive_mcp_servers(self, request_view, fake_gateway, mocker):
        """测试不返回未启用的 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        # 创建未启用的 MCPServer
        inactive_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="inactive-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.INACTIVE.value,  # 未启用
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 确保未启用的 MCPServer 不在结果中
        result_ids = [item["id"] for item in result["data"]["results"]]
        assert inactive_mcp_server.id not in result_ids

    def test_list_excludes_inactive_gateway_mcp_servers(self, request_view, fake_gateway, mocker):
        """测试不返回网关未启用的 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value  # 网关未启用
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        inactive_gateway_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="test-mcp-server-inactive-gw",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 确保网关未启用的 MCPServer 不在结果中
        result_ids = [item["id"] for item in result["data"]["results"]]
        assert inactive_gateway_mcp_server.id not in result_ids

    def test_list_excludes_inactive_stage_mcp_servers(self, request_view, fake_gateway, mocker):
        """测试不返回环境未启用的 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.INACTIVE.value)  # 环境未启用

        inactive_stage_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="test-mcp-server-inactive-stage",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 确保环境未启用的 MCPServer 不在结果中
        result_ids = [item["id"] for item in result["data"]["results"]]
        assert inactive_stage_mcp_server.id not in result_ids

    def test_list_with_keyword_filter(self, request_view, fake_gateway, mocker):
        """测试使用关键字筛选 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        # 创建两个 MCPServer
        mcp_server1 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="hello-world",
            title="Hello World",
            description="A hello world mcp server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )
        G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="another-server",
            title="Another Server",
            description="Another mcp server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        # Mock GatewayAuthContext
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=None)},
        )
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayTypeHandler.is_official",
            return_value=True,
        )

        # 使用关键字筛选
        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            data={"keyword": "hello"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["id"] == mcp_server1.id
