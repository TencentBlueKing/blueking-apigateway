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
from django.urls import URLPattern, URLResolver, get_resolver

from apigateway.apis.web.access_log import views as access_log_views
from apigateway.apis.web.gateway import views as gateway_views
from apigateway.apis.web.gateway_user_permission import views as gateway_user_permission_views
from apigateway.apis.web.mcp_server import views as mcp_server_views
from apigateway.apis.web.mcp_server_log import views as mcp_server_log_views
from apigateway.apis.web.mcp_server_metrics import views as mcp_server_metrics_views
from apigateway.apis.web.metrics import views as metrics_views
from apigateway.apis.web.monitor import views as monitor_views
from apigateway.apis.web.permission import views as permission_views
from apigateway.apps.rbac.constants import GatewayActionEnum

WEB_GATEWAY_URL_PREFIX = "backend/gateways/"

OPERATE_VIEWS = (
    access_log_views.LogTimeChartRetrieveApi,
    access_log_views.SearchLogListApi,
    access_log_views.LogExportApi,
    gateway_user_permission_views.GatewayUserRoleRetrieveApi,
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

# 未声明 Action 的网关内接口默认 manage_gateway。新增接口若也走默认值，必须把 FQCN 加进这里。
MANAGE_DEFAULT_VIEW_FQCNS = frozenset(
    {
        "apigateway.apis.web.ai_completion.views.AICompletionCreateApi",
        "apigateway.apis.web.ai_completion.views.BatchTranslateApi",
        "apigateway.apis.web.api_test.views.APIDebugHistoryListApi",
        "apigateway.apis.web.api_test.views.APIDebugHistoryRetrieveDestroyApi",
        "apigateway.apis.web.api_test.views.APITestApi",
        "apigateway.apis.web.audit.views.AuditEventLogListApi",
        "apigateway.apis.web.backend.views.BackendConnectivityTestApi",
        "apigateway.apis.web.backend.views.BackendListCreateApi",
        "apigateway.apis.web.backend.views.BackendRetrieveUpdateDestroyApi",
        "apigateway.apis.web.gateway.views.GatewayDevGuidelineRetrieveApi",
        "apigateway.apis.web.gateway.views.GatewayReleasingStatusApi",
        "apigateway.apis.web.gateway.views.GatewayTenantAppListApi",
        "apigateway.apis.web.gateway.views.GatewayUpdateStatusApi",
        "apigateway.apis.web.gateway_member.views.GatewayMemberListCreateApi",
        "apigateway.apis.web.gateway_member.views.GatewayMemberUpdateDestroyApi",
        "apigateway.apis.web.label.views.GatewayLabelListCreateApi",
        "apigateway.apis.web.label.views.GatewayLabelRetrieveUpdateDestroyApi",
        "apigateway.apis.web.mcp_server.views.MCPServerBatchConfigApi",
        "apigateway.apis.web.mcp_server.views.MCPServerCategoriesListApi",
        "apigateway.apis.web.mcp_server.views.MCPServerConfigListApi",
        "apigateway.apis.web.mcp_server.views.MCPServerFilterOptionsApi",
        "apigateway.apis.web.mcp_server.views.MCPServerGuidelineRetrieveApi",
        "apigateway.apis.web.mcp_server.views.MCPServerListCreateApi",
        "apigateway.apis.web.mcp_server.views.MCPServerRemotePromptsBatchApi",
        "apigateway.apis.web.mcp_server.views.MCPServerRemotePromptsListApi",
        "apigateway.apis.web.mcp_server.views.MCPServerRetrieveUpdateDestroyApi",
        "apigateway.apis.web.mcp_server.views.MCPServerStageReleaseCheckApi",
        "apigateway.apis.web.mcp_server.views.MCPServerToolDocRetrieveApi",
        "apigateway.apis.web.mcp_server.views.MCPServerToolsListApi",
        "apigateway.apis.web.mcp_server.views.MCPServerUpdateStatusApi",
        "apigateway.apis.web.mcp_server.views.MCPServerUserCustomDocApi",
        "apigateway.apis.web.monitor.views.AlarmStrategyListCreateApi",
        "apigateway.apis.web.monitor.views.AlarmStrategyRetrieveUpdateDestroyApi",
        "apigateway.apis.web.monitor.views.AlarmStrategyUpdateStatusApi",
        "apigateway.apis.web.plugin.views.PluginBindingListApi",
        "apigateway.apis.web.plugin.views.PluginConfigCreateApi",
        "apigateway.apis.web.plugin.views.PluginConfigRetrieveUpdateDestroyApi",
        "apigateway.apis.web.plugin.views.PluginTypeListApi",
        "apigateway.apis.web.plugin.views.PluginTypeTagsListApi",
        "apigateway.apis.web.plugin.views.ScopePluginConfigListApi",
        "apigateway.apis.web.release.views.DeployHistoryListApi",
        "apigateway.apis.web.release.views.DeployIdEventsRetrieveApi",
        "apigateway.apis.web.release.views.HistoryIdEventsRetrieveApi",
        "apigateway.apis.web.release.views.ProgrammableDeployCreateApi",
        "apigateway.apis.web.release.views.ProgrammableDeployRetrieveApi",
        "apigateway.apis.web.release.views.ReleaseAvailableResourceListApi",
        "apigateway.apis.web.release.views.ReleaseAvailableResourceSchemaRetrieveApi",
        "apigateway.apis.web.release.views.ReleaseCreateApi",
        "apigateway.apis.web.release.views.ReleaseHistoryListApi",
        "apigateway.apis.web.release.views.RelishHistoryEventsRetrieveAPI",
        "apigateway.apis.web.resource.doc.views.DocListCreateApi",
        "apigateway.apis.web.resource.doc.views.DocUpdateDestroyApi",
        "apigateway.apis.web.resource.views.BackendPathCheckApi",
        "apigateway.apis.web.resource.views.ResourceBatchUpdateDestroyApi",
        "apigateway.apis.web.resource.views.ResourceExportApi",
        "apigateway.apis.web.resource.views.ResourceImportApi",
        "apigateway.apis.web.resource.views.ResourceImportCheckApi",
        "apigateway.apis.web.resource.views.ResourceImportDocPreviewApi",
        "apigateway.apis.web.resource.views.ResourceLabelUpdateApi",
        "apigateway.apis.web.resource.views.ResourceListCreateApi",
        "apigateway.apis.web.resource.views.ResourceRetrieveUpdateDestroyApi",
        "apigateway.apis.web.resource.views.ResourcesWithVerifiedUserRequiredApi",
        "apigateway.apis.web.resource_doc.views.DocArchiveParseApi",
        "apigateway.apis.web.resource_doc.views.DocExportApi",
        "apigateway.apis.web.resource_doc.views.DocImportByArchiveApi",
        "apigateway.apis.web.resource_doc.views.DocImportBySwaggerApi",
        "apigateway.apis.web.resource_version.views.NextProgramGatewayResourceVersionRetrieveApi",
        "apigateway.apis.web.resource_version.views.NextResourceVersionRetrieveApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionBatchDeleteApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionDiffRetrieveApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionDocExportApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionExportApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionListCreateApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionNeedNewVersionRetrieveApi",
        "apigateway.apis.web.resource_version.views.ResourceVersionRetrieveDestroyApi",
        "apigateway.apis.web.sdk.views.GatewaySDKListCreateApi",
        "apigateway.apis.web.stage.views.ProgrammableStageDeployRetrieveApi",
        "apigateway.apis.web.stage.views.StageBackendListApi",
        "apigateway.apis.web.stage.views.StageBackendRetrieveUpdateApi",
        "apigateway.apis.web.stage.views.StageListCreateApi",
        "apigateway.apis.web.stage.views.StageRetrieveUpdateDestroyApi",
        "apigateway.apis.web.stage.views.StageStatusUpdateApi",
        "apigateway.apis.web.stage.views.StageVarsRetrieveUpdateApi",
    }
)


def _iter_url_patterns(resolver, prefix=""):
    for pattern in resolver.url_patterns:
        path = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            yield from _iter_url_patterns(pattern, path)
        elif isinstance(pattern, URLPattern):
            yield path, pattern


def _view_class_from_callback(callback):
    return getattr(callback, "cls", None) or getattr(callback, "view_class", None)


def _fqcn(view_class) -> str:
    return f"{view_class.__module__}.{view_class.__name__}"


def _declared_gateway_actions(view_class):
    actions = []
    gateway_action = getattr(view_class, "gateway_action", None)
    if gateway_action:
        actions.append(gateway_action)
    actions.extend((getattr(view_class, "gateway_action_map", None) or {}).values())
    return actions


def _iter_web_gateway_view_classes():
    seen = set()
    for path, pattern in _iter_url_patterns(get_resolver()):
        if WEB_GATEWAY_URL_PREFIX not in path or "gateway_id" not in path:
            continue
        view_class = _view_class_from_callback(pattern.callback)
        if view_class is None:
            raise AssertionError(f"gateway route has no view class: {path}")
        if view_class in seen:
            continue
        seen.add(view_class)
        yield view_class


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


def test_web_gateway_urlconf_actions_are_valid_and_explicit():
    valid_actions = set(GatewayActionEnum.get_values())
    undeclared = set()
    invalid = []

    for view_class in _iter_web_gateway_view_classes():
        if getattr(view_class, "gateway_permission_exempt", False):
            continue
        actions = _declared_gateway_actions(view_class)
        if not actions:
            undeclared.add(_fqcn(view_class))
            continue
        invalid.extend((_fqcn(view_class), action) for action in actions if action not in valid_actions)

    assert invalid == [], f"invalid gateway_action declarations: {invalid}"
    assert undeclared == MANAGE_DEFAULT_VIEW_FQCNS, (
        "unlabeled gateway views must be confirmed as manage_gateway defaults: "
        f"new={sorted(undeclared - MANAGE_DEFAULT_VIEW_FQCNS)}; "
        f"stale={sorted(MANAGE_DEFAULT_VIEW_FQCNS - undeclared)}"
    )
