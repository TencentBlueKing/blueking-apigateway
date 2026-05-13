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

from unittest.mock import patch

import pytest
from ddf import G

from apigateway.apis.web.personal_workbench.serializers import (
    WorkbenchGatewayPermissionApplyOutputSLZ,
    WorkbenchGatewayPermissionRecordOutputSLZ,
    WorkbenchMCPPermissionApplyOutputSLZ,
    WorkbenchMCPPermissionHandledOutputSLZ,
)
from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestWorkbenchGatewayPermissionApplyOutputSLZ:
    def test_serialization(self, fake_gateway):
        """测试 API 网关申请单序列化器输出格式正确"""
        apply_record = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test_app",
            applied_by="test_user",
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            expire_days=180,
            reason="need access to resources",
            itsm_ticket_id="12345",
        )

        slz = WorkbenchGatewayPermissionApplyOutputSLZ(apply_record)
        data = slz.data

        assert data["id"] == apply_record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "test_user"
        assert data["gateway_name"] == fake_gateway.name
        assert data["status"] == ApplyStatusEnum.PENDING.value
        assert data["grant_dimension"] == GrantDimensionEnum.RESOURCE.value
        assert "grant_dimension_display" in data
        assert "expire_days_display" in data
        assert data["reason"] == "need access to resources"
        assert data["itsm_ticket_id"] == "12345"

    @patch(
        "apigateway.service.bk_itsm.ItsmPermissionApplyHelper.build_ticket_url", return_value="https://itsm/ticket/123"
    )
    def test_itsm_ticket_url(self, mock_build_url, fake_gateway):
        """测试 ITSM 单据 URL 生成"""
        apply_record = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test_app",
            applied_by="test_user",
            status=ApplyStatusEnum.PENDING.value,
            itsm_ticket_id="123",
        )

        slz = WorkbenchGatewayPermissionApplyOutputSLZ(apply_record)
        data = slz.data

        assert data["itsm_ticket_url"] == "https://itsm/ticket/123"


class TestWorkbenchGatewayPermissionRecordOutputSLZ:
    def test_serialization(self, fake_gateway):
        """测试 API 网关已办记录序列化器输出格式正确"""
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test_app",
            applied_by="applicant",
            applied_time=now_datetime(),
            handled_by="handler",
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
            grant_dimension=GrantDimensionEnum.API.value,
            expire_days=180,
            reason="need gateway access",
            comment="approved",
            itsm_ticket_id="67890",
        )

        slz = WorkbenchGatewayPermissionRecordOutputSLZ(record)
        data = slz.data

        assert data["id"] == record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "applicant"
        assert data["handled_by"] == "handler"
        assert data["gateway_name"] == fake_gateway.name
        assert data["status"] == ApplyStatusEnum.APPROVED.value
        assert data["comment"] == "approved"
        assert "grant_dimension_display" in data
        assert "expire_days_display" in data


class TestWorkbenchMCPPermissionApplyOutputSLZ:
    def test_serialization(self, fake_gateway, fake_stage):
        """测试 MCP Server 申请单序列化器输出格式正确"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            name="test-mcp",
            title="Test MCP Server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="r1;r2",
        )

        apply_record = G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server,
            bk_app_code="test_app",
            applied_by="test_user",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            reason="need mcp access",
            itsm_ticket_id="99999",
            is_deleted=False,
        )

        slz = WorkbenchMCPPermissionApplyOutputSLZ(apply_record)
        data = slz.data

        assert data["id"] == apply_record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "test_user"
        assert data["mcp_server"]["id"] == mcp_server.id
        assert data["mcp_server"]["name"] == "test-mcp"
        assert data["mcp_server"]["title"] == "Test MCP Server"
        assert data["status"] == MCPServerAppPermissionApplyStatusEnum.PENDING.value
        assert "status_display" in data
        assert data["reason"] == "need mcp access"


class TestWorkbenchMCPPermissionHandledOutputSLZ:
    def test_serialization(self, fake_gateway, fake_stage):
        """测试 MCP Server 已办记录序列化器输出格式正确"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            name="test-mcp-handled",
            title="Handled MCP",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="r1",
        )

        apply_record = G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server,
            bk_app_code="test_app",
            applied_by="applicant",
            applied_time=now_datetime(),
            handled_by="handler",
            handled_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            comment="looks good",
            itsm_ticket_id="88888",
            is_deleted=False,
        )

        slz = WorkbenchMCPPermissionHandledOutputSLZ(apply_record)
        data = slz.data

        assert data["id"] == apply_record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "applicant"
        assert data["handled_by"] == "handler"
        assert data["mcp_server"]["id"] == mcp_server.id
        assert data["status"] == MCPServerAppPermissionApplyStatusEnum.APPROVED.value
        assert data["comment"] == "looks good"
        assert "status_display" in data
        assert "handled_time" in data
