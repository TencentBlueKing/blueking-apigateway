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

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply
from apigateway.biz.mcp_server import MCPServerPermissionHandler
from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.biz.personal_workbench import WorkbenchPermissionHandler
from apigateway.common.tenant.query import (
    gateway_filter_by_app_tenant_id,
    gateway_filter_by_maintainer_tenant_id,
    gateway_mcp_server_filter_by_user_tenant_id,
    gateway_related_filter_by_maintainer_tenant_id,
    gateway_related_filter_by_user_tenant_id,
    mcp_server_related_filter_by_user_tenant_id,
)
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.core.models import Gateway, Resource
from apigateway.utils.responses import OKJsonResponse

from .constants import WorkbenchFilterTypeEnum
from .filters import (
    WorkbenchGatewayPendingPermissionApplyFilter,
    WorkbenchGatewayPermissionApplyFilter,
    WorkbenchGatewayPermissionRecordFilter,
    WorkbenchMCPPendingPermissionApplyFilter,
    WorkbenchMCPPermissionApplyFilter,
)
from .serializers import (
    WorkbenchFilterOptionQueryInputSLZ,
    WorkbenchGatewayFilterOptionSLZ,
    WorkbenchGatewayPermissionApplyOutputSLZ,
    WorkbenchGatewayPermissionRecordOutputSLZ,
    WorkbenchMCPPermissionApplyOutputSLZ,
    WorkbenchMCPPermissionHandledOutputSLZ,
    WorkbenchMCPServerFilterOptionSLZ,
)


class WorkbenchPermissionMixin:
    """个人工作台权限接口 Mixin

    个人工作台接口无需网关级别权限校验（URL 不含 gateway_id），
    仅需登录认证，因此显式声明 permission_classes = [IsAuthenticated]。
    """

    permission_classes = [IsAuthenticated]

    def _get_pending_gateway_permission_apply_queryset(self):
        """获取当前用户待审批的 API 网关权限申请列表"""
        return ResourcePermissionHandler.get_pending_apply_queryset_for_maintainer(
            self.request.user.username,
            get_user_tenant_id(self.request),
        )

    def _get_pending_mcp_permission_apply_queryset(self):
        """获取当前用户待审批的 MCP Server 权限申请列表"""
        return MCPServerPermissionHandler.get_pending_apply_queryset_for_gateway_maintainer(
            self.request.user.username,
            get_user_tenant_id(self.request),
        )


class ResourcePrefetchMixin:
    """批量预取资源详情 Mixin

    解决列表接口中 N 条资源维度记录各自触发 DB 查询的 N+1 问题。
    在 list 方法中对分页后的对象批量收集 resource_ids，一次性查出资源详情，
    通过 serializer context 中的 prefetched_resources 传入。
    """

    def _prefetch_resources(self, queryset) -> dict:
        """从 queryset 中收集所有 resource_id 并批量查询，返回 {id: resource_dict} 映射"""
        all_resource_ids = set()
        for obj in queryset:
            if obj.grant_dimension == GrantDimensionEnum.RESOURCE.value:
                all_resource_ids.update(obj.resource_ids)

        if not all_resource_ids:
            return {}

        resources = Resource.objects.filter(id__in=all_resource_ids).values("id", "name", "path", "method")
        return {r["id"]: r for r in resources}

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        items = page if page is not None else queryset

        prefetched_resources = self._prefetch_resources(items)
        context = self.get_serializer_context()
        context["prefetched_resources"] = prefetched_resources
        serializer = self.get_serializer(items, many=True, context=context)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return OKJsonResponse(data=serializer.data)


