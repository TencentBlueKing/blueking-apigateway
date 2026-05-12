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

from typing import List

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.core.models import Gateway

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


def _get_user_maintainer_gateway_ids(username: str) -> List[int]:
    """获取当前用户作为 maintainer 的所有网关 ID

    _maintainers 是以 `;` 拼接的字符串，contains 查询可能匹配到子串（如 admin 匹配 superadmin），
    因此先用 contains 粗筛，再通过 has_permission 做精确过滤，与 GatewayHandler.list_gateways_by_user 逻辑保持一致。
    """
    gateways = Gateway.objects.filter(_maintainers__contains=username)
    return [gw.id for gw in gateways if gw.has_permission(username)]


class BaseWorkbenchListApi(generics.ListAPIView):
    """个人工作台列表接口基类

    子类只需声明 filterset_class / serializer_class / get_queryset()，
    list 的分页+序列化逻辑统一在此处理，减少重复代码。
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


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
        gateway_ids = _get_user_maintainer_gateway_ids(username)
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
        gateway_ids = _get_user_maintainer_gateway_ids(username)
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
                status__in=[
                    MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
                    MCPServerAppPermissionApplyStatusEnum.REJECTED.value,
                ],
                is_deleted=False,
            )
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-handled_time")
        )
