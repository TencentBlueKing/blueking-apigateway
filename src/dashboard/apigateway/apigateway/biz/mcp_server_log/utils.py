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
import re
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from .log_search import MCPServerLogSearchClient

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


def parse_latency_ms(latency_str: str) -> Optional[float]:
    """将 Go 的 duration 字符串转换为毫秒数值

    支持格式: "37.36ms", "1.2s", "500µs", "100us", "2m", "1h"
    """
    if not latency_str:
        return None
    m = _LATENCY_PATTERN.match(latency_str.strip())
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2)
    return round(value * _UNIT_TO_MS.get(unit, 1.0), 3)


def calc_max_end_time(span_list: List[Dict], max_end: float = 0) -> float:
    """递归计算所有 span 的最大结束时间

    结束时间 = start_offset_ms + latency_ms
    """
    for span in span_list:
        start = span.get("start_offset_ms", 0) or 0
        latency = span.get("latency_ms", 0) or 0
        end_time = start + latency
        max_end = max(max_end, end_time)
        # 递归计算子 span
        max_end = calc_max_end_time(span.get("children", []), max_end)
    return max_end


def build_mcp_server_log_client(gateway_name: str, data: dict) -> "MCPServerLogSearchClient":
    """根据网关名称和查询参数构建 MCP Server 日志搜索客户端

    Args:
        gateway_name: 网关名称
        data: 查询参数字典
    """
    from .log_search import MCPServerLogSearchClient  # noqa: PLC0415

    return MCPServerLogSearchClient(
        gateway_name=gateway_name,
        mcp_server_name=data.get("mcp_server_name"),
        mcp_method=data.get("mcp_method"),
        tool_name=data.get("tool_name"),
        prompt_name=data.get("prompt_name"),
        app_code=data.get("app_code"),
        request_id=data.get("request_id"),
        x_request_id=data.get("x_request_id"),
        session_id=data.get("session_id"),
        status=data.get("status"),
        query=data.get("query"),
        include_conditions=data.get("include_conditions"),
        exclude_conditions=data.get("exclude_conditions"),
        time_start=data.get("time_start"),
        time_end=data.get("time_end"),
        time_range=data.get("time_range"),
    )
