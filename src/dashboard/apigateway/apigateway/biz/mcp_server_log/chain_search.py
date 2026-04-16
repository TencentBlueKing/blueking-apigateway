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
import logging
from typing import Any, Dict, List

from django.conf import settings

from apigateway.biz.mcp_server_log.es_query import search_all_layers, search_by_upstream_request_id
from apigateway.biz.mcp_server_log.gateway_log import search_gateway_log
from apigateway.biz.mcp_server_log.span_builder import build_spans, merge_mcp_logs
from apigateway.biz.mcp_server_log.utils import calc_max_end_time
from apigateway.service.es.clients import BKLogESClient

logger = logging.getLogger(__name__)


class MCPServerLogChainSearchClient:
    """MCP Server 调用链路搜索客户端

    通过 request_id 或 x_request_id 从 mcp-proxy 的 ES 日志中查询同一请求的所有层级日志，
    并将它们组装成调用链路树结构，用于前端瀑布图展示。

    日志层级：
    - HTTP 层 (APILogger): 整个 HTTP 请求的入口日志，无 mcp_method 字段
    - MCP 协议层 (LoggingMiddleware): MCP 方法调用日志，有 mcp_method 字段
    """

    _es_index: str = settings.MCP_SERVER_ACCESS_LOG_CONFIG["es_index"]
    _es_time_field_name: str = settings.MCP_SERVER_ACCESS_LOG_CONFIG["es_time_field_name"]

    def __init__(self, request_id: str = "", x_request_id: str = "", upstream_request_id: str = ""):
        self._request_id = request_id
        self._x_request_id = x_request_id
        self._upstream_request_id = upstream_request_id
        self._es_client = BKLogESClient(self._es_index)

    def search_chain(self) -> Dict[str, Any]:
        """查询调用链路

        返回结构:
        {
            "request_id": "xxx",
            "x_request_id": "yyy",
            "total_latency_ms": 905.0,
            "spans": [
                {
                    "span_id": "http_entry",
                    "parent_span_id": null,
                    "layer": "http",
                    "service": "mcp-proxy",
                    "operation": "POST /mcp/xxx/sse/message",
                    "latency": "905ms",
                    "latency_ms": 905.0,
                    "start_offset_ms": 0,
                    "status": 200,
                    "detail": { ... },
                    "children": [
                        {
                            "span_id": "mcp_0",
                            "parent_span_id": "http_entry",
                            "layer": "mcp",
                            "service": "mcp-server-name",
                            "operation": "tools/call search_host",
                            ...
                        }
                    ]
                }
            ]
        }
        """
        # 1. 从 mcp-proxy ES 查询同一 request_id 的所有日志(不限 mcp_method exists)
        logs = search_all_layers(
            self._es_client,
            self._es_time_field_name,
            request_id=self._request_id,
        )

        if not logs:
            return {
                "request_id": self._request_id,
                "x_request_id": "",
                "timestamp": None,
                "total_latency_ms": 0,
                "spans": [],
                "upstream_gateway_log": None,
                "downstream_gateway_log": None,
            }

        # 2. 分类：HTTP 层 vs MCP 协议层
        http_logs, mcp_logs = _classify_logs(logs)

        # 3. 合并同一 request_id + mcp_method + tool_name 的多条 MCP 日志
        mcp_logs = merge_mcp_logs(mcp_logs)

        # 4. 组装调用链路
        spans = build_spans(http_logs, mcp_logs)

        # 5. 提取全链路 ID
        x_request_id = _extract_field(logs, "x_request_id")

        # 5.1 计算总耗时：所有 span 的最大结束时间
        total_latency_ms = calc_max_end_time(spans)

        # 5.2 提取产生时间（从 HTTP 层日志或第一条日志）
        timestamp = _extract_timestamp(http_logs, logs)

        # 6. 从 MCP 日志中提取 upstream_request_id（下游网关的 request_id）
        upstream_request_id = _extract_field(mcp_logs, "upstream_request_id")
        logger.debug(
            "extracted upstream_request_id=%s from mcp_logs, self._request_id=%s",
            upstream_request_id,
            self._request_id,
        )

        # 7. 查询上游网关 (bk-apigateway) 的日志
        upstream_gateway_log = (
            search_gateway_log(self._request_id, gateway_type="upstream") if self._request_id else None
        )
        logger.debug(
            "upstream_gateway_log search result: request_id=%s, found=%s",
            self._request_id,
            upstream_gateway_log is not None,
        )

        # 8. 查询下游网关 (biz-gateway) 的日志
        downstream_gateway_log = (
            search_gateway_log(upstream_request_id, gateway_type="downstream") if upstream_request_id else None
        )
        logger.debug(
            "downstream_gateway_log search result: upstream_request_id=%s, found=%s",
            upstream_request_id,
            downstream_gateway_log is not None,
        )

        return {
            "request_id": self._request_id,
            "x_request_id": x_request_id,
            "timestamp": timestamp,
            "total_latency_ms": total_latency_ms,
            "spans": spans,
            "upstream_gateway_log": upstream_gateway_log,
            "downstream_gateway_log": downstream_gateway_log,
        }

    def search_chain_by_x_request_id(self) -> Dict[str, Any]:
        """通过 x_request_id 查询调用链路

        用于 MCPServerLogTraceApi，支持通过全链路 ID 查询所有层级的日志。
        """
        # 1. 从 mcp-proxy ES 查询同一 x_request_id 的所有日志
        logs = search_all_layers(
            self._es_client,
            self._es_time_field_name,
            x_request_id=self._x_request_id,
        )

        if not logs:
            return {
                "request_id": "",
                "x_request_id": self._x_request_id,
                "timestamp": None,
                "total_latency_ms": 0,
                "spans": [],
                "upstream_gateway_log": None,
                "downstream_gateway_log": None,
            }

        # 2. 分类：HTTP 层 vs MCP 协议层
        http_logs, mcp_logs = _classify_logs(logs)

        # 3. 合并同一 request_id + mcp_method + tool_name 的多条 MCP 日志
        mcp_logs = merge_mcp_logs(mcp_logs)

        # 4. 组装调用链路
        spans = build_spans(http_logs, mcp_logs)

        # 5. 提取 request_id（从 HTTP 层或 MCP 层）
        request_id = _extract_field(logs, "request_id")

        # 5.1 计算总耗时：所有 span 的最大结束时间
        total_latency_ms = calc_max_end_time(spans)

        # 5.2 提取产生时间（从 HTTP 层日志或第一条日志）
        timestamp = _extract_timestamp(http_logs, logs)

        # 6. 从 MCP 日志中提取 upstream_request_id（下游网关的 request_id）
        upstream_request_id = _extract_field(mcp_logs, "upstream_request_id")
        logger.debug(
            "[x_request_id] extracted upstream_request_id=%s from mcp_logs, request_id=%s",
            upstream_request_id,
            request_id,
        )

        # 7. 查询上游网关 (bk-apigateway) 的日志
        upstream_gateway_log = search_gateway_log(request_id, gateway_type="upstream") if request_id else None
        logger.debug(
            "[x_request_id] upstream_gateway_log search result: request_id=%s, found=%s",
            request_id,
            upstream_gateway_log is not None,
        )

        # 8. 查询下游网关 (biz-gateway) 的日志
        downstream_gateway_log = (
            search_gateway_log(upstream_request_id, gateway_type="downstream") if upstream_request_id else None
        )
        logger.debug(
            "[x_request_id] downstream_gateway_log search result: upstream_request_id=%s, found=%s",
            upstream_request_id,
            downstream_gateway_log is not None,
        )

        return {
            "request_id": request_id,
            "x_request_id": self._x_request_id,
            "timestamp": timestamp,
            "total_latency_ms": total_latency_ms,
            "spans": spans,
            "upstream_gateway_log": upstream_gateway_log,
            "downstream_gateway_log": downstream_gateway_log,
        }

    def search_chain_by_upstream_request_id(self) -> Dict[str, Any]:
        """通过 upstream_request_id（上游 API 返回的 request_id）查询调用链路

        用于工具箱接口，当用户通过上游 API 返回的 request_id 查询时使用。
        mcp-proxy 的 tools/call 日志中存储了 upstream_request_id 字段，
        直接用该字段在 mcp-proxy ES 中搜索，获取 mcp-proxy 的 request_id 后，
        再用 request_id 查询完整链路（包含 HTTP 入口日志）。
        """
        if not self._upstream_request_id:
            return {
                "request_id": "",
                "x_request_id": "",
                "total_latency_ms": 0,
                "spans": [],
                "upstream_gateway_log": None,
                "downstream_gateway_log": None,
            }

        # 1. 查询下游网关日志（upstream_request_id 对应下游网关的 request_id）
        downstream_gateway_log = search_gateway_log(self._upstream_request_id, gateway_type="downstream")

        # 2. 用 upstream_request_id 字段在 mcp-proxy ES 中搜索，获取 mcp-proxy 的 request_id
        mcp_logs = search_by_upstream_request_id(
            self._es_client,
            self._es_time_field_name,
            self._upstream_request_id,
        )
        if not mcp_logs:
            return {
                "request_id": "",
                "x_request_id": "",
                "total_latency_ms": 0,
                "spans": [],
                "upstream_gateway_log": None,
                "downstream_gateway_log": downstream_gateway_log,
            }

        # 3. 从查到的日志中提取 mcp-proxy 的 request_id
        mcp_request_id = _extract_field(mcp_logs, "request_id")

        if mcp_request_id:
            # 4. 使用 mcp-proxy 的 request_id 查询完整链路
            self._request_id = mcp_request_id
            result = self.search_chain()
            result["downstream_gateway_log"] = downstream_gateway_log
            return result

        # 5. 如果没有 request_id，直接使用查到的日志构建结果
        merged_mcp_logs = merge_mcp_logs([log for log in mcp_logs if log.get("mcp_method")])
        spans = build_spans([], merged_mcp_logs)

        x_request_id = _extract_field(mcp_logs, "x_request_id")

        # 计算总耗时
        total_latency_ms = calc_max_end_time(spans)

        timestamp = None
        if mcp_logs and mcp_logs[0].get("timestamp"):
            timestamp = mcp_logs[0]["timestamp"]

        return {
            "request_id": "",
            "x_request_id": x_request_id,
            "timestamp": timestamp,
            "total_latency_ms": total_latency_ms,
            "spans": spans,
            "upstream_gateway_log": None,
            "downstream_gateway_log": downstream_gateway_log,
        }


def _classify_logs(logs: List[Dict]) -> tuple:
    """分类日志为 HTTP 层和 MCP 协议层"""
    http_logs = []
    mcp_logs = []
    for log in logs:
        if log.get("mcp_method"):
            mcp_logs.append(log)
        else:
            http_logs.append(log)
    return http_logs, mcp_logs


def _extract_field(logs: List[Dict], field_name: str) -> str:
    """从日志列表中提取第一个非空的指定字段值"""
    for log in logs:
        if log.get(field_name):
            return log[field_name]
    return ""


def _extract_timestamp(http_logs: List[Dict], all_logs: List[Dict]):
    """提取产生时间（从 HTTP 层日志或第一条日志）"""
    if http_logs and http_logs[0].get("timestamp"):
        return http_logs[0]["timestamp"]
    if all_logs and all_logs[0].get("timestamp"):
        return all_logs[0]["timestamp"]
    return None
