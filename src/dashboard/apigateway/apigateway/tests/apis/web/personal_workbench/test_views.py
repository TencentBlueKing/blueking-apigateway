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

import datetime

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.biz.bk_itsm import ITSM_PERMISSION_APPROVAL_HANDLER
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Resource, Stage
from apigateway.utils.time import now_datetime, timestamp

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


@pytest.fixture
def make_mcp_server(faker):
    """创建指定网关下的 MCP Server"""

    def _make_mcp_server(gateway):
        stage = G(
            Stage,
            gateway=gateway,
            status=StageStatusEnum.ACTIVE.value,
            name=faker.pystr()[:20],
            description=faker.pystr(),
        )
        return G(
            MCPServer,
            name=faker.pystr()[:20],
            gateway=gateway,
            stage=stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            description=faker.pystr(),
            is_public=True,
            _resource_names="resource1;resource2",
        )

    return _make_mcp_server


# ==================== 筛选下拉选项 - 网关 ====================


class TestWorkbenchGatewayFilterOptionListApi:
    def test_pending_returns_gateways_from_pending_applies(self, request_view, fake_gateway):
        """pending 类型：返回我的待办权限列表关联的网关"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        assert resp.status_code == 200
        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids

    def test_pending_excludes_gateways_without_pending_apply(self, request_view, fake_gateway):
        """pending 类型：不返回没有待审批申请的网关"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id not in gateway_ids

    def test_pending_excludes_non_maintainer_gateways(self, request_view, fake_other_gateway):
        """pending 类型：不返回非 maintainer 的网关"""
        G(
            AppPermissionApply,
            gateway=fake_other_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_other_gateway.id not in gateway_ids

    def test_applied_returns_gateways_from_my_applies(self, request_view, fake_gateway, fake_other_gateway):
        """applied 类型：返回当前用户申请过的网关（即使不是 maintainer）"""
        G(
            AppPermissionApply,
            gateway=fake_other_gateway,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "applied"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_other_gateway.id in gateway_ids
        # 没有申请过的网关不应出现
        assert fake_gateway.id not in gateway_ids

    def test_handled_returns_gateways_from_my_handled_records(self, request_view, fake_gateway):
        """handled 类型：返回当前用户处理过的网关"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "handled"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids

    def test_handled_returns_itsm_records_for_maintainer(self, request_view, fake_gateway, fake_other_gateway):
        """handled 类型：ITSM 回调无实际审批人，返回当前用户维护网关下的 ITSM 已办记录"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )
        G(
            AppPermissionRecord,
            gateway=fake_other_gateway,
            bk_app_code="app2",
            applied_by="applicant2",
            applied_time=now_datetime(),
            handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "handled"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids
        assert fake_other_gateway.id not in gateway_ids

    def test_default_type_is_pending(self, request_view, fake_gateway):
        """默认 type 为 pending"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            status=ApplyStatusEnum.PENDING.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
        )
        result = resp.json()

        assert resp.status_code == 200
        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids

    def test_no_pagination(self, request_view):
        """下拉选项不分页，响应为标准格式 {"data": [...]}"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert isinstance(result["data"], list)

    def test_invalid_type_returns_400(self, request_view):
        """传入无效 type 值应返回 400"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "invalid_value"},
        )
        assert resp.status_code == 400

    def test_applied_deduplicates_multiple_applies(self, request_view, fake_gateway, fake_other_gateway):
        """applied 类型：同一网关多条申请记录应去重"""
        for _ in range(3):
            G(
                AppPermissionApply,
                gateway=fake_other_gateway,
                bk_app_code="app1",
                applied_by=FAKE_USERNAME,
                status=ApplyStatusEnum.PENDING.value,
            )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "applied"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert gateway_ids.count(fake_other_gateway.id) == 1

    def test_pending_sorted_by_name(self, request_view, fake_gateway, faker):
        """pending 类型：结果应按名称排序"""
        gw_z = G(
            Gateway,
            name="z_gateway",
            _maintainers=FAKE_USERNAME,
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            tenant_mode="single",
            tenant_id="default",
        )
        gw_a = G(
            Gateway,
            name="a_gateway",
            _maintainers=FAKE_USERNAME,
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            tenant_mode="single",
            tenant_id="default",
        )
        for gateway in [gw_z, gw_a]:
            G(
                AppPermissionApply,
                gateway=gateway,
                bk_app_code="app1",
                applied_by="applicant1",
                status=ApplyStatusEnum.PENDING.value,
            )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        names = [item["name"] for item in result["data"]]
        assert names.index("a_gateway") < names.index("z_gateway")


# ==================== 筛选下拉选项 - MCP Server ====================


class TestWorkbenchMCPServerFilterOptionListApi:
    def test_pending_returns_mcp_servers_from_pending_applies(self, request_view, fake_gateway, fake_mcp_server):
        """pending 类型：返回我的待办权限列表关联的 MCP Server"""
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
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "pending"},
        )
        result = resp.json()

        assert resp.status_code == 200
        mcp_ids = [item["id"] for item in result["data"]]
        assert fake_mcp_server.id in mcp_ids
        # 验证返回了 gateway_id 和 gateway_name
        mcp_item = next(item for item in result["data"] if item["id"] == fake_mcp_server.id)
        assert mcp_item["gateway_id"] == fake_gateway.id
        assert mcp_item["gateway_name"] == fake_gateway.name

    def test_pending_excludes_mcp_servers_without_pending_apply(self, request_view, fake_mcp_server):
        """pending 类型：不返回没有待审批申请的 MCP Server"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "pending"},
        )
        result = resp.json()

        mcp_ids = [item["id"] for item in result["data"]]
        assert fake_mcp_server.id not in mcp_ids

    def test_pending_excludes_non_maintainer_mcp_servers(self, request_view, fake_other_gateway, make_mcp_server):
        """pending 类型：不返回非 maintainer 网关下存在待审批申请的 MCP Server"""
        mcp_server = make_mcp_server(fake_other_gateway)
        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "pending"},
        )
        result = resp.json()

        mcp_ids = [item["id"] for item in result["data"]]
        assert mcp_server.id not in mcp_ids

    def test_applied_returns_mcp_servers_from_my_applies(self, request_view, fake_gateway, fake_mcp_server):
        """applied 类型：返回当前用户申请过的 MCP Server"""
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
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "applied"},
        )
        result = resp.json()

        mcp_ids = [item["id"] for item in result["data"]]
        assert fake_mcp_server.id in mcp_ids
        mcp_item = next(item for item in result["data"] if item["id"] == fake_mcp_server.id)
        assert mcp_item["gateway_id"] == fake_gateway.id
        assert mcp_item["gateway_name"] == fake_gateway.name

    def test_handled_returns_mcp_servers_from_my_handled(self, request_view, fake_gateway, fake_mcp_server):
        """handled 类型：返回当前用户处理过的 MCP Server"""
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
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "handled"},
        )
        result = resp.json()

        mcp_ids = [item["id"] for item in result["data"]]
        assert fake_mcp_server.id in mcp_ids
        mcp_item = next(item for item in result["data"] if item["id"] == fake_mcp_server.id)
        assert mcp_item["gateway_id"] == fake_gateway.id
        assert mcp_item["gateway_name"] == fake_gateway.name

    def test_applied_excludes_deleted(self, request_view, fake_gateway, fake_mcp_server):
        """applied 类型：不返回已删除申请对应的 MCP Server"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=True,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "applied"},
        )
        result = resp.json()

        mcp_ids = [item["id"] for item in result["data"]]
        assert fake_mcp_server.id not in mcp_ids

    def test_invalid_type_returns_400(self, request_view):
        """传入无效 type 值应返回 400"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "invalid_value"},
        )
        assert resp.status_code == 400

    def test_applied_deduplicates_multiple_applies(self, request_view, fake_gateway, fake_mcp_server):
        """applied 类型：同一 MCP Server 多条申请记录应去重"""
        for _ in range(3):
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
            view_name="workbench.filter_options.mcp_servers",
            data={"type": "applied"},
        )
        result = resp.json()

        mcp_ids = [item["id"] for item in result["data"]]
        assert mcp_ids.count(fake_mcp_server.id) == 1


