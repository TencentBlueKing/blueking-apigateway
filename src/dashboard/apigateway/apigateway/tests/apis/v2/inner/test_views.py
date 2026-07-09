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
import time
from unittest import mock
from unittest.mock import patch

import pytest
from django.utils import timezone
from django_dynamic_fixture import G

import apigateway.apis.v2.inner.serializers as inner_serializers
import apigateway.apis.v2.inner.views as inner_views
from apigateway.apps.audit.constants import OpObjectTypeEnum
from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerPermissionStatusEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.apps.monitor.constants import AlarmStatusEnum, AlarmTypeEnum
from apigateway.apps.monitor.models import AlarmRecord
from apigateway.apps.permission.models import AppPermissionRecord
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Resource, Stage
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

    @patch("apigateway.apis.v2.inner.views.query_display_names_for_readonly")
    def test_list_batches_maintainer_lookup_by_tenant(
        self,
        mock_query_display_names_for_readonly,
        request_factory,
        settings,
        skip_view_permissions_check,
    ):
        settings.ENABLE_MULTI_TENANT_MODE = True

        another_gateway = G(
            Gateway,
            name="gateway-b",
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            tenant_mode="single",
            tenant_id="default",
            _maintainers="bob",
        )
        gateway = G(
            Gateway,
            name="gateway-a",
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            tenant_mode="single",
            tenant_id="default",
            _maintainers="alice;bob",
        )
        G(Release, gateway=gateway)
        G(Release, gateway=Gateway.objects.get(name="gateway-b"))

        mock_query_display_names_for_readonly.side_effect = lambda tenant_id, bk_usernames: [
            bk_username.title() for bk_username in bk_usernames
        ]

        request = request_factory.get("")
        request.app = mock.MagicMock(app_code="test")
        request.tenant_id = "default"
        response = inner_views.GatewayListApi.as_view()(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"] == [
            {
                "id": gateway.id,
                "name": "gateway-a",
                "description": gateway.description,
                "maintainers": ["Alice", "Bob"],
                "doc_maintainers": gateway.doc_maintainers,
            },
            {
                "id": another_gateway.id,
                "name": "gateway-b",
                "description": another_gateway.description,
                "maintainers": ["Bob"],
                "doc_maintainers": another_gateway.doc_maintainers,
            },
        ]
        mock_query_display_names_for_readonly.assert_called_once_with("default", ["alice", "bob"])


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


class TestGatewayOutputSLZ:
    @pytest.mark.parametrize(
        "output_slz_cls",
        [
            inner_serializers.GatewayListOutputSLZ,
            inner_serializers.GatewayRetrieveOutputSLZ,
        ],
    )
    @patch("apigateway.apis.v2.inner.serializers.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.apis.v2.inner.serializers.query_display_names_for_readonly")
    def test_converts_maintainers_for_cross_tenant_gateway(
        self,
        mock_query_display_names_for_readonly,
        fake_gateway,
        output_slz_cls,
    ):
        fake_gateway.tenant_mode = "global"
        fake_gateway.tenant_id = ""
        fake_gateway._maintainers = "7idwx3b7nzk6xigs;bbb"
        mock_query_display_names_for_readonly.return_value = ["张三", "李四"]

        slz = output_slz_cls(fake_gateway)

        assert slz.data["maintainers"] == ["张三", "李四"]
        mock_query_display_names_for_readonly.assert_called_once_with("system", ["7idwx3b7nzk6xigs", "bbb"])

    @pytest.mark.parametrize(
        "output_slz_cls",
        [
            inner_serializers.GatewayListOutputSLZ,
            inner_serializers.GatewayRetrieveOutputSLZ,
        ],
    )
    @patch("apigateway.apis.v2.inner.serializers.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch(
        "apigateway.apis.v2.inner.serializers.query_display_names_for_readonly",
        side_effect=RuntimeError("bk-user unavailable"),
    )
    def test_falls_back_to_original_maintainers_when_display_name_lookup_fails(
        self,
        _mock_query_display_names_for_readonly,
        fake_gateway,
        output_slz_cls,
    ):
        fake_gateway.tenant_mode = "global"
        fake_gateway.tenant_id = ""
        fake_gateway._maintainers = "7idwx3b7nzk6xigs;bbb"

        slz = output_slz_cls(fake_gateway)

        assert slz.data["maintainers"] == ["7idwx3b7nzk6xigs", "bbb"]


