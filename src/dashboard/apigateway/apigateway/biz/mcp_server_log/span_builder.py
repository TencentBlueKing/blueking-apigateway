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
from typing import Dict, List, Optional

from apigateway.biz.mcp_server_log.utils import parse_latency_ms

logger = logging.getLogger(__name__)


def build_spans(http_logs: List[Dict], mcp_logs: List[Dict]) -> List[Dict]:
    """将日志构建为 span 树结构"""
    spans = []

    # HTTP 入口 span (如果存在)
    http_entry = None
    if http_logs:
        log = http_logs[0]
        latency_ms = parse_latency_ms(log.get("latency", ""))
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
    base_ts_ms = _calc_base_timestamp_ms(http_entry, http_logs, mcp_logs)

    for i, log in enumerate(mcp_logs):
        latency_ms = parse_latency_ms(log.get("latency", ""))
        mcp_method = log.get("mcp_method", "")

        # Audit 日志中 tool 字段存储工具配置字符串，需要提取工具名
        tool_name = _extract_tool_name(log)

        operation = mcp_method
        if tool_name:
            operation = f"{mcp_method} {tool_name}"

        # 计算 start_offset_ms: MCP 日志的 timestamp 是完成时间，
        # 所以 start = 完成时间 - 耗时 - base_ts
        start_offset_ms = _calc_start_offset_ms(base_ts_ms, log, latency_ms)

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
                "tool": log.get("tool", ""),  # 保留原始 tool 字符串
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


def merge_mcp_logs(mcp_logs: List[Dict]) -> List[Dict]:  # noqa: C901, PLR0912
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
        tool_name = _extract_tool_name(log)

        # 如果 mcp_method 缺失，使用 tool_name 作为分组键
        mcp_method = log.get("mcp_method", "") or "tools/call"  # 默认值
        key = (
            log.get("request_id", ""),
            mcp_method,
            tool_name,
        )
        logger.debug(
            "merge_mcp_logs: log[%s] key=%s, has_latency=%s, has_params=%s, has_response=%s",
            idx,
            key,
            bool(log.get("latency")),
            bool(log.get("params")),
            bool(log.get("response")),
        )
        if key not in log_groups:
            log_groups[key] = []
        log_groups[key].append(log)

    logger.debug("merge_mcp_logs: total groups=%s, group_keys=%s", len(log_groups), list(log_groups.keys()))

    # 合并每组日志：优先使用有 latency 的日志（"call tool complete"）
    merged_logs = []
    for key, logs in log_groups.items():
        logger.debug(
            "merging group %s: log_count=%s",
            key,
            len(logs),
        )
        if len(logs) == 1:
            merged_logs.append(logs[0])
            continue

        merged = _merge_log_group(logs)
        merged_logs.append(merged)

    return merged_logs


def _calc_base_timestamp_ms(
    http_entry: Optional[Dict], http_logs: List[Dict], mcp_logs: List[Dict]
) -> Optional[float]:
    """计算用于 start_offset_ms 的基准时间戳"""
    if http_entry and http_logs and http_logs[0].get("timestamp_ms"):
        # HTTP 入口的 timestamp 是请求完成后记录的，所以 MCP span 的偏移需要用 HTTP 开始时间
        # 近似用 HTTP 完成时间 - HTTP 耗时
        http_latency_ms = http_entry.get("latency_ms") or 0
        return http_logs[0]["timestamp_ms"] - http_latency_ms
    if mcp_logs and mcp_logs[0].get("timestamp_ms"):
        return mcp_logs[0]["timestamp_ms"]
    return None


def _calc_start_offset_ms(base_ts_ms: Optional[float], log: Dict, latency_ms: Optional[float]) -> float:
    """计算 span 的 start_offset_ms"""
    if base_ts_ms is not None and log.get("timestamp_ms"):
        log_start_ms = log["timestamp_ms"] - (latency_ms or 0)
        return max(0, round(log_start_ms - base_ts_ms, 3))
    return 0


def _extract_tool_name(log: Dict) -> str:
    """从日志中提取工具名称

    优先使用 tool_name 字段，如果没有则从 tool 字符串中提取。
    格式: "tool:[name:xxx,url:xxx, method:GET]"
    """
    tool_name = log.get("tool_name", "")
    if tool_name:
        return tool_name

    tool_str = log.get("tool", "")
    if tool_str:
        match = re.search(r"name:([^,]+)", tool_str)
        if match:
            return match.group(1).strip()
    return ""


def _merge_log_group(logs: List[Dict]) -> Dict:
    """合并同一组的日志，优先使用有 latency 的日志"""
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
        logger.debug(
            "merged with complete_log: has_latency=%s, has_params=%s, has_response=%s",
            bool(merged.get("latency")),
            bool(merged.get("params")),
            bool(merged.get("response")),
        )
        return merged
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
    logger.debug("merged without complete_log")
    return merged