# ==================== 筛选下拉选项 - MCP Server 维度网关 ====================


class TestWorkbenchMCPGatewayFilterOptionListApi:
    def test_pending_returns_gateways_from_pending_mcp_applies(self, request_view, fake_gateway, fake_mcp_server):
        """pending 类型：返回我的待办权限列表关联的网关"""
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
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        assert resp.status_code == 200
        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids

    def test_pending_excludes_gateways_without_pending_mcp_apply(self, request_view, fake_gateway):
        """pending 类型：不返回没有待审批 MCP 申请的网关"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id not in gateway_ids

    def test_pending_excludes_non_maintainer_gateways(self, request_view, fake_other_gateway, make_mcp_server):
        """pending 类型：不返回非 maintainer 网关下存在待审批 MCP 申请的网关"""
        mcp_server = make_mcp_server(fake_other_gateway)
        G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "pending"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_other_gateway.id not in gateway_ids

    def test_applied_returns_gateways_from_mcp_applies(self, request_view, fake_gateway, fake_mcp_server):
        """applied 类型：返回当前用户 MCP 申请关联的网关"""
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
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "applied"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids

    def test_handled_returns_gateways_from_mcp_handled(self, request_view, fake_gateway, fake_mcp_server):
        """handled 类型：返回当前用户处理过的 MCP 申请关联的网关"""
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
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "handled"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id in gateway_ids

    def test_applied_excludes_deleted(self, request_view, fake_gateway, fake_mcp_server):
        """applied 类型：不返回已删除申请对应的网关"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=True,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "applied"},
        )
        result = resp.json()

        gateway_ids = [item["id"] for item in result["data"]]
        assert fake_gateway.id not in gateway_ids

    def test_invalid_type_returns_400(self, request_view):
        """传入无效 type 值应返回 400"""
        resp = request_view(
            method="GET",
            view_name="workbench.filter_options.mcp_gateways",
            data={"type": "invalid_value"},
        )
        assert resp.status_code == 400


