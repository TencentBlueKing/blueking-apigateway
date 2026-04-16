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
from typing import Dict, List

from apigateway.biz.mcp_server_log.chain_helpers import (
    build_chain_summary,
    build_latency_distribution,
    enrich_chain_data,
    flatten_spans_to_logs,
)
from apigateway.biz.mcp_server_log.chain_search import MCPServerLogChainSearchClient
from apigateway.biz.mcp_server_log.constants import MCP_SERVER_LOG_FIELDS


def search_chain_by_any_id(request_id: str = "") -> Dict:
    """通过 request_id 查询调用链路，自动尝试多种 ID 类型

    按优先级依次尝试：
    1. request_id 查询
    2. x_request_id 查询
    3. upstream_request_id 查询

    Args:
        request_id: 用户传入的请求 ID，可能是任意类型
    """
    client = MCPServerLogChainSearchClient(request_id=request_id)
    chain_data = client.search_chain()

    if not chain_data.get("spans"):
        client = MCPServerLogChainSearchClient(x_request_id=request_id)
        chain_data = client.search_chain_by_x_request_id()

    if not chain_data.get("spans"):
        client = MCPServerLogChainSearchClient(upstream_request_id=request_id)
        chain_data = client.search_chain_by_upstream_request_id()

    return chain_data


def search_chain_logs_by_any_id(request_id: str = "") -> Dict:
    """通过 request_id 查询调用链路并扁平化为日志列表

    适用于日志详情查询场景（MCPServerLogDetailApi / MCPServerLogQueryApi），
    自动尝试多种 ID 类型查询。

    Args:
        request_id: 用户传入的请求 ID
    """
    chain_data = search_chain_by_any_id(request_id)
    logs = flatten_spans_to_logs(chain_data)
    return _build_paginated_log_result(logs, chain_data)


def search_chain_logs_with_gateway_by_any_id(request_id: str = "") -> Dict:
    """通过 request_id 查询调用链路并扁平化为日志列表，同时附加网关日志

    适用于链路追踪场景（MCPServerLogTraceApi / MCPServerLogQueryApi），
    自动尝试多种 ID 类型查询，并添加上下游网关日志。

    Args:
        request_id: 用户传入的请求 ID
    """
    chain_data = search_chain_by_any_id(request_id)
    logs = flatten_spans_to_logs(chain_data)

    # 添加网关日志到列表开头
    if chain_data.get("upstream_gateway_log"):
        upstream_log = chain_data["upstream_gateway_log"]
        upstream_log["layer"] = "gateway_upstream"
        logs.insert(0, upstream_log)

    if chain_data.get("downstream_gateway_log"):
        downstream_log = chain_data["downstream_gateway_log"]
        downstream_log["layer"] = "gateway_downstream"
        logs.insert(0, downstream_log)

    return _build_paginated_log_result(logs, chain_data)


def search_chain_with_summary_by_any_id(request_id: str = "") -> Dict:
    """通过 request_id 查询调用链路并添加汇总统计信息

    适用于瀑布图场景（MCPServerLogChainApi / MCPServerLogQueryChainApi）。

    Args:
        request_id: 用户传入的请求 ID
    """
    chain_data = search_chain_by_any_id(request_id)
    return enrich_chain_data(chain_data)


def search_chain_summary_by_any_id(request_id: str = "") -> Dict:
    """通过 request_id 查询调用链路并构建汇总信息

    适用于工具箱汇总查询场景（MCPServerLogQuerySummaryApi）。

    Args:
        request_id: 用户传入的请求 ID
    """
    chain_data = search_chain_by_any_id(request_id)
    summary = build_chain_summary(chain_data)
    summary["latency_distribution"] = build_latency_distribution(chain_data)
    return summary


def _build_paginated_log_result(logs: List[Dict], chain_data: Dict) -> Dict:
    """构建分页日志结果"""
    total_count = len(logs)
    return {
        "count": total_count,
        "has_next": False,
        "has_previous": False,
        "results": logs,
        "fields": MCP_SERVER_LOG_FIELDS,
    }
