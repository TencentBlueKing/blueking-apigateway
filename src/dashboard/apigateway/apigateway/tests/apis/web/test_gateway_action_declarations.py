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
import pytest

from apigateway.apis.web.access_log import views as access_log_views
from apigateway.apis.web.gateway import views as gateway_views
from apigateway.apis.web.mcp_server import views as mcp_server_views
from apigateway.apis.web.mcp_server_log import views as mcp_server_log_views
from apigateway.apis.web.mcp_server_metrics import views as mcp_server_metrics_views
from apigateway.apis.web.metrics import views as metrics_views
from apigateway.apis.web.monitor import views as monitor_views
from apigateway.apis.web.permission import views as permission_views
from apigateway.apps.rbac.constants import GatewayActionEnum

OPERATE_VIEWS = (
    access_log_views.LogTimeChartRetrieveApi,
    access_log_views.SearchLogListApi,
    access_log_views.LogExportApi,
    access_log_views.LogDetailRetrieveApi,
    access_log_views.LogLinkRetrieveApi,
    metrics_views.QueryRangeApi,
    metrics_views.QueryInstantApi,
    metrics_views.QuerySummaryApi,
    metrics_views.QuerySummaryCallerListApi,
    metrics_views.QuerySummaryExportApi,
    monitor_views.AlarmRecordListApi,
    monitor_views.AlarmRecordRetrieveApi,
    mcp_server_metrics_views.MCPServerQueryRangeApi,
    mcp_server_metrics_views.MCPServerQueryInstantApi,
    mcp_server_log_views.MCPServerLogTimeChartRetrieveApi,
    mcp_server_log_views.MCPServerSearchLogListApi,
    mcp_server_log_views.MCPServerLogExportApi,
    mcp_server_log_views.MCPServerLogDetailApi,
    mcp_server_log_views.MCPServerLogTraceApi,
    mcp_server_log_views.MCPServerLogChainApi,
)

APPROVE_VIEWS = (
    permission_views.AppPermissionListApi,
    permission_views.AppPermissionRenewApi,
    permission_views.AppPermissionAppCodeListApi,
    permission_views.AppPermissionExportApi,
    permission_views.AppPermissionDeleteApi,
    permission_views.AppResourcePermissionCreateApi,
    permission_views.AppResourcePermissionRenewApi,
    permission_views.AppResourcePermissionDeleteApi,
    permission_views.AppGatewayPermissionCreateApi,
    permission_views.AppGatewayPermissionRenewApi,
    permission_views.AppGatewayPermissionDeleteApi,
    permission_views.AppPermissionApplyListApi,
    permission_views.AppPermissionApplyRetrieveApi,
    permission_views.AppPermissionRecordListApi,
    permission_views.AppPermissionRecordRetrieveApi,
    permission_views.AppPermissionApplyApprovalApi,
    mcp_server_views.MCPServerAppPermissionListCreateApi,
    mcp_server_views.MCPServerAppPermissionDestroyApi,
    mcp_server_views.MCPServerAppPermissionApplyListApi,
    mcp_server_views.MCPServerAppPermissionApplyApplicantListApi,
    mcp_server_views.MCPServerAppPermissionApplyUpdateStatusApi,
    mcp_server_views.MCPServerAppPermissionAppCodeListApi,
    mcp_server_views.GatewayMCPServerAppPermissionListApi,
    mcp_server_views.GatewayMCPServerAppPermissionExportApi,
)


@pytest.mark.parametrize("view_class", OPERATE_VIEWS)
def test_operate_gateway_action_declarations(view_class):
    assert view_class.gateway_action == GatewayActionEnum.OPERATE_GATEWAY.value


@pytest.mark.parametrize("view_class", APPROVE_VIEWS)
def test_approve_gateway_action_declarations(view_class):
    assert view_class.gateway_action == GatewayActionEnum.APPROVE_GATEWAY_PERMISSION.value


def test_gateway_detail_get_uses_operate_action():
    assert gateway_views.GatewayRetrieveUpdateDestroyApi.gateway_action_map == {
        "GET": GatewayActionEnum.OPERATE_GATEWAY.value
    }
