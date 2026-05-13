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

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


FAKE_USERNAME = "admin"


@pytest.fixture
def fake_other_gateway(faker):
    """创建一个当前用户不是 maintainer 的网关"""
    return G(
        Gateway,
        name=faker.pystr(),
        _maintainers="other_user",
        status=GatewayStatusEnum.ACTIVE.value,
        is_public=True,
        tenant_mode="single",
        tenant_id="default",
    )


@pytest.fixture
def fake_substring_gateway(faker):
    """创建一个 maintainer 包含当前用户名子串的网关（superadmin 包含 admin），用于验证精确匹配"""
    return G(
        Gateway,
        name=faker.pystr(),
        _maintainers="superadmin",
        status=GatewayStatusEnum.ACTIVE.value,
        is_public=True,
        tenant_mode="single",
        tenant_id="default",
    )


@pytest.fixture
def fake_mcp_server(fake_gateway, fake_stage, faker):
    """创建一个 MCP Server"""
    fake_gateway.status = GatewayStatusEnum.ACTIVE.value
    fake_gateway.save()
    fake_stage.status = StageStatusEnum.ACTIVE.value
    fake_stage.save()

    return G(
        MCPServer,
        name=faker.pystr()[:20],
        gateway=fake_gateway,
        stage=fake_stage,
        status=MCPServerStatusEnum.ACTIVE.value,
        description=faker.pystr(),
        is_public=True,
        _resource_names="resource1;resource2",
    )


# ==================== 我的代办 - API 网关 ====================


class TestWorkbenchPendingGatewayPermissionListApi:
    def test_list(self, request_view, fake_gateway):
        """测试我的代办 - API 网关：当前用户是 maintainer 的网关下有待审批的申请单"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            reason="need access",
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "app1"
        assert result["data"]["results"][0]["gateway_name"] == fake_gateway.name

    def test_list_excludes_non_maintainer_gateway(self, request_view, fake_gateway, fake_other_gateway):
        """测试我的代办 - 不返回非 maintainer 网关的申请"""
        G(
            AppPermissionApply,
            gateway=fake_other_gateway,
            bk_app_code="app2",
            applied_by="applicant2",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_excludes_substring_maintainer_gateway(self, request_view, fake_substring_gateway):
        """测试我的代办 - 用户名 admin 不应匹配 maintainer 为 superadmin 的网关（子串精确过滤）"""
        G(
            AppPermissionApply,
            gateway=fake_substring_gateway,
            bk_app_code="app_substring",
            applied_by="applicant_sub",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_excludes_non_pending(self, request_view, fake_gateway):
        """测试我的代办 - 不返回已审批或已驳回的申请"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app3",
            applied_by="applicant3",
            status=ApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_filter_by_bk_app_code(self, request_view, fake_gateway):
        """测试我的代办 - 按 bk_app_code 筛选"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="target_app",
            applied_by="applicant",
            status=ApplyStatusEnum.PENDING.value,
        )
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="other_app",
            applied_by="applicant",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
            data={"bk_app_code": "target"},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "target_app"

    def test_list_empty(self, request_view):
        """测试我的代办 - 空数据"""
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []


# ==================== 我的代办 - MCP Server ====================


class TestWorkbenchPendingMCPPermissionListApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的代办 - MCP Server：当前用户是 maintainer 的网关下有待审批的 MCP 申请"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "app1"
        assert result["data"]["results"][0]["mcp_server"]["id"] == fake_mcp_server.id

    def test_list_excludes_substring_maintainer_gateway(self, request_view, fake_substring_gateway, fake_stage, faker):
        """测试我的代办 - MCP Server：用户名 admin 不应匹配 maintainer 为 superadmin 的网关"""
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server_sub = G(
            MCPServer,
            name=faker.pystr()[:20],
            gateway=fake_substring_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            description=faker.pystr(),
            is_public=True,
            _resource_names="resource1",
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server_sub,
            bk_app_code="app_substring",
            applied_by="applicant_sub",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_excludes_deleted(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的代办 - 不返回已删除的 MCP 申请"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app2",
            applied_by="applicant2",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=True,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_empty(self, request_view):
        """测试我的代办 - MCP Server 空数据"""
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []


# ==================== 我的申请 - API 网关 ====================


class TestWorkbenchMyApplyGatewayPermissionListApi:
    def test_list(self, request_view, fake_gateway):
        """测试我的申请 - API 网关：返回当前用户提交的申请"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["applied_by"] == FAKE_USERNAME

    def test_list_excludes_other_user_apply(self, request_view, fake_gateway):
        """测试我的申请 - 不返回其他用户提交的申请"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app2",
            applied_by="other_user",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_includes_all_status(self, request_view, fake_gateway):
        """测试我的申请 - 包含各种状态的申请"""
        for status_val in [ApplyStatusEnum.PENDING.value, ApplyStatusEnum.APPROVED.value]:
            G(
                AppPermissionApply,
                gateway=fake_gateway,
                bk_app_code="app",
                applied_by=FAKE_USERNAME,
                status=status_val,
            )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 2


# ==================== 我的申请 - MCP Server ====================


class TestWorkbenchMyApplyMCPPermissionListApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的申请 - MCP Server：返回当前用户提交的 MCP 权限申请"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["applied_by"] == FAKE_USERNAME

    def test_list_excludes_other_user_apply(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的申请 - MCP Server 不返回其他用户的申请"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app2",
            applied_by="other_user",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0


# ==================== 我的已办 - API 网关 ====================


class TestWorkbenchHandledGatewayPermissionListApi:
    def test_list(self, request_view, fake_gateway):
        """测试我的已办 - API 网关：返回当前用户处理过的记录"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["handled_by"] == FAKE_USERNAME
        assert result["data"]["results"][0]["gateway_name"] == fake_gateway.name

    def test_list_excludes_pending(self, request_view, fake_gateway):
        """测试我的已办 - 不返回 pending 状态的记录"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="app2",
            applied_by="applicant2",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_excludes_other_handler(self, request_view, fake_gateway):
        """测试我的已办 - 不返回其他人处理的记录"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="app3",
            applied_by="applicant3",
            applied_time=now_datetime(),
            handled_by="other_handler",
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_empty(self, request_view):
        """测试我的已办 - 空数据"""
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []


# ==================== 我的已办 - MCP Server ====================


class TestWorkbenchHandledMCPPermissionListApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的已办 - MCP Server：返回当前用户处理过的 MCP 审批"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["handled_by"] == FAKE_USERNAME
        assert result["data"]["results"][0]["mcp_server"]["id"] == fake_mcp_server.id

    def test_list_includes_rejected(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的已办 - 包含已驳回的记录"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app2",
            applied_by="applicant2",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.REJECTED.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

    def test_list_excludes_pending(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的已办 - 不返回 pending 状态的记录"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app3",
            applied_by="applicant3",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_excludes_deleted(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的已办 - 不返回已删除的记录"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app4",
            applied_by="applicant4",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=True,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_empty(self, request_view):
        """测试我的已办 - MCP Server 空数据"""
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []
