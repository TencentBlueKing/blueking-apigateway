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

from unittest.mock import patch

import pytest
from ddf import G

from apigateway.apis.web.personal_workbench.serializers import (
    WorkbenchGatewayPermissionApproverOutputSLZ,
    WorkbenchGatewayPermissionMyApplyOutputSLZ,
    WorkbenchMCPPermissionApproverOutputSLZ,
    WorkbenchMCPPermissionMyApplyOutputSLZ,
)
from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestWorkbenchGatewayPermissionApproverOutputSLZ:
    def test_pending_apply(self, fake_gateway):
        """待办序列化申请单，处理字段为空，并返回当前审批责任人。"""
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

        slz = WorkbenchGatewayPermissionApproverOutputSLZ(
            apply_record,
            context={"gateway_approvers": {fake_gateway.id: ["admin"]}},
        )
        data = slz.data

        assert data["id"] == apply_record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "test_user"
        assert data["approvers"] == ["admin"]
        assert data["gateway_id"] == fake_gateway.id
        assert data["gateway_name"] == fake_gateway.name
        assert data["status"] == ApplyStatusEnum.PENDING.value
        assert data["grant_dimension"] == GrantDimensionEnum.RESOURCE.value
        assert "grant_dimension_display" in data
        assert "expire_days_display" in data
        assert data["reason"] == "need access to resources"
        assert data["itsm_ticket_id"] == "12345"
        assert data["created_time"] is not None
        assert data["applied_time"] is None
        assert data["handled_by"] == ""
        assert data["handled_time"] is None
        assert data["comment"] == ""

    def test_pending_apply_prefers_operator_approvers(self, fake_gateway):
        apply_record = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test_app",
            applied_by="test_user",
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.API.value,
        )

        slz = WorkbenchGatewayPermissionApproverOutputSLZ(
            apply_record,
            context={"gateway_approvers": {fake_gateway.id: ["operator"]}},
        )

        assert slz.data["approvers"] == ["operator"]

    @patch(
        "apigateway.service.bk_itsm.ItsmPermissionApplyHelper.build_ticket_url", return_value="https://itsm/ticket/123"
    )
    def test_pending_apply_itsm_ticket_url(self, mock_build_url, fake_gateway):
        apply_record = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="test_app",
            applied_by="test_user",
            status=ApplyStatusEnum.PENDING.value,
            itsm_ticket_id="123",
        )

        slz = WorkbenchGatewayPermissionApproverOutputSLZ(
            apply_record,
            context={"gateway_approvers": {fake_gateway.id: ["admin"]}},
        )

        assert slz.data["itsm_ticket_url"] == "https://itsm/ticket/123"

    def test_handled_record(self, fake_gateway):
        """已办序列化申请记录，不返回当前审批责任人。"""
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

        slz = WorkbenchGatewayPermissionApproverOutputSLZ(record)
        data = slz.data

        assert data["id"] == record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "applicant"
        assert data["handled_by"] == "handler"
        assert data["gateway_id"] == fake_gateway.id
        assert data["gateway_name"] == fake_gateway.name
        assert data["status"] == ApplyStatusEnum.APPROVED.value
        assert data["comment"] == "approved"
        assert data["approvers"] == []
        assert data["created_time"] is None
        assert data["applied_time"] is not None
        assert "grant_dimension_display" in data
        assert "expire_days_display" in data


class TestWorkbenchGatewayPermissionMyApplyOutputSLZ:
    @patch(
        "apigateway.service.bk_itsm.ItsmPermissionApplyHelper.build_ticket_url",
        return_value="https://itsm/ticket/123",
    )
    def test_serialization_keeps_my_apply_contract(self, mock_build_url, fake_gateway):
        applied_time = now_datetime()
        record = G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="test_app",
            applied_by="test_user",
            applied_time=applied_time,
            handled_by="handler",
            handled_time=now_datetime(),
            status=ApplyStatusEnum.PARTIAL_APPROVED.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            expire_days=180,
            reason="need access to resources",
            itsm_ticket_id="123",
        )

        slz = WorkbenchGatewayPermissionMyApplyOutputSLZ(
            record,
            context={"gateway_approvers": {fake_gateway.id: ["admin"]}},
        )
        data = slz.data

        assert data["id"] == record.id
        assert data["applied_by"] == "test_user"
        assert data["approvers"] == ["admin"]
        assert data["status"] == ApplyStatusEnum.PARTIAL_APPROVED.value
        assert data["applied_time"] == data["created_time"]
        assert data["itsm_ticket_url"] == "https://itsm/ticket/123"
        assert "handled_by" not in data
        assert "handled_time" not in data


class TestWorkbenchMCPPermissionMyApplyOutputSLZ:
    def test_serialization(self, fake_gateway, fake_stage):
        """我的申请不返回处理字段。"""
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

        slz = WorkbenchMCPPermissionMyApplyOutputSLZ(
            apply_record,
            context={"gateway_approvers": {fake_gateway.id: ["admin"]}},
        )
        data = slz.data

        assert data["id"] == apply_record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "test_user"
        assert data["approvers"] == ["admin"]
        assert data["mcp_server"]["id"] == mcp_server.id
        assert data["mcp_server"]["name"] == "test-mcp"
        assert data["mcp_server"]["title"] == "Test MCP Server"
        assert data["mcp_server"]["gateway_id"] == fake_gateway.id
        assert data["mcp_server"]["gateway_name"] == fake_gateway.name
        assert data["status"] == MCPServerAppPermissionApplyStatusEnum.PENDING.value
        assert "status_display" in data
        assert data["reason"] == "need mcp access"
        assert "handled_by" not in data
        assert "handled_time" not in data
        assert "comment" not in data


class TestWorkbenchMCPPermissionApproverOutputSLZ:
    def test_pending_apply(self, fake_gateway, fake_stage):
        """待办返回当前审批责任人，处理字段为空。"""
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
            is_deleted=False,
        )

        slz = WorkbenchMCPPermissionApproverOutputSLZ(
            apply_record,
            context={"gateway_approvers": {fake_gateway.id: ["admin"]}},
        )
        data = slz.data

        assert data["approvers"] == ["admin"]
        assert data["handled_by"] == ""
        assert data["handled_time"] is None
        assert data["comment"] == ""

    def test_handled_record(self, fake_gateway, fake_stage):
        """已办返回处理结果，不查询当前审批责任人。"""
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

        slz = WorkbenchMCPPermissionApproverOutputSLZ(apply_record)
        data = slz.data

        assert data["id"] == apply_record.id
        assert data["bk_app_code"] == "test_app"
        assert data["applied_by"] == "applicant"
        assert data["approvers"] == []
        assert data["handled_by"] == "handler"
        assert data["mcp_server"]["id"] == mcp_server.id
        assert data["mcp_server"]["gateway_id"] == fake_gateway.id
        assert data["mcp_server"]["gateway_name"] == fake_gateway.name
        assert data["status"] == MCPServerAppPermissionApplyStatusEnum.APPROVED.value
        assert data["comment"] == "looks good"
        assert "status_display" in data
        assert "handled_time" in data
