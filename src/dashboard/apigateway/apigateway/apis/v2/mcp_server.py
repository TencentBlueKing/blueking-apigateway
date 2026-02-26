#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import logging
from typing import Any, Dict, Optional, Sequence

from django.conf import settings
from django.db.models import Q, QuerySet
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.biz.gateway.type import GatewayTypeHandler
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Stage
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.mcp.mcp_server import build_mcp_server_url

logger = logging.getLogger(__name__)


def build_mcp_server_list_queryset(
    *,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    order_by: str = "-updated_time",
) -> QuerySet:
    """构建 MCPServer 列表的通用 queryset（不含分页）"""
    queryset = MCPServer.objects.filter(status=MCPServerStatusEnum.ACTIVE.value)
    queryset = queryset.filter(gateway__status=GatewayStatusEnum.ACTIVE.value)
    queryset = queryset.filter(stage__status=StageStatusEnum.ACTIVE.value)

    if is_public is not None:
        queryset = queryset.filter(is_public=is_public)

    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(title__icontains=keyword) | Q(description__icontains=keyword)
        )

    if category:
        queryset = queryset.filter(categories__name=category, categories__is_active=True)

    return queryset.select_related("gateway", "stage").order_by(order_by)


def build_mcp_server_list_context(mcp_servers: Sequence[MCPServer]) -> Dict[str, Any]:
    """构建 MCPServer 列表序列化所需的 gateway/stage 上下文"""
    gateway_ids = list({ms.gateway.id for ms in mcp_servers})
    gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids)
    gateways = {
        gw.id: {
            "id": gw.id,
            "name": gw.name,
            "maintainers": gw.maintainers,
            "is_official": GatewayTypeHandler.is_official(gateway_auth_configs[gw.id].gateway_type),
        }
        for gw in Gateway.objects.filter(id__in=gateway_ids)
    }

    stage_ids = [ms.stage.id for ms in mcp_servers]
    stages = {
        s.id: {
            "id": s.id,
            "name": s.name,
        }
        for s in Stage.objects.filter(id__in=stage_ids)
    }

    return {"gateways": gateways, "stages": stages}


def validate_and_enrich_mcp_server_for_retrieve(
    instance: MCPServer,
    *,
    check_public: bool = False,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """校验 MCPServer 状态并构建 retrieve 所需的上下文数据

    Args:
        instance: MCPServer 实例
        check_public: 是否检查公开性（open 接口需要，inner 接口不需要）
        username: 当前用户名，用于公开性检查
    Returns:
        序列化所需的 context 字典
    """
    if instance.status != MCPServerStatusEnum.ACTIVE.value:
        raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未启用，无法访问。"))
    if instance.gateway.status != GatewayStatusEnum.ACTIVE.value:
        raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关未启用，无法访问。"))
    if instance.stage.status != StageStatusEnum.ACTIVE.value:
        raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关对应的环境未启用，无法访问。"))

    if check_public and not instance.is_public and (not username or username not in instance.gateway.maintainers):
        raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未公开，无法访问。"))

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
            "user_tenant_id": "",
            "protocol_type": instance.protocol_type,
        },
    )
    instance.guideline = guideline

    tool_resources, labels = MCPServerHandler.get_tools_resources_and_labels(
        gateway_id=instance.gateway.id,
        stage_name=instance.stage.name,
        resource_names=instance.resource_names,
    )
    instance.tools = tool_resources
    instance.maintainers = instance.gateway.maintainers

    prompts_count_map = MCPServerHandler.get_prompts_count_map([instance.id])
    prompts = MCPServerHandler.get_prompts(instance.id)
    user_custom_doc = MCPServerHandler.get_user_custom_doc(instance.id)

    return {
        "labels": labels,
        "prompts_count_map": prompts_count_map,
        "prompts": prompts,
        "user_custom_doc": user_custom_doc,
    }
