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
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.mcp_server.serializers import MCPServerConfigListOutputSLZ
from apigateway.apps.mcp_server.constants import (
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerCategory
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.constants import TENANT_ID_OPERATION, TenantModeEnum
from apigateway.common.tenant.query import gateway_mcp_server_filter_by_user_tenant_id
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.common.tenant.validators import check_user_can_access_gateway
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    MCPServerBatchConfigInputSLZ,
    MCPServerBatchConfigOutputSLZ,
    MCPServerCategoryOutputSLZ,
    MCPServerListInputSLZ,
    MCPServerListOutputSLZ,
    MCPServerRetrieveOutputSLZ,
    MCPServerToolDocOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关的 MCPServer 列表",
        query_serializer=MCPServerListInputSLZ,
        responses={status.HTTP_200_OK: MCPServerListOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = MCPServerListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        # mcp server should be public and active
        queryset = MCPServer.objects.filter(is_public=True, status=MCPServerStatusEnum.ACTIVE.value)
        # gateway should be active
        queryset = queryset.filter(gateway__status=GatewayStatusEnum.ACTIVE.value)
        # the stage should be active and online
        queryset = queryset.filter(stage__status=StageStatusEnum.ACTIVE.value)

        keyword = slz.validated_data.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(_labels__icontains=keyword)
            )

        # 分类筛选 —— 使用 biz 层的通用方法
        categories = slz.validated_data.get("categories")
        if categories:
            queryset = MCPServerHandler.apply_category_filter(queryset, categories)

        # tenant_id filter here
        user_tenant_id = get_user_tenant_id(request)
        if user_tenant_id:
            queryset = gateway_mcp_server_filter_by_user_tenant_id(queryset, user_tenant_id)

        # optimize query by using select_related and prefetch_related
        queryset = queryset.select_related("gateway", "stage").prefetch_related("categories")

        # 排序
        order_by = slz.validated_data.get("order_by", "-updated_time")
        queryset = queryset.order_by(order_by)

        # note: the stage offline will update related mcp server status to inactive,
        # the stage publish will update the mcp server resource_names,
        # so we don't need to care about is the mcp server stage is correctly published here

        page = self.paginate_queryset(queryset)

        # 使用 biz 层的通用方法构建上下文
        context = MCPServerHandler.build_list_context(
            page,
            include_prompts_count=True,
            include_least_privileges=True,
        )

        slz = MCPServerListOutputSLZ(
            page,
            many=True,
            context=context,
        )

        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCP 市场中某个 Server 的详情",
        responses={status.HTTP_200_OK: MCPServerRetrieveOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerRetrieveApi(generics.RetrieveAPIView):
    queryset = MCPServer.objects.select_related("gateway", "stage").prefetch_related("categories")
    serializer_class = MCPServerRetrieveOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        user_tenant_id = get_user_tenant_id(request)
        check_user_can_access_gateway(instance.gateway.tenant_mode, instance.gateway.tenant_id, user_tenant_id)

        # 使用 biz 层的通用方法完成访问校验和上下文构建
        context = MCPServerHandler.build_retrieve_context(
            instance,
            check_public=True,
            user_tenant_id=user_tenant_id,
        )

        serializer = self.get_serializer(instance, context=context)
        return OKJsonResponse(data=serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCP 市场中某个 Server 的某个工具的文档",
        responses={status.HTTP_200_OK: MCPServerToolDocOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerToolDocRetrieveApi(generics.RetrieveAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerToolDocOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # 使用 biz 层的通用方法校验访问权限
        MCPServerHandler.validate_access(instance, check_public=True)

        user_tenant_id = get_user_tenant_id(request)
        check_user_can_access_gateway(instance.gateway.tenant_mode, instance.gateway.tenant_id, user_tenant_id)

        resource_name = kwargs.get("tool_name")

        doc = MCPServerHandler.get_tool_doc(
            gateway_id=instance.gateway.id,
            stage_name=instance.stage.name,
            tool_name=resource_name,
        )

        slz = MCPServerToolDocOutputSLZ(doc)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCP 市场中某个 Server 的配置列表（支持 Cursor、CodeBuddy、Claude、VSCode 等工具的配置）",
        responses={status.HTTP_200_OK: MCPServerConfigListOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerConfigListApi(generics.RetrieveAPIView):
    """获取 MCP 市场中某个 Server 的配置列表"""

    queryset = MCPServer.objects.all()
    serializer_class = MCPServerConfigListOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # 使用 biz 层的通用方法校验访问权限
        MCPServerHandler.validate_access(instance, check_public=True)

        user_tenant_id = get_user_tenant_id(request)
        check_user_can_access_gateway(instance.gateway.tenant_mode, instance.gateway.tenant_id, user_tenant_id)

        least_privileges = MCPServerHandler.get_least_privileges([instance])
        least_privilege = least_privileges.get((instance.gateway.id, instance.stage.id), "")

        configs = MCPServerHandler.build_agent_client_configs(instance, least_privilege, user_tenant_id=user_tenant_id)
        return OKJsonResponse(data={"configs": configs})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCP 市场分类列表",
        query_serializer=MCPServerListInputSLZ,
        responses={status.HTTP_200_OK: MCPServerCategoryOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceCategoryListApi(generics.ListAPIView):
    """MCP 市场分类列表 API"""

    serializer_class = MCPServerCategoryOutputSLZ

    def list(self, request, *args, **kwargs):
        slz = MCPServerListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        # 获取用户租户 ID，用于过滤
        user_tenant_id = get_user_tenant_id(request)

        # 构建分类统计过滤条件（和 MCPMarketplaceServerListApi 保持一致）
        mcp_server_filter = Q(
            mcp_servers__is_public=True,
            mcp_servers__status=MCPServerStatusEnum.ACTIVE.value,
            mcp_servers__gateway__status=GatewayStatusEnum.ACTIVE.value,
            mcp_servers__stage__status=StageStatusEnum.ACTIVE.value,
        )

        # 关键字筛选
        keyword = slz.validated_data.get("keyword")
        if keyword:
            mcp_server_filter &= (
                Q(mcp_servers__name__icontains=keyword)
                | Q(mcp_servers__title__icontains=keyword)
                | Q(mcp_servers__description__icontains=keyword)
                | Q(mcp_servers___labels__icontains=keyword)
            )

        # 分类筛选（支持多个分类，与 MCPMarketplaceServerListApi 逻辑一致）
        categories = slz.validated_data.get("categories")
        if categories:
            special_categories = {OFFICIAL_MCP_CATEGORY_NAME, FEATURED_MCP_CATEGORY_NAME}
            if special_categories & set(categories):
                # 包含 Official 或 Featured 分类时，使用 AND 逻辑：必须同时属于所有选择的分类
                for category in categories:
                    mcp_server_filter &= Q(
                        mcp_servers__categories__name=category, mcp_servers__categories__is_active=True
                    )
            else:
                # 不包含特殊分类时，使用 OR 逻辑：属于任意一个选择的分类即可
                mcp_server_filter &= Q(
                    mcp_servers__categories__name__in=categories, mcp_servers__categories__is_active=True
                )
        # 如果有租户过滤，使用和 MCPMarketplaceServerListApi 一样的筛选逻辑
        if user_tenant_id:
            # 运营租户可以看到 全租户网关 + 自己租户网关的 MCP Server
            if user_tenant_id == TENANT_ID_OPERATION:
                mcp_server_filter &= Q(mcp_servers__gateway__tenant_mode=TenantModeEnum.GLOBAL.value) | Q(
                    mcp_servers__gateway__tenant_mode=TenantModeEnum.SINGLE.value,
                    mcp_servers__gateway__tenant_id=user_tenant_id,
                )
            else:
                # 其他租户只能看到本租户网关的 MCP Server
                mcp_server_filter &= Q(
                    mcp_servers__gateway__tenant_mode=TenantModeEnum.SINGLE.value,
                    mcp_servers__gateway__tenant_id=user_tenant_id,
                )

        # 使用 annotate 一次性统计每个分类的 MCPServer 数量，避免 N+1 查询
        queryset = (
            MCPServerCategory.objects.filter(is_active=True)
            .annotate(mcp_server_count=Count("mcp_servers", filter=mcp_server_filter, distinct=True))
            .order_by("sort_order", "id")
        )

        # 构建统计数据字典
        category_stats = {cat.id: cat.mcp_server_count for cat in queryset}

        serializer = self.get_serializer(queryset, many=True, context={"category_stats": category_stats})
        return OKJsonResponse(data=serializer.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="批量获取 MCP 市场 MCPServer 配置（支持指定客户端类型：cursor, codebuddy, claude, vscode 等）",
        request_body=MCPServerBatchConfigInputSLZ,
        responses={status.HTTP_200_OK: MCPServerBatchConfigOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceBatchConfigApi(generics.CreateAPIView):
    """批量获取 MCP 市场 MCPServer 配置，支持指定客户端类型"""

    def create(self, request, *args, **kwargs):
        slz = MCPServerBatchConfigInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        mcp_server_ids = slz.validated_data["mcp_server_ids"]
        client_type = slz.validated_data["client_type"]

        # 查询 MCPServer 列表（只查询公开的）
        queryset = MCPServer.objects.filter(
            id__in=mcp_server_ids,
            is_public=True,
            status=MCPServerStatusEnum.ACTIVE.value,
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
        ).select_related("gateway", "stage")

        # 租户过滤
        user_tenant_id = get_user_tenant_id(request)
        if user_tenant_id:
            queryset = gateway_mcp_server_filter_by_user_tenant_id(queryset, user_tenant_id)

        instances = list(queryset)

        if not instances:
            raise error_codes.NOT_FOUND.format(_("未找到有效的 MCPServer"), replace=True)

        # 校验访问权限
        for instance in instances:
            check_user_can_access_gateway(instance.gateway.tenant_mode, instance.gateway.tenant_id, user_tenant_id)

        # 获取最低权限信息（按 mcp_server.id 为 key）
        least_privileges = MCPServerHandler.get_least_privileges_by_server(instances)

        # 构建批量配置
        config = MCPServerHandler.build_batch_agent_client_config(
            instances, client_type, least_privileges, user_tenant_id=user_tenant_id
        )

        # 查找客户端显示名称
        display_name = MCPServerHandler.get_client_display_name(client_type)

        result = {
            "client_type": client_type,
            "display_name": display_name,
            "config": config,
        }

        output_slz = MCPServerBatchConfigOutputSLZ(result)
        return OKJsonResponse(data=output_slz.data)