# ==================== 我的待办 - API 网关 ====================


class TestWorkbenchPendingGatewayPermissionListApi:
    def test_list(self, request_view, fake_gateway):
        """测试我的待办 - API 网关：当前用户是 maintainer 的网关下有待审批的申请单"""
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
        assert result["data"]["results"][0]["gateway_id"] == fake_gateway.id
        assert result["data"]["results"][0]["gateway_name"] == fake_gateway.name

    def test_list_excludes_non_maintainer_gateway(self, request_view, fake_gateway, fake_other_gateway):
        """测试我的待办 - 不返回非 maintainer 网关的申请"""
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
        """测试我的待办 - 用户名 admin 不应匹配 maintainer 为 superadmin 的网关（子串精确过滤）"""
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
        """测试我的待办 - 不返回已审批或已驳回的申请"""
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
        """测试我的待办 - 按 bk_app_code 筛选"""
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

    def test_list_filter_by_applied_time_range(self, request_view, fake_gateway):
        """测试我的待办 - API 网关按申请时间范围筛选"""
        current_time = now_datetime()
        old_time = current_time - datetime.timedelta(days=2)
        old_apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="old_app",
            applied_by="applicant",
            status=ApplyStatusEnum.PENDING.value,
        )
        AppPermissionApply.objects.filter(id=old_apply.id).update(created_time=old_time)
        current_apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="current_app",
            applied_by="applicant",
            status=ApplyStatusEnum.PENDING.value,
        )
        AppPermissionApply.objects.filter(id=current_apply.id).update(created_time=current_time)

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
            data={
                "time_start": timestamp(current_time - datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time + datetime.timedelta(minutes=1)),
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "current_app"

    def test_list_invalid_time_range(self, request_view):
        """测试我的待办 - API 网关申请时间范围参数非法"""
        current_time = now_datetime()
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
            data={
                "time_start": timestamp(current_time + datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time - datetime.timedelta(minutes=1)),
            },
        )

        assert resp.status_code == 400

    def test_list_empty(self, request_view):
        """测试我的待办 - 空数据"""
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []

    def test_list_with_resource_dimension_returns_resources(self, request_view, fake_gateway):
        """资源维度的申请应返回资源详情列表"""
        resource = G(Resource, gateway=fake_gateway, name="get_apis", path="/api/v1/apis/", method="GET")
        apply_obj = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
        )
        apply_obj.resource_ids = [resource.id]
        apply_obj.save(update_fields=["_resource_ids"])

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        resources = result["data"]["results"][0]["resources"]
        assert len(resources) == 1
        assert resources[0]["name"] == "get_apis"
        assert resources[0]["path"] == "/api/v1/apis/"
        assert resources[0]["method"] == "GET"

    def test_list_with_gateway_dimension_returns_empty_resources(self, request_view, fake_gateway):
        """网关维度的申请应返回空资源列表"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.API.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["resources"] == []


# ==================== 我的待办 - MCP Server ====================


class TestWorkbenchPendingMCPPermissionListApi:
    def test_list(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的待办 - MCP Server：当前用户是 maintainer 的网关下有待审批的 MCP 申请"""
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
        assert result["data"]["results"][0]["mcp_server"]["gateway_id"] == fake_gateway.id
        assert result["data"]["results"][0]["mcp_server"]["gateway_name"] == fake_gateway.name

    def test_list_excludes_substring_maintainer_gateway(self, request_view, fake_substring_gateway, fake_stage, faker):
        """测试我的待办 - MCP Server：用户名 admin 不应匹配 maintainer 为 superadmin 的网关"""
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
        """测试我的待办 - 不返回已删除的 MCP 申请"""
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
        """测试我的待办 - MCP Server 空数据"""
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0
        assert result["data"]["results"] == []

    def test_list_filter_by_gateway_id(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的待办 - MCP Server 按 gateway_id 筛选"""
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        # 使用正确的 gateway_id 筛选
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
            data={"gateway_id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1

        # 使用不存在的 gateway_id 筛选
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
            data={"gateway_id": 99999},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 0

    def test_list_filter_by_applied_time_range(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的待办 - MCP Server 按申请时间范围筛选"""
        current_time = now_datetime()
        old_time = current_time - datetime.timedelta(days=2)
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="old_app",
            applied_by="applicant",
            applied_time=old_time,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="current_app",
            applied_by="applicant",
            applied_time=current_time,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
            data={
                "time_start": timestamp(current_time - datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time + datetime.timedelta(minutes=1)),
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "current_app"

    def test_list_invalid_time_range(self, request_view):
        """测试我的待办 - MCP Server 申请时间范围参数非法"""
        current_time = now_datetime()
        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.pending",
            data={
                "time_start": timestamp(current_time + datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time - datetime.timedelta(minutes=1)),
            },
        )

        assert resp.status_code == 400


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
        assert result["data"]["results"][0]["approvers"] == fake_gateway.maintainers
        assert result["data"]["results"][0]["gateway_id"] == fake_gateway.id
        assert result["data"]["results"][0]["gateway_name"] == fake_gateway.name

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

    def test_list_filter_by_status(self, request_view, fake_gateway):
        """测试我的申请 - API 网关按状态筛选"""
        for status_val in [ApplyStatusEnum.PENDING.value, ApplyStatusEnum.APPROVED.value]:
            G(
                AppPermissionApply,
                gateway=fake_gateway,
                bk_app_code=status_val,
                applied_by=FAKE_USERNAME,
                status=status_val,
            )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
            data={"status": ApplyStatusEnum.APPROVED.value},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["status"] == ApplyStatusEnum.APPROVED.value

    def test_list_filter_by_applied_time_range(self, request_view, fake_gateway):
        """测试我的申请 - API 网关按申请时间范围筛选"""
        current_time = now_datetime()
        old_time = current_time - datetime.timedelta(days=2)
        old_apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="old_app",
            applied_by=FAKE_USERNAME,
            status=ApplyStatusEnum.PENDING.value,
        )
        AppPermissionApply.objects.filter(id=old_apply.id).update(created_time=old_time)
        current_apply = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="current_app",
            applied_by=FAKE_USERNAME,
            status=ApplyStatusEnum.PENDING.value,
        )
        AppPermissionApply.objects.filter(id=current_apply.id).update(created_time=current_time)

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
            data={
                "time_start": timestamp(current_time - datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time + datetime.timedelta(minutes=1)),
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "current_app"

    def test_list_with_resource_dimension_returns_resources(self, request_view, fake_gateway):
        """测试我的申请 - 资源维度应返回资源详情列表"""
        resource = G(Resource, gateway=fake_gateway, name="get_apps", path="/api/v1/apps/", method="GET")
        apply_obj = G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
        )
        apply_obj.resource_ids = [resource.id]
        apply_obj.save()

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        resources = result["data"]["results"][0]["resources"]
        assert len(resources) == 1
        assert resources[0]["name"] == "get_apps"
        assert resources[0]["path"] == "/api/v1/apps/"
        assert resources[0]["method"] == "GET"

    def test_list_with_gateway_dimension_returns_empty_resources(self, request_view, fake_gateway):
        """测试我的申请 - 网关维度应返回空资源列表"""
        G(
            AppPermissionApply,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by=FAKE_USERNAME,
            status=ApplyStatusEnum.PENDING.value,
            grant_dimension=GrantDimensionEnum.API.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.applied",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["resources"] == []


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
        assert result["data"]["results"][0]["approvers"] == fake_gateway.maintainers
        assert result["data"]["results"][0]["mcp_server"]["gateway_id"] == fake_gateway.id
        assert result["data"]["results"][0]["mcp_server"]["gateway_name"] == fake_gateway.name

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

    def test_list_filter_by_status(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的申请 - MCP Server 按状态筛选"""
        for status_val in [
            MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
        ]:
            G(
                MCPServerAppPermissionApply,
                mcp_server=fake_mcp_server,
                bk_app_code=status_val,
                applied_by=FAKE_USERNAME,
                applied_time=now_datetime(),
                status=status_val,
                is_deleted=False,
            )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.applied",
            data={"status": MCPServerAppPermissionApplyStatusEnum.APPROVED.value},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["status"] == MCPServerAppPermissionApplyStatusEnum.APPROVED.value

    def test_list_filter_by_applied_time_range(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的申请 - MCP Server 按申请时间范围筛选"""
        current_time = now_datetime()
        old_time = current_time - datetime.timedelta(days=2)
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="old_app",
            applied_by=FAKE_USERNAME,
            applied_time=old_time,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="current_app",
            applied_by=FAKE_USERNAME,
            applied_time=current_time,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.applied",
            data={
                "time_start": timestamp(current_time - datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time + datetime.timedelta(minutes=1)),
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "current_app"


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
        assert result["data"]["results"][0]["gateway_id"] == fake_gateway.id
        assert result["data"]["results"][0]["gateway_name"] == fake_gateway.name

    def test_list_includes_itsm_records_for_maintainer(self, request_view, fake_gateway, fake_other_gateway):
        """测试我的已办 - API 网关：ITSM 回调无实际审批人，按当前用户维护网关补充可见记录"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="app1",
            applied_by="applicant1",
            applied_time=now_datetime(),
            handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )
        G(
            AppPermissionRecord,
            gateway=fake_other_gateway,
            bk_app_code="app2",
            applied_by="applicant2",
            applied_time=now_datetime(),
            handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "app1"
        assert result["data"]["results"][0]["handled_by"] == ITSM_PERMISSION_APPROVAL_HANDLER

    def test_list_filter_by_status(self, request_view, fake_gateway):
        """测试我的已办 - API 网关：按 status 筛选"""
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="approved_app",
            applied_by="applicant1",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.APPROVED.value,
        )
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="rejected_app",
            applied_by="applicant2",
            applied_time=now_datetime(),
            handled_by=FAKE_USERNAME,
            handled_time=now_datetime(),
            status=ApplyStatusEnum.REJECTED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
            data={"status": ApplyStatusEnum.REJECTED.value},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "rejected_app"

    def test_list_filter_by_applied_time_range(self, request_view, fake_gateway):
        """测试我的已办 - API 网关按申请时间范围筛选"""
        current_time = now_datetime()
        old_time = current_time - datetime.timedelta(days=2)
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="old_app",
            applied_by="applicant1",
            applied_time=old_time,
            handled_by=FAKE_USERNAME,
            handled_time=current_time,
            status=ApplyStatusEnum.APPROVED.value,
        )
        G(
            AppPermissionRecord,
            gateway=fake_gateway,
            bk_app_code="current_app",
            applied_by="applicant2",
            applied_time=current_time,
            handled_by=FAKE_USERNAME,
            handled_time=current_time,
            status=ApplyStatusEnum.APPROVED.value,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
            data={
                "time_start": timestamp(current_time - datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time + datetime.timedelta(minutes=1)),
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "current_app"

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

    def test_list_with_resource_dimension_returns_resources(self, request_view, fake_gateway):
        """已办-资源维度的记录应返回资源详情列表"""
        resource = G(Resource, gateway=fake_gateway, name="create_user", path="/api/v1/users/", method="POST")
        record = G(
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
        record.resource_ids = [resource.id]
        record.save(update_fields=["_resource_ids"])

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.gateway.handled",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        resources = result["data"]["results"][0]["resources"]
        assert len(resources) == 1
        assert resources[0]["name"] == "create_user"
        assert resources[0]["path"] == "/api/v1/users/"
        assert resources[0]["method"] == "POST"


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
        assert result["data"]["results"][0]["mcp_server"]["gateway_id"] == fake_gateway.id
        assert result["data"]["results"][0]["mcp_server"]["gateway_name"] == fake_gateway.name

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

    def test_list_filter_by_applied_time_range(self, request_view, fake_gateway, fake_mcp_server):
        """测试我的已办 - MCP Server 按申请时间范围筛选"""
        current_time = now_datetime()
        old_time = current_time - datetime.timedelta(days=2)
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="old_app",
            applied_by="applicant1",
            applied_time=old_time,
            handled_by=FAKE_USERNAME,
            handled_time=current_time,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=False,
        )
        G(
            MCPServerAppPermissionApply,
            mcp_server=fake_mcp_server,
            bk_app_code="current_app",
            applied_by="applicant2",
            applied_time=current_time,
            handled_by=FAKE_USERNAME,
            handled_time=current_time,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=False,
        )

        resp = request_view(
            method="GET",
            view_name="workbench.permissions.mcp.handled",
            data={
                "time_start": timestamp(current_time - datetime.timedelta(minutes=1)),
                "time_end": timestamp(current_time + datetime.timedelta(minutes=1)),
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 1
        assert result["data"]["results"][0]["bk_app_code"] == "current_app"

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