class TestGatewayAppPermissionApplyCreateApi:
    def test_create_rejects_resource_ids_from_other_gateway(
        self,
        request_to_view,
        request_factory,
        fake_gateway,
        mocker,
    ):
        get_released_public_resources = mocker.patch(
            "apigateway.apis.v2.inner.views.ResourceVersionHandler.get_released_public_resources",
            return_value=[
                {
                    "id": 1,
                    "allow_apply_permission": True,
                }
            ],
        )
        get_manager = mocker.patch("apigateway.apis.v2.inner.views.PermissionDimensionManager.get_manager")

        request = request_factory.post(
            "",
            data={
                "target_app_code": "test-app",
                "resource_ids": [2],
                "grant_dimension": "resource",
            },
        )
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.permission.apply",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 400
        assert "resource_ids" in result["error"]["message"]
        get_released_public_resources.assert_called_once_with(fake_gateway.id)
        get_manager.assert_not_called()


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

        mcp_server_data = result["data"][0]["mcp_server"]
        assert mcp_server_data["id"] == mcp_server.id
        assert mcp_server_data["name"] == "test-mcp-server"
        assert mcp_server_data["title"] == "Test MCP Server"
        assert mcp_server_data["protocol_type"] == MCPServerProtocolTypeEnum.SSE.value

    def test_list_with_tool_names(self, request_view, fake_gateway, fake_stage):
        """测试 MCP Server 权限列表包含 tool_names 字段（重命名后的工具名称）"""
        # 创建 MCP Server，resource_name=original_tool，tool_name=renamed_tool
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-tool-names",
            title="Test MCP Server Tool Names",
            description="Test Description",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="original_tool@renamed_tool;tool2",  # resource_name@tool_name 格式
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
        # 验证 tool_names 返回重命名后的名称
        assert mcp_server_data["tool_names"] == ["renamed_tool", "tool2"]

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

    def test_list_with_grant_permission(self, request_view, fake_gateway, fake_stage):
        """测试主动授权（grant）的 mcp_server 状态为 OWNED"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-grant",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 创建主动授权记录
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
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
        assert permission_data["status"] == MCPServerPermissionStatusEnum.OWNED.value

    def test_list_with_apply_approved_permission(self, request_view, fake_gateway, fake_stage):
        """测试申请通过（apply）且有实际权限的 mcp_server 状态为 OWNED"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-apply-approved",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 创建申请通过记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            applied_by="test-user",
            applied_time=timezone.now(),
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
        )

        # 创建实际权限记录（申请通过后会创建）
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
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
        assert permission_data["status"] == MCPServerPermissionStatusEnum.OWNED.value

    def test_list_with_pending_apply_no_grant(self, request_view, fake_gateway, fake_stage):
        """测试只有申请记录（待审批）且无实际权限的 mcp_server 状态为 PENDING"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-pending",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 创建待审批申请记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            applied_by="test-user",
            applied_time=timezone.now(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
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
        assert permission_data["status"] == MCPServerPermissionStatusEnum.PENDING.value

    def test_list_with_no_permission(self, request_view, fake_gateway, fake_stage):
        """测试没有任何权限记录的 mcp_server 状态为 NEED_APPLY"""
        G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-no-permission",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
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
        assert permission_data["status"] == MCPServerPermissionStatusEnum.NEED_APPLY.value

    def test_list_grant_overrides_apply_status(self, request_view, fake_gateway, fake_stage):
        """测试主动授权（grant）优先级高于申请记录状态"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-grant-overrides",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 创建驳回的申请记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            applied_by="test-user",
            applied_time=timezone.now(),
            status=MCPServerAppPermissionApplyStatusEnum.REJECTED.value,
        )

        # 创建主动授权记录（覆盖驳回状态）
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
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
        # 主动授权应该覆盖驳回状态
        assert permission_data["status"] == MCPServerPermissionStatusEnum.OWNED.value


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
        assert "itsm_ticket_id" in apply_record
        assert "approval_url" in apply_record
        assert f"/gateways/{fake_gateway.id}/mcp-servers/{mcp_server.id}/permissions/" in apply_record["approval_url"]
        apply = MCPServerAppPermissionApply.objects.get(bk_app_code="test-app", mcp_server=mcp_server)
        assert not AuditEventLog.objects.filter(
            op_object_type=OpObjectTypeEnum.MCP_SERVER_PERMISSION.value,
            op_object=str(apply),
        ).exists()

    def test_create_does_not_record_audit_logs(self, request_view, fake_gateway, fake_stage):
        """测试批量申请 MCP Server 权限时，不记录申请单创建审计日志"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        same_gateway_mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="same-gateway-test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        another_gateway = G(Gateway, status=GatewayStatusEnum.ACTIVE.value)
        another_stage = G(Stage, gateway=another_gateway, status=StageStatusEnum.ACTIVE.value)
        another_mcp_server = G(
            MCPServer,
            gateway=another_gateway,
            stage=another_stage,
            name="another-test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        resp = request_view(
            method="POST",
            view_name="openapi.v2.inner.mcp_server.permission.apply",
            data={
                "target_app_code": "test-app",
                "mcp_server_ids": [mcp_server.id, same_gateway_mcp_server.id, another_mcp_server.id],
                "applied_by": "test-user",
                "reason": "Test reason",
            },
            app=mock.MagicMock(app_code="test"),
        )

        assert resp.status_code == 200
        applies = MCPServerAppPermissionApply.objects.filter(bk_app_code="test-app")
        assert applies.count() == 3
        assert not AuditEventLog.objects.filter(
            op_object_type=OpObjectTypeEnum.MCP_SERVER_PERMISSION.value,
            op_object__in=[str(apply) for apply in applies],
        ).exists()

    def test_create_with_itsm_ticket_returns_itsm_url(self, request_view, fake_gateway, fake_stage, settings, mocker):
        """测试创建 MCP Server 权限申请时，若存在 itsm_ticket_id 且 ITSM 模板已配置，则 approval_url 返回 ITSM 链接"""
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = "http://itsm.example.com/ticket/{ticket_id}"

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        apply_record = G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            applied_by="test-user",
            reason="Test reason",
            itsm_ticket_id="102025092210362600001802",
        )

        mocker.patch(
            "apigateway.apis.v2.inner.views.MCPServerPermissionHandler.create_apply",
            return_value=MCPServerAppPermissionApply.objects.filter(id=apply_record.id),
        )

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

        apply_record_data = result["data"][0]
        assert apply_record_data["itsm_ticket_id"] == "102025092210362600001802"
        assert "itsm.example.com/ticket/102025092210362600001802" in apply_record_data["approval_url"]


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
        # 创建实际权限记录
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
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

    def test_list_with_tool_names(self, request_view, fake_gateway, fake_stage):
        """测试已申请权限列表包含 tool_names 字段（重命名后的工具名称）"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-tool-names",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="original_tool@renamed_tool;tool2",
        )

        # 创建已批准的申请记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            handled_by="admin",
        )
        # 创建实际权限记录
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
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
        # 验证 tool_names 返回重命名后的名称
        assert mcp_server_data["tool_names"] == ["renamed_tool", "tool2"]

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
        # 创建实际权限记录
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
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

    def test_list_with_grant_permission(self, request_view, fake_gateway, fake_stage):
        """测试主动授权（grant）的 mcp_server 能被查询到"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-grant",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value,
        )

        # 创建主动授权记录（无申请记录）
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
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
        assert mcp_server_data["name"] == "test-mcp-server-grant"

    def test_list_grant_and_apply_permissions(self, request_view, fake_gateway, fake_stage):
        """测试同时有主动授权和申请通过的 mcp_server 不会重复"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-both",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value,
        )

        # 创建申请通过记录
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            handled_by="admin",
        )

        # 创建实际权限记录
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.app-permissions",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 应该只返回一条记录，不重复
        assert len(result["data"]) == 1

    def test_list_only_approved_applies_shown(self, request_view, fake_gateway, fake_stage):
        """测试只有申请通过的记录才会显示（待审批和驳回的不显示）"""
        mcp_server_approved = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-approved",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        mcp_server_pending = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-pending",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        mcp_server_rejected = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-rejected",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        # 创建已批准的申请记录（有实际权限）
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server_approved,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            handled_by="admin",
        )
        G(
            MCPServerAppPermission,
            bk_app_code="test-app",
            mcp_server=mcp_server_approved,
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )

        # 创建待审批的申请记录（无实际权限）
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server_pending,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
        )

        # 创建已驳回的申请记录（无实际权限）
        G(
            MCPServerAppPermissionApply,
            bk_app_code="test-app",
            mcp_server=mcp_server_rejected,
            status=MCPServerAppPermissionApplyStatusEnum.REJECTED.value,
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.permission.app-permissions",
            data={"target_app_code": "test-app"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        # 只有已批准的（有实际权限）才会显示
        assert len(result["data"]) == 1
        assert result["data"][0]["mcp_server"]["name"] == "test-mcp-server-approved"


class TestMCPServerAppPermissionRecordListApi:
    def test_list_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试申请记录列表包含审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = "http://itsm.example.com/ticket/{ticket_id}"

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
            itsm_ticket_id="102025092210362600001802",
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
        assert record_data["itsm_ticket_id"] == "102025092210362600001802"
        assert "approval_url" in record_data
        assert "102025092210362600001802" in record_data["approval_url"]

    def test_list_with_itsm_ticket_fallback_to_dashboard_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试 ITSM 模板未配置时，approval_url 回退到 dashboard 审批链接"""
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )
        # 不设置 BK_ITSM4_TICKET_URL_TEMPLATE

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
            itsm_ticket_id="102025092210362600001802",
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
        assert record_data["itsm_ticket_id"] == "102025092210362600001802"
        assert "dashboard.example.com" in record_data["approval_url"]

    def test_list_with_tool_names(self, request_view, fake_gateway, fake_stage):
        """测试申请记录列表包含 tool_names 字段（重命名后的工具名称）"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-tool-names",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="resource1@tool_name_1;resource2@tool_name_2",
        )

        G(
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

        mcp_server_data = result["data"][0]["mcp_server"]
        # 验证 tool_names 返回重命名后的名称
        assert mcp_server_data["tool_names"] == ["tool_name_1", "tool_name_2"]


class TestMCPServerAppPermissionRecordRetrieveApi:
    def test_retrieve_with_approval_url(self, request_view, fake_gateway, fake_stage, settings):
        """测试申请记录详情包含审批 URL"""
        # 设置审批 URL 模板
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/"
        )
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = "http://itsm.example.com/ticket/{ticket_id}"

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
            itsm_ticket_id="102025092210362600001803",
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
        assert record_data["itsm_ticket_id"] == "102025092210362600001803"
        assert "approval_url" in record_data
        assert "102025092210362600001803" in record_data["approval_url"]

    def test_retrieve_with_tool_names(self, request_view, fake_gateway, fake_stage):
        """测试申请记录详情包含 tool_names 字段（重命名后的工具名称）"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp-server-tool-names",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1@renamed_tool1;resource2",
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

        mcp_server_data = result["data"]["mcp_server"]
        # 验证 tool_names 返回重命名后的名称
        assert mcp_server_data["tool_names"] == ["renamed_tool1", "resource2"]


class TestGatewayUpdateStatusApi:
    """测试网关状态更新接口（停用/启用）"""

    def test_update_status_with_invalid_gateway_name_prefix(self, request_to_view, request_factory, fake_gateway):
        """测试非 bp- 开头的网关不允许操作"""
        fake_gateway.name = "test-gateway"  # 不是 bp- 开头
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        request = request_factory.put("", data={"status": 0}, content_type="application/json")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.update_status",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 400
        assert "bp-" in result["error"]["message"]

    def test_disable_gateway_success(self, request_to_view, request_factory, fake_gateway, mocker):
        """测试停用 bp- 开头的网关成功"""
        fake_gateway.name = "bp-test-gateway"
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        mcp_server = G(MCPServer, gateway=fake_gateway, status=MCPServerStatusEnum.ACTIVE.value)

        # Mock 触发发布
        mocker.patch(
            "apigateway.apis.v2.inner.views.trigger_gateway_publish",
            return_value=None,
        )

        request = request_factory.put("", data={"status": 0}, content_type="application/json")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.update_status",
            path_params={"gateway_name": fake_gateway.name},
        )

        assert response.status_code == 204

        # 验证网关状态已更新
        fake_gateway.refresh_from_db()
        assert fake_gateway.status == GatewayStatusEnum.INACTIVE.value
        mcp_server.refresh_from_db()
        assert mcp_server.status == MCPServerStatusEnum.INACTIVE.value
        mcp_server_audit_log = AuditEventLog.objects.get(
            op_object_type=OpObjectTypeEnum.MCP_SERVER.value,
            op_object_id=mcp_server.id,
        )
        assert mcp_server_audit_log.comment == "网关停用，同步停用其 MCP Server"

    def test_enable_gateway_success(self, request_to_view, request_factory, fake_gateway, mocker):
        """测试启用 bp- 开头的网关成功"""
        fake_gateway.name = "bp-test-gateway"
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()

        # Mock 触发发布
        mocker.patch(
            "apigateway.apis.v2.inner.views.trigger_gateway_publish",
            return_value=None,
        )

        request = request_factory.put("", data={"status": 1}, content_type="application/json")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.update_status",
            path_params={"gateway_name": fake_gateway.name},
        )

        assert response.status_code == 204

        # 验证网关状态已更新
        fake_gateway.refresh_from_db()
        assert fake_gateway.status == GatewayStatusEnum.ACTIVE.value


class TestGatewayDestroyApi:
    """测试网关删除接口"""

    def test_destroy_with_invalid_gateway_name_prefix(self, request_to_view, request_factory, fake_gateway):
        """测试非 bp- 开头的网关不允许删除"""
        fake_gateway.name = "test-gateway"  # 不是 bp- 开头
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()

        request = request_factory.delete("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 400
        assert "bp-" in result["error"]["message"]

    def test_destroy_active_gateway_failed(self, request_to_view, request_factory, fake_gateway):
        """测试删除启用状态的网关失败"""
        fake_gateway.name = "bp-test-gateway"
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        request = request_factory.delete("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 400
        assert "停用" in result["error"]["message"]

    def test_destroy_gateway_success(self, request_to_view, request_factory, fake_gateway, mocker):
        """测试删除 bp- 开头的停用网关成功"""
        fake_gateway.name = "bp-test-gateway"
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()

        gateway_id = fake_gateway.id

        # Mock 触发发布和删除网关
        mocker.patch(
            "apigateway.apis.v2.inner.views.trigger_gateway_publish",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apis.v2.inner.views.GatewayHandler.delete_gateway",
            return_value=None,
        )

        request = request_factory.delete("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")

        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )

        assert response.status_code == 204


class TestAppPermissionRecordListApi:
    """测试申请记录列表 API 分页响应"""

    def test_list_with_pagination(self, request_view, fake_gateway, settings):
        """测试申请记录列表返回分页参数"""
        settings.BK_ITSM4_TICKET_URL_TEMPLATE = "http://itsm.example.com/ticket/{ticket_id}"
        # 创建申请记录
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test-app",
            applied_by="test-user",
            applied_time=timezone.now(),
            handled_time=timezone.now(),
            status="approved",
            itsm_ticket_id="102025092210362600001802",
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
        assert result["data"]["results"][0]["itsm_ticket_id"] == "102025092210362600001802"
        assert "itsm_ticket_url" in result["data"]["results"][0]
        assert "102025092210362600001802" in result["data"]["results"][0]["itsm_ticket_url"]

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


class TestAppAlarmRecordListApi:
    def _get_time_range_params(self):
        now = int(time.time())
        return {
            "time_start": now - 3600,
            "time_end": now + 60,
        }

    def test_list(self, request_view, fake_gateway):
        app_code = "bk-test-app"
        resource = G(Resource, gateway=fake_gateway, name="test-resource")

        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code=app_code,
            resource_id=resource.id,
            stage="prod",
            alarm_type=AlarmTypeEnum.APP_REQUEST.value,
            alarm_id="alarm-1",
            status=AlarmStatusEnum.SUCCESS.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": resource.id,
                    "stage": "prod",
                    "app_code": app_code,
                }
            ),
            message="请求 ID: req-001",
        )
        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code="other-app",
            resource_id=resource.id,
            alarm_type=AlarmTypeEnum.APP_REQUEST.value,
            alarm_id="alarm-2",
            status=AlarmStatusEnum.FAILURE.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": resource.id,
                    "stage": "prod",
                    "app_code": "other-app",
                }
            ),
            message="请求 ID: req-002",
        )
        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code=app_code,
            resource_id=resource.id,
            alarm_type=AlarmTypeEnum.RESOURCE_BACKEND.value,
            alarm_id="alarm-resource-backend",
            status=AlarmStatusEnum.SUCCESS.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": resource.id,
                    "stage": "prod",
                    "app_code": app_code,
                }
            ),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_alarm_records",
            path_params={"app_code": app_code},
            data=self._get_time_range_params(),
            app=mock.MagicMock(app_code=app_code),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        record = result["data"]["results"][0]
        assert record["alarm_id"] == "alarm-1"
        assert record["request_id"] == "req-001"
        assert record["resource_name"] == "test-resource"
        assert record["gateway_name"] == fake_gateway.name
        assert record["stage"] == "prod"

    def test_reject_missing_time_range(self, request_view):
        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_alarm_records",
            path_params={"app_code": "current-app"},
            app=mock.MagicMock(app_code="current-app"),
        )
        assert resp.status_code == 400

    def test_filter_by_resource_name(self, request_view, fake_gateway):
        app_code = "bk-test-app"
        target_resource = G(Resource, gateway=fake_gateway, name="target-resource")
        other_resource = G(Resource, gateway=fake_gateway, name="other-resource")

        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code=app_code,
            resource_id=target_resource.id,
            alarm_type=AlarmTypeEnum.APP_REQUEST.value,
            alarm_id="alarm-target",
            status=AlarmStatusEnum.SUCCESS.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": target_resource.id,
                    "stage": "prod",
                    "app_code": app_code,
                }
            ),
        )
        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code=app_code,
            resource_id=other_resource.id,
            alarm_type=AlarmTypeEnum.APP_REQUEST.value,
            alarm_id="alarm-other",
            status=AlarmStatusEnum.SUCCESS.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": other_resource.id,
                    "stage": "prod",
                    "app_code": app_code,
                }
            ),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_alarm_records",
            path_params={"app_code": app_code},
            data={
                "gateway_name": fake_gateway.name,
                "resource_name": "target-resource",
                **self._get_time_range_params(),
            },
            app=mock.MagicMock(app_code=app_code),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["alarm_id"] == "alarm-target"
        assert result["data"]["results"][0]["resource_name"] == "target-resource"

    def test_filter_by_resource_name_with_resource_id_prefix(self, request_view, fake_gateway):
        app_code = "bk-test-app"
        target_resource = G(Resource, id=120001, gateway=fake_gateway, name="target-resource-prefix")
        other_resource = G(Resource, id=1200019, gateway=fake_gateway, name="other-resource-prefix")

        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code=app_code,
            resource_id=target_resource.id,
            alarm_type=AlarmTypeEnum.APP_REQUEST.value,
            alarm_id="alarm-target-prefix",
            status=AlarmStatusEnum.SUCCESS.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": target_resource.id,
                    "stage": "prod",
                    "app_code": app_code,
                }
            ),
        )
        _ = G(
            AlarmRecord,
            gateway=fake_gateway,
            app_code=app_code,
            resource_id=other_resource.id,
            alarm_type=AlarmTypeEnum.APP_REQUEST.value,
            alarm_id="alarm-other-prefix",
            status=AlarmStatusEnum.SUCCESS.value,
            match_dimension=json.dumps(
                {
                    "api_id": fake_gateway.id,
                    "resource_id": other_resource.id,
                    "stage": "prod",
                    "app_code": app_code,
                }
            ),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_alarm_records",
            path_params={"app_code": app_code},
            data={
                "gateway_name": fake_gateway.name,
                "resource_name": "target-resource-prefix",
                **self._get_time_range_params(),
            },
            app=mock.MagicMock(app_code=app_code),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["alarm_id"] == "alarm-target-prefix"
        assert result["data"]["results"][0]["resource_id"] == target_resource.id

    def test_reject_resource_name_without_gateway_name(self, request_view):
        app_code = "bk-test-app"

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_alarm_records",
            path_params={"app_code": app_code},
            data={
                "resource_name": "target-resource",
                **self._get_time_range_params(),
            },
            app=mock.MagicMock(app_code=app_code),
        )

        assert resp.status_code == 400


class TestAppRequestLogListApi:
    def _get_time_range_params(self):
        now = int(time.time())
        return {
            "time_start": now - 3600,
            "time_end": now - 60,
        }

    def test_list(self, request_view, mocker):
        mock_search_logs = mocker.patch(
            "apigateway.apis.v2.inner.views.LogSearchClient.search_logs",
            return_value=(
                1,
                [
                    {
                        "request_id": "req-001",
                        "timestamp": 1751366500,
                        "gateway_name": "bk-user-api",
                        "stage": "prod",
                        "resource_id": 12,
                        "resource_name": "list_users",
                        "method": "GET",
                        "http_host": "bk-user-api.example.com",
                        "http_path": "/prod/users",
                        "status": 200,
                        "request_duration": 32,
                        "code_name": "",
                        "error": "",
                        "response_desc": "OK",
                        "backend_host": "private-backend.example.com",
                    }
                ],
            ),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_request_logs",
            path_params={"app_code": "bk-test-app"},
            data=self._get_time_range_params(),
            app=mock.MagicMock(app_code="bk-test-app"),
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        record = result["data"]["results"][0]
        assert record["request_id"] == "req-001"
        assert record["gateway_name"] == "bk-user-api"
        assert "backend_host" not in record
        mock_search_logs.assert_called_once()

    def test_allow_path_app_code_different_from_request_app(self, request_view, mocker):
        mock_search_logs = mocker.patch(
            "apigateway.apis.v2.inner.views.LogSearchClient.search_logs",
            return_value=(0, []),
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_request_logs",
            path_params={"app_code": "another-app"},
            data=self._get_time_range_params(),
            app=mock.MagicMock(app_code="current-app"),
        )

        assert resp.status_code == 200
        mock_search_logs.assert_called_once()

    @pytest.mark.parametrize(
        "case",
        [
            "missing_time_range",
            "time_start_too_old",
            "time_end_not_greater",
            "time_end_in_future",
        ],
    )
    def test_reject_invalid_time_range(self, request_view, case):
        now = int(time.time())
        data = {
            "missing_time_range": {},
            "time_start_too_old": {"time_start": now - 181 * 24 * 3600, "time_end": now - 60},
            "time_end_not_greater": {"time_start": now - 3600, "time_end": now - 3600},
            "time_end_in_future": {"time_start": now - 3600, "time_end": now + 60},
        }[case]

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_request_logs",
            path_params={"app_code": "current-app"},
            data=data,
            app=mock.MagicMock(app_code="current-app"),
        )
        assert resp.status_code == 400

    def test_reject_limit_greater_than_100(self, request_view):
        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.monitor.app_request_logs",
            path_params={"app_code": "current-app"},
            data={**self._get_time_range_params(), "limit": 101},
            app=mock.MagicMock(app_code="current-app"),
        )
        assert resp.status_code == 400


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

        # Mock GatewayAuthContext - 使用 OFFICIAL_API gateway_type 使 is_official 为 True
        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
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

        # Mock GatewayAuthContext - 使用 OFFICIAL_API gateway_type 使 is_official 为 True
        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
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

        # Mock GatewayAuthContext - 使用 OFFICIAL_API gateway_type 使 is_official 为 True
        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
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

    def test_list_with_mcp_server_ids_filter(self, request_view, fake_gateway, mocker):
        """测试使用 mcp_server_ids 筛选 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        mcp_server1 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="server-one",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )
        mcp_server2 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="server-two",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )
        mcp_server3 = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="server-three",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
        )

        # 只筛选 server1 和 server3
        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            data={"mcp_server_ids": f"{mcp_server1.id},{mcp_server3.id}"},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        result_ids = [item["id"] for item in result["data"]["results"]]
        assert mcp_server1.id in result_ids
        assert mcp_server3.id in result_ids
        assert mcp_server2.id not in result_ids

    def test_list_with_mcp_server_ids_empty(self, request_view, fake_gateway, mocker):
        """测试 mcp_server_ids 为空时返回所有"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="server-empty-ids-test",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
        )

        # mcp_server_ids 为空字符串，应返回所有
        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            data={"mcp_server_ids": ""},
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        result_ids = [item["id"] for item in result["data"]["results"]]
        assert mcp_server.id in result_ids

    def test_list_with_mcp_server_ids_invalid(self, request_view, fake_gateway, mocker):
        """测试 mcp_server_ids 包含非法值时返回 400"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            data={"mcp_server_ids": "abc,def"},
            app=mock.MagicMock(app_code="test"),
        )

        assert resp.status_code == 400

    def test_list_returns_oauth2_public_client_enabled_true(self, request_view, fake_gateway, mocker):
        """测试 MCPServer 列表接口返回 oauth2_public_client_enabled=True"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="oauth2-enabled-mcp",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            oauth2_public_client_enabled=True,
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_data = next(
            (item for item in result["data"]["results"] if item["id"] == mcp_server.id),
            None,
        )
        assert mcp_data is not None
        assert mcp_data["oauth2_public_client_enabled"] is True

    def test_list_returns_oauth2_public_client_enabled_false(self, request_view, fake_gateway, mocker):
        """测试 MCPServer 列表接口返回 oauth2_public_client_enabled=False"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="oauth2-disabled-mcp",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            oauth2_public_client_enabled=False,
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_data = next(
            (item for item in result["data"]["results"] if item["id"] == mcp_server.id),
            None,
        )
        assert mcp_data is not None
        assert mcp_data["oauth2_public_client_enabled"] is False

    def test_list_returns_tool_names(self, request_view, fake_gateway, mocker):
        """测试 MCPServer 列表接口返回 tool_names（含重命名场景）"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.maintainers = ["admin"]
        fake_gateway.save()

        stage = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=stage,
            name="tool-names-mcp",
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            protocol_type=MCPServerProtocolTypeEnum.SSE.value,
            _resource_names="res1;res2@custom_tool2",
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.GatewayAuthContext.get_gateway_id_to_auth_config",
            return_value={fake_gateway.id: mock.MagicMock(gateway_type=1)},
        )

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.mcp_server.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_data = next(
            (item for item in result["data"]["results"] if item["id"] == mcp_server.id),
            None,
        )
        assert mcp_data is not None
        assert "tool_names" in mcp_data
        assert mcp_data["tool_names"] == ["res1", "custom_tool2"]
        assert mcp_data["resource_names"] == ["res1", "res2"]


def test_v2_inner_does_not_import_shared_api_mcp_module():
    shared_api_mcp_module = ".".join(["apigateway", "apis", "v2", "mcp_server"])

    assert not any(getattr(obj, "__module__", "") == shared_api_mcp_module for obj in inner_views.__dict__.values())
    assert not any(
        getattr(obj, "__module__", "") == shared_api_mcp_module for obj in inner_serializers.__dict__.values()
    )
