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


class WorkbenchPermissionMixin:
    """个人工作台权限接口 Mixin

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
class WorkbenchPendingGatewayPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
    """我的代办 - API 网关

    展示当前用户作为网关管理员（maintainer）待审批的权限申请单
    """

    serializer_class = WorkbenchGatewayPermissionApplyOutputSLZ
    filterset_class = WorkbenchGatewayPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)
        gateways = GatewayHandler.list_gateways_by_user(username, tenant_id)
        gateway_ids = [gw.id for gw in gateways]
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
class WorkbenchPendingMCPPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
    """我的代办 - MCP Server

    展示当前用户作为 MCP Server 所属网关管理员待审批的申请单
    """

    serializer_class = WorkbenchMCPPermissionApplyOutputSLZ
    filterset_class = WorkbenchMCPPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)
        gateways = GatewayHandler.list_gateways_by_user(username, tenant_id)
        gateway_ids = [gw.id for gw in gateways]
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
class WorkbenchMyApplyGatewayPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
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
class WorkbenchMyApplyMCPPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
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
class WorkbenchHandledGatewayPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
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
class WorkbenchHandledMCPPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
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
