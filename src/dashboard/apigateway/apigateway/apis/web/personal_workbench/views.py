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
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.biz.gateway.gateway import GatewayHandler
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.core.models import Gateway
from apigateway.utils.responses import OKJsonResponse

from .constants import WorkbenchFilterTypeEnum
from .filters import (
    WorkbenchGatewayPermissionApplyFilter,
    WorkbenchGatewayPermissionRecordFilter,
    WorkbenchMCPPermissionApplyFilter,
)
from .serializers import (
    WorkbenchFilterOptionQueryInputSLZ,
    WorkbenchGatewayFilterOptionSLZ,
    WorkbenchGatewayPermissionApplyOutputSLZ,
    WorkbenchGatewayPermissionQueryInputSLZ,
    WorkbenchGatewayPermissionRecordOutputSLZ,
    WorkbenchMCPPermissionApplyOutputSLZ,
    WorkbenchMCPPermissionHandledOutputSLZ,
    WorkbenchMCPPermissionQueryInputSLZ,
    WorkbenchMCPServerFilterOptionSLZ,
)


class WorkbenchPermissionMixin:
    """个人工作台权限接口 Mixin

    个人工作台接口无需网关级别权限校验（URL 不含 gateway_id），
    仅需登录认证，因此显式声明 permission_classes = [IsAuthenticated]。
    """

    permission_classes = [IsAuthenticated]


# ========== 筛选下拉选项 ==========


class WorkbenchFilterOptionMixin:
    """筛选下拉选项公共逻辑

    根据 type 参数返回不同数据来源的筛选选项：
    - pending（我的代办）：当前用户作为 maintainer 管理的网关/MCP Server
    - applied（我的申请）：当前用户提交过申请的网关/MCP Server
    - handled（我的已办）：当前用户处理过的网关/MCP Server
    """

    def _get_maintainer_gateway_ids(self):
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)
        gateways = GatewayHandler.list_gateways_by_user(username, tenant_id)
        return [gw.id for gw in gateways]


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 网关下拉筛选选项列表",
        query_serializer=WorkbenchFilterOptionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchGatewayFilterOptionSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchGatewayFilterOptionListApi(WorkbenchPermissionMixin, WorkbenchFilterOptionMixin, generics.ListAPIView):
    """网关下拉筛选选项

    根据 type 参数返回对应数据来源中涉及的网关列表，用于筛选条件下拉框
    """

    serializer_class = WorkbenchGatewayFilterOptionSLZ

    def get_queryset(self):
        filter_type = self.request.query_params.get("type", WorkbenchFilterTypeEnum.PENDING.value)
        username = self.request.user.username

        if filter_type == WorkbenchFilterTypeEnum.APPLIED.value:
            # 我的申请：从用户提交的申请记录中提取去重的网关
            gateway_ids = (
                AppPermissionApply.objects.filter(applied_by=username).values_list("gateway_id", flat=True).distinct()
            )
            return Gateway.objects.filter(id__in=gateway_ids).order_by("name")

        if filter_type == WorkbenchFilterTypeEnum.HANDLED.value:
            # 我的已办：从用户处理过的记录中提取去重的网关
            gateway_ids = (
                AppPermissionRecord.objects.filter(handled_by=username)
                .exclude(status=ApplyStatusEnum.PENDING.value)
                .values_list("gateway_id", flat=True)
                .distinct()
            )
            return Gateway.objects.filter(id__in=gateway_ids).order_by("name")

        # pending（默认）：当前用户作为 maintainer 管理的网关
        tenant_id = get_user_tenant_id(self.request)
        return GatewayHandler.list_gateways_by_user(username, tenant_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        slz = self.get_serializer(queryset, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - MCP Server 下拉筛选选项列表",
        query_serializer=WorkbenchFilterOptionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchMCPServerFilterOptionSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchMCPServerFilterOptionListApi(
    WorkbenchPermissionMixin, WorkbenchFilterOptionMixin, generics.ListAPIView
):
    """MCP Server 下拉筛选选项

    根据 type 参数返回对应数据来源中涉及的 MCP Server 列表，用于筛选条件下拉框
    """

    serializer_class = WorkbenchMCPServerFilterOptionSLZ

    def get_queryset(self):
        filter_type = self.request.query_params.get("type", WorkbenchFilterTypeEnum.PENDING.value)
        username = self.request.user.username

        if filter_type == WorkbenchFilterTypeEnum.APPLIED.value:
            # 我的申请：从用户提交的申请记录中提取去重的 MCP Server
            mcp_server_ids = (
                MCPServerAppPermissionApply.objects.filter(applied_by=username, is_deleted=False)
                .values_list("mcp_server_id", flat=True)
                .distinct()
            )
            return MCPServer.objects.filter(id__in=mcp_server_ids).order_by("name")

        if filter_type == WorkbenchFilterTypeEnum.HANDLED.value:
            # 我的已办：从用户处理过的记录中提取去重的 MCP Server
            mcp_server_ids = (
                MCPServerAppPermissionApply.objects.filter(handled_by=username, is_deleted=False)
                .exclude(status=MCPServerAppPermissionApplyStatusEnum.PENDING.value)
                .values_list("mcp_server_id", flat=True)
                .distinct()
            )
            return MCPServer.objects.filter(id__in=mcp_server_ids).order_by("name")

        # pending（默认）：当前用户作为 maintainer 管理的网关下的 MCP Server
        gateway_ids = self._get_maintainer_gateway_ids()
        return MCPServer.objects.filter(gateway_id__in=gateway_ids).order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        slz = self.get_serializer(queryset, many=True)
        return OKJsonResponse(data=slz.data)


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
