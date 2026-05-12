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

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.biz.gateway.gateway import GatewayHandler
from apigateway.common.tenant.request import get_user_tenant_id

from .filters import (
    WorkbenchGatewayPermissionApplyFilter,
    WorkbenchGatewayPermissionRecordFilter,
    WorkbenchMCPPermissionApplyFilter,
)
from .serializers import (
    WorkbenchGatewayPermissionApplyOutputSLZ,
    WorkbenchGatewayPermissionQueryInputSLZ,
    WorkbenchGatewayPermissionRecordOutputSLZ,
    WorkbenchMCPPermissionApplyOutputSLZ,
    WorkbenchMCPPermissionHandledOutputSLZ,
    WorkbenchMCPPermissionQueryInputSLZ,
)


def _get_user_maintainer_gateway_ids(username: str, tenant_id: str = "") -> list[int]:
    """获取当前用户作为 maintainer 的所有网关 ID

    复用 GatewayHandler.list_gateways_by_user，该方法内部已处理：
    1. _maintainers__contains 粗筛 + has_permission 精确过滤（避免子串误匹配）
    2. tenant_id 维度的数据隔离（多租户场景）
    """
    if not username:
        return []
    gateways = GatewayHandler.list_gateways_by_user(username, tenant_id)
    return [gw.id for gw in gateways]


class BaseWorkbenchListApi(generics.ListAPIView):
    """个人工作台列表接口基类

    子类只需声明 filterset_class / serializer_class / get_queryset()，
    分页+序列化逻辑由 DRF ListAPIView 默认 list() 处理。

    个人工作台接口无需网关级别权限校验（URL 不含 gateway_id），
    仅需登录认证，因此显式声明 permission_classes = [IsAuthenticated]。
    """

    permission_classes = [IsAuthenticated]


# ========== 我的代办 ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的代办 - API 网关权限申请列表",
        query_serializer=WorkbenchGatewayPermissionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchGatewayPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchPendingGatewayPermissionListApi(BaseWorkbenchListApi):
    """我的代办 - API 网关

    展示当前用户作为网关管理员（maintainer）待审批的权限申请单
    """

    serializer_class = WorkbenchGatewayPermissionApplyOutputSLZ
    filterset_class = WorkbenchGatewayPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)
        gateway_ids = _get_user_maintainer_gateway_ids(username, tenant_id)
        return (
            AppPermissionApply.objects.filter(
                gateway_id__in=gateway_ids,
                status=ApplyStatusEnum.PENDING.value,
            )
            .select_related("gateway")
            .order_by("-id")
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的代办 - MCP Server 权限申请列表",
        query_serializer=WorkbenchMCPPermissionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchMCPPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchPendingMCPPermissionListApi(BaseWorkbenchListApi):
    """我的代办 - MCP Server

    展示当前用户作为 MCP Server 所属网关管理员待审批的申请单
    """

    serializer_class = WorkbenchMCPPermissionApplyOutputSLZ
    filterset_class = WorkbenchMCPPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)
        gateway_ids = _get_user_maintainer_gateway_ids(username, tenant_id)
        return (
            MCPServerAppPermissionApply.objects.filter(
                mcp_server__gateway_id__in=gateway_ids,
                status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
                is_deleted=False,
            )
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-id")
        )


# ========== 我的申请 ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的申请 - API 网关权限申请列表",
        query_serializer=WorkbenchGatewayPermissionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchGatewayPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchMyApplyGatewayPermissionListApi(BaseWorkbenchListApi):
    """我的申请 - API 网关

    展示当前用户自己提交的权限申请
    """

    serializer_class = WorkbenchGatewayPermissionApplyOutputSLZ
    filterset_class = WorkbenchGatewayPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        return AppPermissionApply.objects.filter(applied_by=username).select_related("gateway").order_by("-id")


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的申请 - MCP Server 权限申请列表",
        query_serializer=WorkbenchMCPPermissionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchMCPPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchMyApplyMCPPermissionListApi(BaseWorkbenchListApi):
    """我的申请 - MCP Server

    展示当前用户自己提交的 MCP Server 权限申请
    """

    serializer_class = WorkbenchMCPPermissionApplyOutputSLZ
    filterset_class = WorkbenchMCPPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        return (
            MCPServerAppPermissionApply.objects.filter(
                applied_by=username,
                is_deleted=False,
            )
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-id")
        )


# ========== 我的已办 ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的已办 - API 网关权限申请列表",
        query_serializer=WorkbenchGatewayPermissionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchGatewayPermissionRecordOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchHandledGatewayPermissionListApi(BaseWorkbenchListApi):
    """我的已办 - API 网关

    展示当前用户已处理过的权限申请记录
    """

    serializer_class = WorkbenchGatewayPermissionRecordOutputSLZ
    filterset_class = WorkbenchGatewayPermissionRecordFilter

    def get_queryset(self):
        username = self.request.user.username
        return (
            AppPermissionRecord.objects.filter(handled_by=username)
            .exclude(status=ApplyStatusEnum.PENDING.value)
            .select_related("gateway")
            .order_by("-handled_time")
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的已办 - MCP Server 权限申请列表",
        query_serializer=WorkbenchMCPPermissionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchMCPPermissionHandledOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchHandledMCPPermissionListApi(BaseWorkbenchListApi):
    """我的已办 - MCP Server

    展示当前用户已处理的 MCP Server 权限申请
    """

    serializer_class = WorkbenchMCPPermissionHandledOutputSLZ
    filterset_class = WorkbenchMCPPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        return (
            MCPServerAppPermissionApply.objects.filter(
                handled_by=username,
                is_deleted=False,
            )
            .exclude(status=MCPServerAppPermissionApplyStatusEnum.PENDING.value)
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-handled_time")
        )
