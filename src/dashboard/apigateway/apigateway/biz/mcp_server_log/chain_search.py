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
import re
from typing import Any, Dict, List, Optional

from django.conf import settings
from elasticsearch_dsl import Search

from apigateway.biz.access_log.log_search import LogSearchClient
from apigateway.service.es.clients import BKLogESClient
from apigateway.utils import time as time_utils

logger = logging.getLogger(__name__)

# latency 字符串(如 "37.36ms", "1.2s", "500µs") 转换为毫秒
_LATENCY_PATTERN = re.compile(r"^([\d.]+)(µs|us|ms|s|m|h)$")

_UNIT_TO_MS = {
    "µs": 0.001,
    "us": 0.001,
    "ms": 1.0,
    "s": 1000.0,
    "m": 60_000.0,
    "h": 3_600_000.0,
}


def _parse_latency_ms(latency_str: str) -> Optional[float]:
    """将 Go 的 duration 字符串转换为毫秒数值"""
    if not latency_str:
        return None
    m = _LATENCY_PATTERN.match(latency_str.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2)
    return round(value * _UNIT_TO_MS.get(unit, 1.0), 3)


# MCP Proxy 的 ES 日志中，所有层共有的字段
_CHAIN_OUTPUT_FIELDS = [
    # 链路标识
    "request_id",
    "x_request_id",
    "session_id",
    # 网关信息
    "gateway_id",
    "gateway_name",
    "mcp_server_name",
    "mcp_server_id",
    # HTTP 层字段
    "method",
    "path",
    "status",
    # MCP 协议层字段
    "mcp_method",
    "tool_name",
    "params",
    "response",
    "request_body_size",
    "response_body_size",
    # 调用方信息
    "app_code",
    "bk_username",
    "client_ip",
    "client_id",
    # 性能
    "latency",
    # trace
    "trace_id",
    # 错误
    "error",
]