# ========== 筛选下拉选项 ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 网关下拉筛选选项列表",
        query_serializer=WorkbenchFilterOptionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchGatewayFilterOptionSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchGatewayFilterOptionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
    """网关下拉筛选选项

    根据 type 参数返回对应数据来源中涉及的网关列表，用于筛选条件下拉框
    """

    serializer_class = WorkbenchGatewayFilterOptionSLZ
    filter_backends: list[type] = []

    def get_queryset(self):
        slz = WorkbenchFilterOptionQueryInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        filter_type = slz.validated_data.get("type", WorkbenchFilterTypeEnum.PENDING.value)
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)

        if filter_type == WorkbenchFilterTypeEnum.APPLIED.value:
            # 我的申请：从用户提交的申请记录中提取去重的网关
            gateway_ids = (
                AppPermissionApply.objects.filter(applied_by=username).values_list("gateway_id", flat=True).distinct()
            )
            queryset = Gateway.objects.filter(id__in=gateway_ids).order_by("name")
            return gateway_filter_by_app_tenant_id(queryset, tenant_id)

        if filter_type == WorkbenchFilterTypeEnum.HANDLED.value:
            # 我的已办：从用户处理过的记录中提取去重的网关；ITSM 回调无实际审批人，按当前用户维护的网关补充
            queryset = WorkbenchPermissionHandler.get_handled_gateway_permission_record_queryset(username, tenant_id)
            gateway_ids = queryset.values_list("gateway_id", flat=True).distinct()
            queryset = Gateway.objects.filter(id__in=gateway_ids).order_by("name")
            return gateway_filter_by_maintainer_tenant_id(queryset, tenant_id)

        # pending（默认）：从当前用户待审批的 API 网关权限申请中提取去重的网关
        gateway_ids = (
            self._get_pending_gateway_permission_apply_queryset().values_list("gateway_id", flat=True).distinct()
        )
        return Gateway.objects.filter(id__in=gateway_ids).order_by("name")

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
class WorkbenchMCPServerFilterOptionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
    """MCP Server 下拉筛选选项

    根据 type 参数返回对应数据来源中涉及的 MCP Server 列表，用于筛选条件下拉框
    """

    serializer_class = WorkbenchMCPServerFilterOptionSLZ
    filter_backends: list[type] = []

    def get_queryset(self):
        slz = WorkbenchFilterOptionQueryInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        filter_type = slz.validated_data.get("type", WorkbenchFilterTypeEnum.PENDING.value)
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)

        if filter_type == WorkbenchFilterTypeEnum.APPLIED.value:
            # 我的申请：从用户提交的申请记录中提取去重的 MCP Server
            mcp_server_ids = (
                MCPServerAppPermissionApply.objects.filter(applied_by=username, is_deleted=False)
                .values_list("mcp_server_id", flat=True)
                .distinct()
            )
            queryset = MCPServer.objects.select_related("gateway").filter(id__in=mcp_server_ids).order_by("name")
            return gateway_mcp_server_filter_by_user_tenant_id(queryset, tenant_id)

        if filter_type == WorkbenchFilterTypeEnum.HANDLED.value:
            # 我的已办：从管理员处理过的记录中提取去重的 MCP Server；ITSM 回调无实际审批人，按当前用户维护的网关补充
            mcp_server_ids = (
                WorkbenchPermissionHandler.get_handled_mcp_permission_apply_queryset(username, tenant_id)
                .values_list("mcp_server_id", flat=True)
                .distinct()
            )
            queryset = MCPServer.objects.select_related("gateway").filter(id__in=mcp_server_ids).order_by("name")
            return gateway_related_filter_by_maintainer_tenant_id(queryset, tenant_id)

        # pending（默认）：从当前用户待审批的 MCP Server 权限申请中提取去重的 MCP Server
        mcp_server_ids = (
            self._get_pending_mcp_permission_apply_queryset().values_list("mcp_server_id", flat=True).distinct()
        )
        return MCPServer.objects.select_related("gateway").filter(id__in=mcp_server_ids).order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        slz = self.get_serializer(queryset, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - MCP Server 维度网关下拉筛选选项列表",
        query_serializer=WorkbenchFilterOptionQueryInputSLZ,
        responses={status.HTTP_200_OK: WorkbenchGatewayFilterOptionSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchMCPGatewayFilterOptionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
    """MCP Server 维度 - 网关下拉筛选选项

    根据 type 参数返回 MCP Server 权限申请中涉及的网关列表，用于筛选条件下拉框
    """

    serializer_class = WorkbenchGatewayFilterOptionSLZ
    filter_backends: list[type] = []

    def get_queryset(self):
        slz = WorkbenchFilterOptionQueryInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        filter_type = slz.validated_data.get("type", WorkbenchFilterTypeEnum.PENDING.value)
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)

        if filter_type == WorkbenchFilterTypeEnum.APPLIED.value:
            # 我的申请：从用户提交的 MCP 申请记录中提取去重的网关
            gateway_ids = (
                MCPServerAppPermissionApply.objects.filter(applied_by=username, is_deleted=False)
                .values_list("mcp_server__gateway_id", flat=True)
                .distinct()
            )
            queryset = Gateway.objects.filter(id__in=gateway_ids).order_by("name")
            return gateway_filter_by_app_tenant_id(queryset, tenant_id)

        if filter_type == WorkbenchFilterTypeEnum.HANDLED.value:
            # 我的已办：从用户处理过的 MCP 记录中提取去重的网关；ITSM 回调无实际审批人，按当前用户维护的网关补充
            gateway_ids = (
                WorkbenchPermissionHandler.get_handled_mcp_permission_apply_queryset(username, tenant_id)
                .values_list("mcp_server__gateway_id", flat=True)
                .distinct()
            )
            queryset = Gateway.objects.filter(id__in=gateway_ids).order_by("name")
            return gateway_filter_by_maintainer_tenant_id(queryset, tenant_id)

        # pending（默认）：从当前用户待审批的 MCP Server 权限申请中提取去重的网关
        gateway_ids = (
            self._get_pending_mcp_permission_apply_queryset()
            .values_list("mcp_server__gateway_id", flat=True)
            .distinct()
        )
        return Gateway.objects.filter(id__in=gateway_ids).order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        slz = self.get_serializer(queryset, many=True)
        return OKJsonResponse(data=slz.data)


# ========== 我的待办 ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的待办 - API 网关权限申请列表",
        responses={status.HTTP_200_OK: WorkbenchGatewayPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchPendingGatewayPermissionListApi(ResourcePrefetchMixin, WorkbenchPermissionMixin, generics.ListAPIView):
    """我的待办 - API 网关

    展示当前用户作为网关管理员（maintainer）待审批的权限申请单
    """

    serializer_class = WorkbenchGatewayPermissionApplyOutputSLZ
    filterset_class = WorkbenchGatewayPendingPermissionApplyFilter

    def get_queryset(self):
        return self._get_pending_gateway_permission_apply_queryset().select_related("gateway").order_by("-id")


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的待办 - MCP Server 权限申请列表",
        responses={status.HTTP_200_OK: WorkbenchMCPPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchPendingMCPPermissionListApi(WorkbenchPermissionMixin, generics.ListAPIView):
    """我的待办 - MCP Server

    展示当前用户作为 MCP Server 所属网关管理员待审批的申请单
    """

    serializer_class = WorkbenchMCPPermissionApplyOutputSLZ
    filterset_class = WorkbenchMCPPendingPermissionApplyFilter

    def get_queryset(self):
        return (
            self._get_pending_mcp_permission_apply_queryset()
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-id")
        )


# ========== 我的申请 ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的申请 - API 网关权限申请列表",
        responses={status.HTTP_200_OK: WorkbenchGatewayPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchMyApplyGatewayPermissionListApi(ResourcePrefetchMixin, WorkbenchPermissionMixin, generics.ListAPIView):
    """我的申请 - API 网关

    展示当前用户自己提交的权限申请
    """

    serializer_class = WorkbenchGatewayPermissionApplyOutputSLZ
    filterset_class = WorkbenchGatewayPermissionApplyFilter

    def get_queryset(self):
        username = self.request.user.username
        tenant_id = get_user_tenant_id(self.request)
        queryset = AppPermissionApply.objects.filter(applied_by=username).select_related("gateway").order_by("-id")
        return gateway_related_filter_by_user_tenant_id(queryset, tenant_id)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的申请 - MCP Server 权限申请列表",
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
        tenant_id = get_user_tenant_id(self.request)
        queryset = (
            MCPServerAppPermissionApply.objects.filter(
                applied_by=username,
                is_deleted=False,
            )
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-id")
        )
        return mcp_server_related_filter_by_user_tenant_id(queryset, tenant_id)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的已办 - API 网关权限申请列表",
        responses={status.HTTP_200_OK: WorkbenchGatewayPermissionRecordOutputSLZ(many=True)},
        tags=["WebAPI.PersonalWorkbench"],
    ),
)
class WorkbenchHandledGatewayPermissionListApi(ResourcePrefetchMixin, WorkbenchPermissionMixin, generics.ListAPIView):
    """我的已办 - API 网关

    展示当前用户已处理过的权限申请记录
    """

    serializer_class = WorkbenchGatewayPermissionRecordOutputSLZ
    filterset_class = WorkbenchGatewayPermissionRecordFilter

    def get_queryset(self):
        return (
            WorkbenchPermissionHandler.get_handled_gateway_permission_record_queryset(
                self.request.user.username,
                get_user_tenant_id(self.request),
            )
            .select_related("gateway")
            .order_by("-handled_time")
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="个人工作台 - 我的已办 - MCP Server 权限申请列表",
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
        return (
            WorkbenchPermissionHandler.get_handled_mcp_permission_apply_queryset(
                self.request.user.username,
                get_user_tenant_id(self.request),
            )
            .select_related("mcp_server", "mcp_server__gateway")
            .order_by("-handled_time")
        )
