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
from apigateway.common.error_codes import error_codes
from apigateway.service.es.clients import BKLogESClient
from apigateway.utils import time as time_utils
from apigateway.utils.time import SmartTimeRange

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
    # HTTP 层字段（注意：ES 中 method/path/status 在 __ext_json 中）
    "method",
    "path",
    "status",
    # Filebeat 提取的字段
    "__ext_json",
    # MCP 协议层字段
    "mcp_method",
    "tool_name",
    "prompt_name",  # prompt 名称
    "tool",  # audit 日志中的原始 tool 配置字符串
    "params",
    "request",  # audit 日志使用 request 字段存储请求参数
    "response",
    "request_body_size",
    "response_body_size",
    "upstream_request_id",  # 上游 API 返回的 request_id
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

        # 3. 合并同一 request_id + mcp_method + tool_name 的多条 MCP 日志
        # "call tool" (无 latency) 和 "call tool complete" (有 latency) 需要合并
        mcp_logs = self._merge_mcp_logs(mcp_logs)

        # 4. 组装调用链路
        spans = self._build_spans(http_logs, mcp_logs)

        # 5. 提取全链路 ID
        x_request_id = ""
        for log in logs:
            if log.get("x_request_id"):
                x_request_id = log["x_request_id"]
                break

        # 5.1 计算总耗时：所有 span 的最大结束时间
        # 结束时间 = start_offset_ms + latency_ms
        def calc_max_end_time(span_list, max_end=0):
            for span in span_list:
                start = span.get("start_offset_ms", 0) or 0
                latency = span.get("latency_ms", 0) or 0
                end_time = start + latency
                max_end = max(max_end, end_time)
                # 递归计算子 span
                max_end = calc_max_end_time(span.get("children", []), max_end)
            return max_end

        total_latency_ms = calc_max_end_time(spans)

        # 5.2 提取产生时间（从 HTTP 层日志或第一条日志）
        timestamp = None
        if http_logs and http_logs[0].get("timestamp"):
            timestamp = http_logs[0]["timestamp"]
        elif logs and logs[0].get("timestamp"):
            timestamp = logs[0]["timestamp"]

        # 6. 从 MCP 日志中提取 upstream_request_id（下游网关的 request_id）
        upstream_request_id = ""
        for log in mcp_logs:
            if log.get("upstream_request_id"):
                upstream_request_id = log["upstream_request_id"]
                break
        logger.info(
            "extracted upstream_request_id=%s from mcp_logs, self._request_id=%s",
            upstream_request_id,
            self._request_id,
        )

        # 7. 查询上游网关 (bk-apigateway) 的日志
        # 使用 request_id 查询，因为 bk-apigateway 的 request_id 对应 mcp-proxy 的 request_id
        upstream_gateway_log = (
            self._search_gateway_log(self._request_id, gateway_type="upstream") if self._request_id else None
        )
        logger.info(
            "upstream_gateway_log search result: request_id=%s, found=%s",
            self._request_id,
            upstream_gateway_log is not None,
        )

        # 8. 查询下游网关 (biz-gateway) 的日志
        # 使用 upstream_request_id 查询，这是 API 响应中返回的 request_id
        # 注意：如果 biz-gateway 的日志不在 bk-apigateway 的 ES 索引中，将无法查询到
        downstream_gateway_log = (
            self._search_gateway_log(upstream_request_id, gateway_type="downstream") if upstream_request_id else None
        )
        logger.info(
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
        logs = self._search_all_layers()

        if not logs:
            return {
                "request_id": "",
                "x_request_id": self._x_request_id,
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

        # 3. 合并同一 request_id + mcp_method + tool_name 的多条 MCP 日志
        mcp_logs = self._merge_mcp_logs(mcp_logs)

        # 4. 组装调用链路
        spans = self._build_spans(http_logs, mcp_logs)

        # 5. 提取 request_id（从 HTTP 层或 MCP 层）
        request_id = ""
        for log in logs:
            if log.get("request_id"):
                request_id = log["request_id"]
                break

        # 5.1 计算总耗时：所有 span 的最大结束时间
        def calc_max_end_time_x(span_list, max_end=0):
            for span in span_list:
                start = span.get("start_offset_ms", 0) or 0
                latency = span.get("latency_ms", 0) or 0
                end_time = start + latency
                max_end = max(max_end, end_time)
                max_end = calc_max_end_time_x(span.get("children", []), max_end)
            return max_end

        total_latency_ms = calc_max_end_time_x(spans)

        # 5.2 提取产生时间（从 HTTP 层日志或第一条日志）
        timestamp = None
        if http_logs and http_logs[0].get("timestamp"):
            timestamp = http_logs[0]["timestamp"]
        elif logs and logs[0].get("timestamp"):
            timestamp = logs[0]["timestamp"]

        # 6. 从 MCP 日志中提取 upstream_request_id（下游网关的 request_id）
        upstream_request_id = ""
        for log in mcp_logs:
            if log.get("upstream_request_id"):
                upstream_request_id = log["upstream_request_id"]
                break
        logger.info(
            "[x_request_id] extracted upstream_request_id=%s from mcp_logs, request_id=%s",
            upstream_request_id,
            request_id,
        )

        # 7. 查询上游网关 (bk-apigateway) 的日志
        # 使用 request_id 查询，因为 bk-apigateway 的 request_id 对应 mcp-proxy 的 request_id
        upstream_gateway_log = self._search_gateway_log(request_id, gateway_type="upstream") if request_id else None
        logger.info(
            "[x_request_id] upstream_gateway_log search result: request_id=%s, found=%s",
            request_id,
            upstream_gateway_log is not None,
        )

        # 8. 查询下游网关 (biz-gateway) 的日志
        # 使用 upstream_request_id 查询，这是 API 响应中返回的 request_id
        # 注意：如果 biz-gateway 的日志不在 bk-apigateway 的 ES 索引中，将无法查询到
        downstream_gateway_log = (
            self._search_gateway_log(upstream_request_id, gateway_type="downstream") if upstream_request_id else None
        )
        logger.info(
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
        downstream_gateway_log = self._search_gateway_log(self._upstream_request_id, gateway_type="downstream")

        # 2. 用 upstream_request_id 字段在 mcp-proxy ES 中搜索，获取 mcp-proxy 的 request_id
        mcp_logs = self._search_by_upstream_request_id()
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
        # upstream_request_id 查到的日志都是 MCP 协议层日志（有 upstream_request_id 字段），
        # 需要用 mcp-proxy 的 request_id 查完整链路（包含 HTTP 入口日志）
        mcp_request_id = ""
        for log in mcp_logs:
            if log.get("request_id"):
                mcp_request_id = log["request_id"]
                break

        if mcp_request_id:
            # 4. 使用 mcp-proxy 的 request_id 查询完整链路
            self._request_id = mcp_request_id
            result = self.search_chain()
            result["downstream_gateway_log"] = downstream_gateway_log
            return result

        # 5. 如果没有 request_id，直接使用查到的日志构建结果
        merged_mcp_logs = self._merge_mcp_logs([log for log in mcp_logs if log.get("mcp_method")])
        spans = self._build_spans([], merged_mcp_logs)

        x_request_id = ""
        for log in mcp_logs:
            if log.get("x_request_id"):
                x_request_id = log["x_request_id"]
                break

        # 计算总耗时：所有 span 的最大结束时间
        def calc_max_end_time_upstream(span_list, max_end=0):
            for span in span_list:
                start = span.get("start_offset_ms", 0) or 0
                latency = span.get("latency_ms", 0) or 0
                end_time = start + latency
                max_end = max(max_end, end_time)
                max_end = calc_max_end_time_upstream(span.get("children", []), max_end)
            return max_end

        total_latency_ms = calc_max_end_time_upstream(spans)

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

    def _search_all_layers(self) -> List[Dict]:  # noqa: C901, PLR0912
        """从 ES 中查询同一 request_id 或 x_request_id 的所有层级日志"""
        s = Search()

        # 根据传入的参数决定查询条件
        if self._request_id:
            s = s.filter("term", request_id=self._request_id)
        elif self._x_request_id:
            s = s.filter("term", x_request_id=self._x_request_id)
        else:
            return []

        # 添加默认时间范围（最近7天），避免ES查询超时或返回过多数据
        # 由于request_id/x_request_id是唯一的，时间范围不会影响结果准确性
        time_range = SmartTimeRange(time_range=7 * 24 * 60 * 60)  # 7天
        time_start, time_end = time_range.get_head_and_tail()
        s = s.filter(
            "range",
            **{
                self._es_time_field_name: {
                    "gte": time_utils.convert_second_to_epoch_millisecond(time_start),
                    "lte": time_utils.convert_second_to_epoch_millisecond(time_end),
                }
            },
        )

        s = s.source(fields=_CHAIN_OUTPUT_FIELDS)
        s = s.sort({self._es_time_field_name: {"order": "asc"}})
        s = s[:100]  # 限制最多 100 条

        try:
            data = self._es_client.execute_search(s.to_dict())
        except Exception as e:
            logger.exception(
                "failed to search mcp server chain logs for request_id=%s, x_request_id=%s",
                self._request_id,
                self._x_request_id,
            )
            # 重新抛出异常，让上层处理
            raise error_codes.INTERNAL.format(message=f"ES query failed: {str(e)}")

        hits = data.get("hits", {}).get("hits", [])
        logger.info(
            "search mcp server chain logs success, request_id=%s, x_request_id=%s, hits=%s",
            self._request_id,
            self._x_request_id,
            len(hits),
        )
        # 调试：记录每个 hit 的关键字段
        for i, hit in enumerate(hits):
            src = hit.get("_source", {})
            logger.info(
                "hit[%s]: request_id=%s, mcp_method=%s, has_latency=%s, latency=%s, "
                "has_params=%s, has_response=%s, has_tool=%s",
                i,
                src.get("request_id"),
                src.get("mcp_method"),
                bool(src.get("latency")),
                src.get("latency"),
                bool(src.get("params")),
                bool(src.get("response")),
                bool(src.get("tool")),
            )
        result = []
        for hit in hits:
            log = hit["_source"]
            # 调试日志：检查 sort 字段
            sort = hit.get("sort")
            logger.info(
                "hit sort field: hit_id=%s, sort=%s, is_list=%s, len=%s",
                hit.get("_id"),
                sort,
                isinstance(sort, list),
                len(sort) if isinstance(sort, list) else "N/A",
            )
            if sort and len(sort) > 0:
                log["timestamp"] = time_utils.convert_epoch_millisecond_to_second(sort[0])
                log["timestamp_ms"] = sort[0]
                logger.info("added timestamp=%s to log", log.get("timestamp"))
            else:
                logger.warning("sort field is missing or empty for hit_id=%s", hit.get("_id"))

            # 合并 __ext_json 中的字段到顶层（Filebeat 提取的字段）
            # Filebeat 可能将某些字段提取到 __ext_json 中，需要合并到顶层
            ext_json = log.get("__ext_json", {}) or {}
            if ext_json:
                # 合并所有 __ext_json 中的字段到顶层（优先使用 __ext_json 中的值）
                # 这解决了 Filebeat 字段提取位置不一致的问题
                for key, value in ext_json.items():
                    # 只在顶层字段为空或不存在时，才用 __ext_json 中的值覆盖
                    if (
                        value is not None
                        and value != ""
                        and (key not in log or log.get(key) is None or log.get(key) == "")
                    ):
                        log[key] = value

            # 排除文件访问日志：如果 __ext_json.method 为空，说明是文件访问日志
            # 真正的 HTTP 请求日志有 __ext_json.method 字段
            # 但 MCP 协议层日志（audit 日志）没有 __ext_json，通过 mcp_method 字段识别
            if not ext_json.get("method") and not log.get("mcp_method"):
                continue

            # 排除健康检查请求
            path = log.get("path", "")
            if "/health" in path and path.split("?")[0].split("/")[-1] == "/health":
                continue

            result.append(log)
        return result

    def _search_by_upstream_request_id(self) -> List[Dict]:
        """从 ES 中查询 upstream_request_id 匹配的日志

        当用户通过上游 API 返回的 request_id（即 biz-gateway 的 request_id）查询时使用。
        mcp-proxy 的 tools/call 日志中存储了 upstream_request_id 字段，
        该值是下游 API 响应中返回的 request_id。
        """
        if not self._upstream_request_id:
            return []

        s = Search()
        s = s.filter("term", upstream_request_id=self._upstream_request_id)

        # 添加默认时间范围（最近7天）
        time_range = SmartTimeRange(time_range=7 * 24 * 60 * 60)  # 7天
        time_start, time_end = time_range.get_head_and_tail()
        s = s.filter(
            "range",
            **{
                self._es_time_field_name: {
                    "gte": time_utils.convert_second_to_epoch_millisecond(time_start),
                    "lte": time_utils.convert_second_to_epoch_millisecond(time_end),
                }
            },
        )

        s = s.source(fields=_CHAIN_OUTPUT_FIELDS)
        s = s.sort({self._es_time_field_name: {"order": "asc"}})
        s = s[:100]  # 同一 upstream_request_id 可能关联多条日志

        try:
            data = self._es_client.execute_search(s.to_dict())
        except Exception:
            logger.exception(
                "failed to search mcp server logs by upstream_request_id=%s",
                self._upstream_request_id,
            )
            return []

        hits = data.get("hits", {}).get("hits", [])
        logger.info(
            "search mcp server logs by upstream_request_id=%s, hits=%s",
            self._upstream_request_id,
            len(hits),
        )
        result = []
        for hit in hits:
            log = hit["_source"]
            # 调试日志：检查 sort 字段
            sort = hit.get("sort")
            logger.info(
                "[upstream_request_id] hit sort field: hit_id=%s, sort=%s, is_list=%s, len=%s",
                hit.get("_id"),
                sort,
                isinstance(sort, list),
                len(sort) if isinstance(sort, list) else "N/A",
            )
            if sort and len(sort) > 0:
                log["timestamp"] = time_utils.convert_epoch_millisecond_to_second(sort[0])
                log["timestamp_ms"] = sort[0]
                logger.info("[upstream_request_id] added timestamp=%s to log", log.get("timestamp"))
            else:
                logger.warning("[upstream_request_id] sort field is missing or empty for hit_id=%s", hit.get("_id"))

            # 合并 __ext_json 中的字段到顶层（Filebeat 提取的字段）
            ext_json = log.get("__ext_json", {}) or {}
            if ext_json:
                for key, value in ext_json.items():
                    if (
                        value is not None
                        and value != ""
                        and (key not in log or log.get(key) is None or log.get(key) == "")
                    ):
                        log[key] = value

            # 排除文件访问日志
            if not ext_json.get("method") and not log.get("mcp_method"):
                continue

            # 排除健康检查请求
            path = log.get("path", "")
            if "/health" in path and path.split("?")[0].split("/")[-1] == "/health":
                continue

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
                "upstream": log.get("mcp_server_name", "") or "",
                "operation": f"{log.get('method', '')} {log.get('path', '')}",
                "latency": log.get("latency", ""),
                "latency_ms": latency_ms,
                "start_offset_ms": 0,
                "status": log.get("status"),
                "detail": {
                    "timestamp": log.get("timestamp"),
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

            # Audit 日志中 tool 字段存储工具配置字符串，需要提取工具名
            # 格式: "tool:[name:xxx,url:xxx, method:GET]"
            tool_str = log.get("tool", "")
            tool_name = log.get("tool_name", "")
            if not tool_name and tool_str:
                # 从 tool 字符串中提取工具名
                match = re.search(r"name:([^,]+)", tool_str)
                if match:
                    tool_name = match.group(1).strip()

            operation = mcp_method
            if tool_name:
                operation = f"{mcp_method} {tool_name}"

            # 计算 start_offset_ms: MCP 日志的 timestamp 是完成时间，
            # 所以 start = 完成时间 - 耗时 - base_ts
            start_offset_ms = 0
            if base_ts_ms is not None and log.get("timestamp_ms"):
                log_start_ms = log["timestamp_ms"] - (latency_ms or 0)
                start_offset_ms = max(0, round(log_start_ms - base_ts_ms, 3))

            # Audit 日志中的 request 字段存储请求参数
            params = log.get("params") or log.get("request")

            span = {
                "span_id": f"mcp_{i}",
                "parent_span_id": "http_entry" if http_entry else None,
                "layer": "mcp",
                "service": log.get("mcp_server_name") or log.get("gateway_name", ""),
                "upstream": log.get("gateway_name", "") or "",
                "operation": operation,
                "latency": log.get("latency", ""),
                "latency_ms": latency_ms,
                "start_offset_ms": start_offset_ms,
                "status": None,
                "detail": {
                    "timestamp": log.get("timestamp"),
                    "mcp_method": mcp_method,
                    "tool_name": tool_name,
                    "prompt_name": log.get("prompt_name"),
                    "tool": tool_str,  # 保留原始 tool 字符串
                    "params": params,
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

    def _merge_mcp_logs(self, mcp_logs: List[Dict]) -> List[Dict]:  # noqa: C901, PLR0912
        """合并同一 request_id + mcp_method + tool_name 的多条 MCP 日志

        mcp-proxy 会输出多份 MCP 层日志：
        - "call tool": 开始调用时记录，只有 request 字段
        - "call tool request params": 请求参数信息，包含 header, query, path, body
        - "call tool complete": 函数返回时记录，有完整的 params, response, latency 等字段
        - api log: 包含完整字段（但如果 filebeat 过滤可能不存在）

        需要合并这些日志，优先使用有 latency 字段的日志（即 "call tool complete"）。
        如果某些日志缺少 mcp_method，则按 request_id + tool_name 分组。
        """
        if not mcp_logs:
            return []

        # 按 (request_id, mcp_method, tool_name) 分组
        # 如果 mcp_method 缺失，则使用 tool_name 作为分组键的一部分
        log_groups: Dict[tuple, List[Dict]] = {}
        for idx, log in enumerate(mcp_logs):
            # 确保 tool_name 存在
            tool_name = log.get("tool_name", "")
            if not tool_name:
                # 尝试从 tool 字段提取
                tool_str = log.get("tool", "")
                if tool_str:
                    match = re.search(r"name:([^,]+)", tool_str)
                    if match:
                        tool_name = match.group(1).strip()

            # 如果 mcp_method 缺失，使用 tool_name 作为分组键
            mcp_method = log.get("mcp_method", "") or "tools/call"  # 默认值
            key = (
                log.get("request_id", ""),
                mcp_method,
                tool_name,
            )
            logger.info(
                "_merge_mcp_logs: log[%s] key=%s, has_latency=%s, has_params=%s, has_response=%s",
                idx,
                key,
                bool(log.get("latency")),
                bool(log.get("params")),
                bool(log.get("response")),
            )
            if key not in log_groups:
                log_groups[key] = []
            log_groups[key].append(log)

        logger.info("_merge_mcp_logs: total groups=%s, group_keys=%s", len(log_groups), list(log_groups.keys()))

        # 合并每组日志：优先使用有 latency 的日志（"call tool complete"）
        merged_logs = []
        for key, logs in log_groups.items():
            logger.info(
                "merging group %s: log_count=%s",
                key,
                len(logs),
            )
            if len(logs) == 1:
                merged_logs.append(logs[0])
                continue

            # 找到有 latency 的日志（通常是 "call tool complete"）
            complete_log = None
            for log in logs:
                if log.get("latency"):
                    complete_log = log
                    break

            if complete_log:
                # 使用 complete_log 作为基础，但补充其他日志中的非空字段
                merged = dict(complete_log)
                for log in logs:
                    if log is complete_log:
                        continue
                    for field_name, value in log.items():
                        if (
                            value is not None
                            and value != ""
                            and (field_name not in merged or merged[field_name] is None or merged[field_name] == "")
                        ):
                            merged[field_name] = value
                merged_logs.append(merged)
                logger.info(
                    "merged with complete_log: has_latency=%s, has_params=%s, has_response=%s",
                    bool(merged.get("latency")),
                    bool(merged.get("params")),
                    bool(merged.get("response")),
                )
            else:
                # 如果没有 complete log，使用第一个日志并合并其他字段
                merged = dict(logs[0])
                for log in logs[1:]:
                    for field_name, value in log.items():
                        if (
                            value is not None
                            and value != ""
                            and (field_name not in merged or merged[field_name] is None or merged[field_name] == "")
                        ):
                            merged[field_name] = value
                merged_logs.append(merged)
                logger.info("merged without complete_log")

        return merged_logs

    def _search_gateway_log(self, request_id: str, gateway_type: str = "upstream") -> Optional[Dict]:
        """通过 request_id 查询网关日志

        bk-apigateway 的 access_log ES 中，request_id 字段对应的是 X-Bkapi-Request-ID，
        而这个值就是 mcp-proxy 日志中的 request_id 字段（从上游传入的）。

        Args:
            request_id: 网关的请求 ID
            gateway_type: 网关类型，"upstream" 或 "downstream"
        """
        if not request_id:
            logger.warning("search_gateway_log called with empty request_id, gateway_type=%s", gateway_type)
            return None

        try:
            # 使用已有的 access_log LogSearchClient 查询
            # 注意：这里查询的是 bk-apigateway 的日志索引
            # 对于 upstream（bk-apigateway），request_id 是直接对应的
            # 对于 downstream（biz-gateway），如果它的日志也在同一个 ES 索引中，才能查询到
            logger.info(
                "searching %s gateway log with request_id=%s",
                gateway_type,
                request_id,
            )
            client = LogSearchClient(request_id=request_id, time_range=7 * 24 * 60 * 60)  # 7天
            total_count, logs = client.search_logs(offset=0, limit=1)
            logger.info(
                "%s gateway log search result: request_id=%s, total_count=%s, has_logs=%s",
                gateway_type,
                request_id,
                total_count,
                bool(logs),
            )
            if logs:
                log = logs[0]
                return {
                    "layer": "gateway",
                    "service": "bk-apigateway" if gateway_type == "upstream" else "biz-gateway",
                    "timestamp": log.get("timestamp"),
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
            logger.warning(
                "no %s gateway log found for request_id=%s, may be out of time range or not indexed",
                gateway_type,
                request_id,
            )
        except Exception:
            logger.exception(
                "failed to search %s gateway log for request_id=%s",
                gateway_type,
                request_id,
            )

        return None