class MCPServerLogChainSearchClient:
    """MCP Server 调用链路搜索客户端

    通过 request_id 从 mcp-proxy 的 ES 日志中查询同一请求的所有层级日志，
    并将它们组装成调用链路树结构，用于前端瀑布图展示。

    日志层级：
    - HTTP 层 (APILogger): 整个 HTTP 请求的入口日志，无 mcp_method 字段
    - MCP 协议层 (LoggingMiddleware): MCP 方法调用日志，有 mcp_method 字段
    """

    _es_index: str = settings.MCP_SERVER_ACCESS_LOG_CONFIG["es_index"]
    _es_time_field_name: str = settings.MCP_SERVER_ACCESS_LOG_CONFIG["es_time_field_name"]

    def __init__(self, request_id: str):
        self._request_id = request_id
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
        logs = self._search_all_layers()

        if not logs:
            return {
                "request_id": self._request_id,
                "x_request_id": "",
                "total_latency_ms": 0,
                "spans": [],
                "gateway_log": None,
            }

        # 2. 分类：HTTP 层 vs MCP 协议层
        http_logs = []
        mcp_logs = []
        for log in logs:
            if log.get("mcp_method"):
                mcp_logs.append(log)
            else:
                http_logs.append(log)

        # 3. 组装调用链路
        spans = self._build_spans(http_logs, mcp_logs)

        # 4. 提取全链路 ID
        x_request_id = ""
        for log in logs:
            if log.get("x_request_id"):
                x_request_id = log["x_request_id"]
                break

        # 5. 计算总耗时
        total_latency_ms = 0
        if spans:
            total_latency_ms = spans[0].get("latency_ms", 0) or 0

        # 6. 查询上游网关 (bk-apigateway) 的日志
        gateway_log = self._search_gateway_log(x_request_id) if x_request_id else None

        return {
            "request_id": self._request_id,
            "x_request_id": x_request_id,
            "total_latency_ms": total_latency_ms,
            "spans": spans,
            "gateway_log": gateway_log,
        }

    def _search_all_layers(self) -> List[Dict]:
        """从 ES 中查询同一 request_id 的所有层级日志"""
        s = Search()
        s = s.filter("term", request_id=self._request_id)
        s = s.source(fields=_CHAIN_OUTPUT_FIELDS)
        s = s.sort({self._es_time_field_name: {"order": "asc"}})
        s = s[:100]  # 限制最多 100 条

        try:
            data = self._es_client.execute_search(s.to_dict())
        except Exception:
            logger.exception("failed to search mcp server chain logs for request_id=%s", self._request_id)
            return []

        hits = data.get("hits", {}).get("hits", [])
        result = []
        for hit in hits:
            log = hit["_source"]
            if hit.get("sort"):
                log["timestamp"] = time_utils.convert_epoch_millisecond_to_second(hit["sort"][0])
                log["timestamp_ms"] = hit["sort"][0]
            result.append(log)
        return result

    def _build_spans(self, http_logs: List[Dict], mcp_logs: List[Dict]) -> List[Dict]:
        """将日志构建为 span 树结构"""
        spans = []

        # HTTP 入口 span (如果存在)
        http_entry = None
        if http_logs:
            log = http_logs[0]
            latency_ms = _parse_latency_ms(log.get("latency", ""))
            http_entry = {
                "span_id": "http_entry",
                "parent_span_id": None,
                "layer": "http",
                "service": "mcp-proxy",
                "operation": f"{log.get('method', '')} {log.get('path', '')}",
                "latency": log.get("latency", ""),
                "latency_ms": latency_ms,
                "start_offset_ms": 0,
                "status": log.get("status"),
                "detail": {
                    "method": log.get("method"),
                    "path": log.get("path"),
                    "status": log.get("status"),
                    "client_ip": log.get("client_ip"),
                    "app_code": log.get("app_code"),
                    "gateway_name": log.get("gateway_name"),
                    "mcp_server_name": log.get("mcp_server_name"),
                    "request_id": log.get("request_id"),
                    "x_request_id": log.get("x_request_id"),
                },
                "children": [],
            }
            spans.append(http_entry)

        # MCP 协议层 span
        # 计算 base timestamp 用于 start_offset_ms
        base_ts_ms = None
        if http_entry and http_logs and http_logs[0].get("timestamp_ms"):
            # HTTP 入口的 timestamp 是请求完成后记录的，所以 MCP span 的偏移需要用 HTTP 开始时间
            # 近似用 HTTP 完成时间 - HTTP 耗时
            http_latency_ms = http_entry.get("latency_ms") or 0
            base_ts_ms = http_logs[0]["timestamp_ms"] - http_latency_ms
        elif mcp_logs and mcp_logs[0].get("timestamp_ms"):
            base_ts_ms = mcp_logs[0]["timestamp_ms"]

        for i, log in enumerate(mcp_logs):
            latency_ms = _parse_latency_ms(log.get("latency", ""))
            mcp_method = log.get("mcp_method", "")
            tool_name = log.get("tool_name", "")

            operation = mcp_method
            if tool_name:
                operation = f"{mcp_method} {tool_name}"

            # 计算 start_offset_ms: MCP 日志的 timestamp 是完成时间，
            # 所以 start = 完成时间 - 耗时 - base_ts
            start_offset_ms = 0
            if base_ts_ms is not None and log.get("timestamp_ms"):
                log_start_ms = log["timestamp_ms"] - (latency_ms or 0)
                start_offset_ms = max(0, round(log_start_ms - base_ts_ms, 3))

            span = {
                "span_id": f"mcp_{i}",
                "parent_span_id": "http_entry" if http_entry else None,
                "layer": "mcp",
                "service": log.get("mcp_server_name", ""),
                "operation": operation,
                "latency": log.get("latency", ""),
                "latency_ms": latency_ms,
                "start_offset_ms": start_offset_ms,
                "status": None,
                "detail": {
                    "mcp_method": mcp_method,
                    "tool_name": tool_name,
                    "params": log.get("params"),
                    "response": log.get("response"),
                    "request_body_size": log.get("request_body_size"),
                    "response_body_size": log.get("response_body_size"),
                    "app_code": log.get("app_code"),
                    "bk_username": log.get("bk_username"),
                    "client_ip": log.get("client_ip"),
                    "client_id": log.get("client_id"),
                    "session_id": log.get("session_id"),
                    "request_id": log.get("request_id"),
                    "x_request_id": log.get("x_request_id"),
                    "trace_id": log.get("trace_id"),
                    "error": log.get("error"),
                },
                "children": [],
            }

            if http_entry:
                http_entry["children"].append(span)
            else:
                spans.append(span)

        return spans

    def _search_gateway_log(self, x_request_id: str) -> Optional[Dict]:
        """通过 x_request_id (即 bk-apigateway 的 request_id) 查询上游网关日志

        bk-apigateway 的 access_log ES 中，request_id 字段对应的是 X-Bkapi-Request-ID，
        而这个值就是 mcp-proxy 日志中的 request_id 字段。
        """
        if not x_request_id:
            return None

        try:
            # 使用已有的 access_log LogSearchClient 查询
            # x_request_id 对应 bk-apigateway 的 request_id
            client = LogSearchClient(request_id=x_request_id)
            total_count, logs = client.search_logs(offset=0, limit=1)
            if logs:
                log = logs[0]
                return {
                    "layer": "gateway",
                    "service": "bk-apigateway",
                    "request_id": log.get("request_id"),
                    "method": log.get("method"),
                    "http_host": log.get("http_host"),
                    "http_path": log.get("http_path"),
                    "status": log.get("status"),
                    "request_duration": log.get("request_duration"),
                    "backend_duration": log.get("backend_duration"),
                    "stage": log.get("stage"),
                    "resource_name": log.get("resource_name"),
                    "backend_host": log.get("backend_host"),
                    "backend_path": log.get("backend_path"),
                    "backend_method": log.get("backend_method"),
                    "backend_scheme": log.get("backend_scheme"),
                    "app_code": log.get("app_code"),
                    "client_ip": log.get("client_ip"),
                    "error": log.get("error"),
                    "code_name": log.get("code_name"),
                }
        except Exception:
            logger.exception("failed to search gateway log for x_request_id=%s", x_request_id)

        return None
