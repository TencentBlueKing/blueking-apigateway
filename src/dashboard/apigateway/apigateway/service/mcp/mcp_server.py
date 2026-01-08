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

from django.conf import settings

from apigateway.apps.mcp_server.constants import MCPServerProtocolTypeEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.core.models import ResourceVersion


def update_stage_mcp_server_related_resource_names(
    stage_id: int,
    resource_version_id: int,
) -> None:
    """发布后同步 mcp server 中的 resource_names 列表，删除已删除的资源

    Args:
        stage_id (int): stage ID
        resource_version_id (int): 资源版本 ID
    """

    # 1. stage without mcp servers, do nothing
    mcp_servers = MCPServer.objects.filter(stage_id=stage_id).all()
    if not mcp_servers:
        return

    # get the resource names of the resource version
    resource_version = ResourceVersion.objects.filter(id=resource_version_id).first()
    if not resource_version:
        resource_version_resource_names = set()
    else:
        resource_version_resource_names = {resource["name"] for resource in resource_version.data}

    to_update: List[MCPServer] = []
    for mcp_server in mcp_servers:
        # 使用纯资源名称进行比较
        server_resource_names = set(mcp_server.resource_names)
        deleted_resource_names = server_resource_names - resource_version_resource_names

        # 使用 model 方法移除已删除的资源
        if mcp_server.delete_resource_names(deleted_resource_names):
            to_update.append(mcp_server)

    if to_update:
        MCPServer.objects.bulk_update(to_update, fields=["_resource_names"])


def build_mcp_server_url(mcp_server_name: str, protocol_type: str = MCPServerProtocolTypeEnum.SSE.value) -> str:
    """构建 MCP Server 访问 URL

    Args:
        mcp_server_name: MCP Server 名称
        protocol_type: 协议类型，默认为 SSE

    Returns:
        MCP Server 访问 URL
    """
    bk_apigateway_url = settings.BK_API_URL_TMPL.format(api_name="bk-apigateway")
    if protocol_type == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value:
        return f"{bk_apigateway_url}/prod/api/v2/mcp-servers/{mcp_server_name}/mcp/"
    return f"{bk_apigateway_url}/prod/api/v2/mcp-servers/{mcp_server_name}/sse/"


def build_mcp_streamable_http_url(mcp_server_name: str) -> str:
    """构建 MCP Server Streamable HTTP 协议的 URL（便捷方法）"""
    return build_mcp_server_url(mcp_server_name, MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value)


def build_mcp_server_application_url(
    mcp_server_name: str, protocol_type: str = MCPServerProtocolTypeEnum.SSE.value
) -> str:
    """构建应用态 MCP Server 访问 URL

    Args:
        mcp_server_name: MCP Server 名称
        protocol_type: 协议类型，默认为 SSE

    Returns:
        应用态 MCP Server 访问 URL
    """
    bk_apigateway_url = settings.BK_API_URL_TMPL.format(api_name="bk-apigateway")
    if protocol_type == MCPServerProtocolTypeEnum.STREAMABLE_HTTP.value:
        return f"{bk_apigateway_url}/prod/api/v2/mcp-servers/{mcp_server_name}/application/mcp/"
    return f"{bk_apigateway_url}/prod/api/v2/mcp-servers/{mcp_server_name}/application/sse/"


def build_mcp_server_detail_url(mcp_server_id: int) -> str:
    return f"{settings.DASHBOARD_FE_URL}/mcp-market-details/{mcp_server_id}/"


def build_mcp_server_permission_approval_url(gateway_id: int, mcp_server_id: int) -> str:
    """构建 MCP Server 权限审批 URL

    Args:
        gateway_id: 网关 ID
        mcp_server_id: MCP Server ID

    Returns:
        MCP Server 权限审批 URL
    """
    return settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL.format(
        gateway_id=gateway_id, mcp_server_id=mcp_server_id
    )
