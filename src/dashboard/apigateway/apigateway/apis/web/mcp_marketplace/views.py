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
import base64
import json
from urllib.parse import quote

from django.conf import settings
from django.db.models import Count, Q
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.mcp_server.serializers import MCPServerConfigListOutputSLZ
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerCategory
from apigateway.biz.gateway.type import GatewayTypeHandler
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.query import gateway_mcp_server_filter_by_user_tenant_id
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.common.tenant.validators import check_user_can_access_gateway
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Stage
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.mcp.mcp_server import build_mcp_server_url
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
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

        # 分类筛选
        category = slz.validated_data.get("category")
        if category:
            queryset = queryset.filter(categories__name=category, categories__is_active=True).distinct()

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

        gateway_ids = list({mcp_server.gateway.id for mcp_server in page})
        gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids)
        gateways = {
            gateway.id: {
                "id": gateway.id,
                "name": gateway.name,
                "is_official": GatewayTypeHandler.is_official(gateway_auth_configs[gateway.id].gateway_type),
            }
            for gateway in Gateway.objects.filter(id__in=gateway_ids)
        }

        stage_ids = [mcp_server.stage.id for mcp_server in page]
        stages = {
            stage.id: {
                "id": stage.id,
                "name": stage.name,
            }
            for stage in Stage.objects.filter(id__in=stage_ids)
        }

        # 获取 prompts_count
        mcp_server_ids = [mcp_server.id for mcp_server in page]
        prompts_count_map = MCPServerHandler.get_prompts_count_map(mcp_server_ids)

        slz = MCPServerListOutputSLZ(
            page,
            many=True,
            context={
                "gateways": gateways,
                "stages": stages,
                "prompts_count_map": prompts_count_map,
            },
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
        if not instance.is_public:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未公开，无法访问。"))
        if instance.status != MCPServerStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未启用，无法访问。"))
        if instance.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关未启用，无法访问。"))
        if instance.stage.status != StageStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关对应的环境未启用，无法访问。"))

        user_tenant_id = get_user_tenant_id(request)
        check_user_can_access_gateway(instance.gateway.tenant_mode, instance.gateway.tenant_id, user_tenant_id)

        template_name = f"mcp_server/{get_current_language_code()}/guideline.md"
        guideline = render_to_string(
            template_name,
            context={
                "name": instance.name,
                "url": build_mcp_server_url(instance.name, instance.protocol_type),
                "description": instance.description,
                "bk_login_ticket_key": settings.BK_LOGIN_TICKET_KEY,
                "bk_access_token_doc_url": settings.BK_ACCESS_TOKEN_DOC_URL,
                "enable_multi_tenant_mode": settings.ENABLE_MULTI_TENANT_MODE,
                "user_tenant_id": user_tenant_id,
                "protocol_type": instance.protocol_type,
            },
        )
        # set the guideline here, for slz
        instance.guideline = guideline

        gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config([instance.gateway.id])
        gateways = {
            instance.gateway.id: {
                "id": instance.gateway.id,
                "name": instance.gateway.name,
                "is_official": GatewayTypeHandler.is_official(gateway_auth_configs[instance.gateway.id].gateway_type),
            }
        }
        stages = {
            instance.stage.id: {
                "id": instance.stage.id,
                "name": instance.stage.name,
            }
        }

        tool_resources, labels = MCPServerHandler.get_tools_resources_and_labels(
            gateway_id=instance.gateway.id,
            stage_name=instance.stage.name,
            resource_names=instance.resource_names,
        )
        instance.tools = tool_resources

        # append the maintainers
        instance.maintainers = instance.gateway.maintainers

        # 获取 prompts_count 和 prompts 列表
        prompts_count_map = MCPServerHandler.get_prompts_count_map([instance.id])
        prompts = MCPServerHandler.get_prompts(instance.id)

        # 获取用户自定义文档
        user_custom_doc = MCPServerHandler.get_user_custom_doc(instance.id)

        serializer = self.get_serializer(
            instance,
            context={
                "gateways": gateways,
                "stages": stages,
                "labels": labels,
                "tool_name_map": instance.gen_tool_name_map(),
                "prompts_count_map": prompts_count_map,
                "prompts": prompts,
                "user_custom_doc": user_custom_doc,
            },
        )
        # 返回工具列表页面需要的信息
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
        if not instance.is_public:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未公开，无法访问。"))
        if instance.status != MCPServerStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未启用，无法访问。"))
        if instance.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关未启用，无法访问。"))
        if instance.stage.status != StageStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关对应的环境未启用，无法访问。"))

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
        operation_description="获取 MCP 市场中某个 Server 的配置列表（支持 Cursor、CodeBuddy、Claude、AIDev 等工具的配置）",
        responses={status.HTTP_200_OK: MCPServerConfigListOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerConfigListApi(generics.RetrieveAPIView):
    """获取 MCP 市场中某个 Server 的配置列表"""

    queryset = MCPServer.objects.all()
    serializer_class = MCPServerConfigListOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def _build_cursor_install_url(self, instance, mcp_url: str) -> str:
        """
        生成 Cursor 一键配置 URL

        格式: cursor://anysphere.cursor-deeplink/mcp/install?name=<NAME>&config=<BASE64_CONFIG>
        """
        config = {
            "url": mcp_url,
            "headers": {
                "X-Bkapi-Authorization": json.dumps(
                    {
                        "bk_app_code": "your_app_code",
                        "bk_app_secret": "your_app_secret",
                        settings.BK_LOGIN_TICKET_KEY: "your_ticket",
                    }
                )
            },
        }
        config_json = json.dumps(config)
        config_base64 = base64.b64encode(config_json.encode()).decode()
        return (
            f"cursor://anysphere.cursor-deeplink/mcp/install?name={quote(instance.name)}&config={quote(config_base64)}"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # 验证 MCPServer 访问权限
        if not instance.is_public:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未公开，无法访问。"))
        if instance.status != MCPServerStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未启用，无法访问。"))
        if instance.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关未启用，无法访问。"))
        if instance.stage.status != StageStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关对应的环境未启用，无法访问。"))

        user_tenant_id = get_user_tenant_id(request)
        check_user_can_access_gateway(instance.gateway.tenant_mode, instance.gateway.tenant_id, user_tenant_id)

        language_code = get_current_language_code()
        mcp_url = build_mcp_server_url(instance.name, instance.protocol_type)
        configs = []

        for tool in settings.MCP_CONFIG_TOOLS:
            template_name = f"mcp_server/{language_code}/config/{tool['name']}.md"

            context = {
                "name": instance.name,
                "url": mcp_url,
                "description": instance.description,
                "bk_login_ticket_key": settings.BK_LOGIN_TICKET_KEY,
                "protocol_type": instance.protocol_type,
            }

            if tool["name"] == "aidev":
                context["aidev_agent_create_url"] = settings.AIDEV_AGENT_CREATE_URL

            content = render_to_string(template_name, context=context)

            install_url = ""
            if tool["name"] == "cursor":
                install_url = self._build_cursor_install_url(instance, mcp_url)

            configs.append(
                {
                    "name": tool["name"],
                    "display_name": tool["display_name"],
                    "content": content,
                    "install_url": install_url,
                }
            )

        return OKJsonResponse(data={"configs": configs})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCP 市场分类列表",
        responses={status.HTTP_200_OK: MCPServerCategoryOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceCategoryListApi(generics.ListAPIView):
    """MCP 市场分类列表 API"""

    serializer_class = MCPServerCategoryOutputSLZ

    def list(self, request, *args, **kwargs):
        # 获取用户租户 ID，用于过滤
        user_tenant_id = get_user_tenant_id(request)

        # 构建 MCPServer 过滤条件
        mcp_server_filter = Q(
            mcp_servers__is_public=True,
            mcp_servers__status=MCPServerStatusEnum.ACTIVE.value,
            mcp_servers__gateway__status=GatewayStatusEnum.ACTIVE.value,
            mcp_servers__stage__status=StageStatusEnum.ACTIVE.value,
        )

        # 如果有租户过滤，添加租户条件
        if user_tenant_id:
            mcp_server_filter &= Q(mcp_servers__gateway__tenant_id=user_tenant_id) | Q(
                mcp_servers__gateway__tenant_mode="global"
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
