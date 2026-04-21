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
"""
v2 MCP Server 公共函数模块

注意: 本模块为向后兼容保留，新代码应直接使用 apigateway.biz.mcp_server.MCPServerHandler 中的对应方法。

对应关系:
    - build_mcp_server_list_queryset  -> MCPServerHandler.build_list_queryset
    - build_mcp_server_list_context   -> MCPServerHandler.build_list_context
    - validate_and_enrich_mcp_server_for_retrieve -> MCPServerHandler.build_retrieve_context
"""

from typing import Any, Dict, List, Optional, Sequence, Union

from django.db.models import QuerySet

from apigateway.apps.mcp_server.models import MCPServer
from apigateway.biz.mcp_server import MCPServerHandler


def get_categories_from_context(context: dict, obj: Union[dict, MCPServer]) -> List[Dict[str, str]]:
    """从 serializer context 中获取 obj 对应的 categories 列表

    支持 dict 和 model 实例两种 obj 格式，统一 inner/open 序列化器中的 categories 获取逻辑。

    Args:
        context: serializer 的 context 字典，应包含 "categories" 键
        obj: MCPServer 数据，可以是 dict（含 "id" 键）或 model 实例（含 id 属性）

    Returns:
        categories 列表，如 [{"name": "official", "display_name": "官方"}]
    """
    obj_id = obj.get("id") if isinstance(obj, dict) else obj.id
    return context.get("categories", {}).get(obj_id, [])


def build_mcp_server_list_queryset(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    is_public: Optional[bool] = None,
    order_by: str = "-updated_time",
) -> QuerySet:
    """构建 MCPServer 列表的通用 queryset（不含分页）

    .. deprecated::
        请使用 MCPServerHandler.build_list_queryset()
    """
    return MCPServerHandler.build_list_queryset(
        keyword=keyword,
        category=category,
        is_public=is_public,
        order_by=order_by,
    )


def build_mcp_server_list_context(mcp_servers: Sequence[MCPServer]) -> Dict[str, Any]:
    """构建 MCPServer 列表序列化所需的 gateway/stage 上下文

    .. deprecated::
        请使用 MCPServerHandler.build_list_context()
    """
    return MCPServerHandler.build_list_context(mcp_servers)


def validate_and_enrich_mcp_server_for_retrieve(
    instance: MCPServer,
    check_public: bool = False,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """校验 MCPServer 状态并构建 retrieve 所需的上下文数据

    .. deprecated::
        请使用 MCPServerHandler.build_retrieve_context()
    """
    return MCPServerHandler.build_retrieve_context(
        instance,
        check_public=check_public,
        username=username,
    )
