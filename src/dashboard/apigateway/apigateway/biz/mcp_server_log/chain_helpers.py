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
from typing import Dict, List, Optional, Set

from apigateway.biz.mcp_server_log.constants import MCP_SERVER_LOG_FIELDS


def span_to_log(span: dict) -> dict:
    """将 span 转换为日志格式"""
    detail = span.get("detail", {})
    return {
        "layer": span.get("layer"),
        "service": span.get("service"),
        "operation": span.get("operation"),
        "latency": span.get("latency"),
        "latency_ms": span.get("latency_ms"),
        "status": span.get("status"),
        **detail,
    }


def _count_spans(span_list: List[Dict]) -> int:
    """递归统计 span 数量"""
    count = 0
    for span in span_list:
        count += 1
        count += _count_spans(span.get("children", []))
    return count


def _collect_services(span_list: List[Dict], services: Set[str]) -> None:
    """递归收集所有 service 名称"""
    for span in span_list:
        if span.get("service"):
            services.add(span["service"])
        _collect_services(span.get("children", []), services)


def _find_first_mcp_span(span_list: List[Dict]) -> Optional[Dict]:
    """递归查找第一个 MCP 层 span（含 mcp_method / tool_name）"""
    for span in span_list:
        if span.get("layer") == "mcp":
            return span
        result = _find_first_mcp_span(span.get("children", []))
        if result:
            return result
    return None


def _collect_latencies(span_list: List[Dict], total_latency_ms: float, latency_distribution: list) -> None:
    """递归收集各服务的耗时信息"""
    for span in span_list:
        service = span.get("service", "")
        latency_ms = span.get("latency_ms", 0) or 0
        start_offset_ms = span.get("start_offset_ms", 0) or 0
        layer = span.get("layer", "")
        operation = span.get("operation", "")

        if service:
            percentage = (latency_ms / total_latency_ms * 100) if total_latency_ms > 0 else 0
            latency_distribution.append(
                {
                    "service": service,
                    "upstream": span.get("upstream", ""),
                    "layer": layer,
                    "operation": operation,
                    "latency_ms": round(latency_ms, 2),
                    "start_offset_ms": round(start_offset_ms, 2),
                    "percentage": round(percentage, 1),
                }
            )

        _collect_latencies(span.get("children", []), total_latency_ms, latency_distribution)


def build_chain_summary(chain_data: dict) -> dict:
    """从调用链数据构建汇总信息"""
    spans = chain_data.get("spans", [])

    # 计算服务数（去重）和 span 总数
    services: Set[str] = set()
    _collect_services(spans, services)
    span_count = _count_spans(spans)

    # 计算状态：如果有任何 error 则为 failed
    status = "success"
    for span in spans:
        if span.get("detail", {}).get("error"):
            status = "failed"
            break

    # 从 HTTP 入口 span 提取公共信息，从第一个 MCP 子 span 提取 MCP 特有信息
    first_span = spans[0] if spans else {}
    first_detail = first_span.get("detail", {})

    mcp_span = _find_first_mcp_span(spans)
    mcp_detail = mcp_span.get("detail", {}) if mcp_span else {}

    # 获取 timestamp（从 chain_data 中获取）
    timestamp = chain_data.get("timestamp")

    return {
        "request_id": chain_data.get("request_id", ""),
        "x_request_id": chain_data.get("x_request_id", ""),
        "timestamp": timestamp,
        "total_latency_ms": chain_data.get("total_latency_ms", 0),
        "service_count": len(services),
        "span_count": span_count,
        "status": status,
        "mcp_server_name": mcp_detail.get("mcp_server_name", "") or first_detail.get("mcp_server_name", ""),
        "mcp_method": mcp_detail.get("mcp_method", ""),
        "tool_name": mcp_detail.get("tool_name", ""),
        "app_code": mcp_detail.get("app_code", "") or first_detail.get("app_code", ""),
        "client_ip": mcp_detail.get("client_ip", "") or first_detail.get("client_ip", ""),
        "error": mcp_detail.get("error", "") or first_detail.get("error", ""),
    }


def build_latency_distribution(chain_data: dict) -> list:
    """从调用链数据构建耗时分布

    返回各服务的耗时统计列表，按 start_offset_ms 排序
    """
    total_latency_ms = chain_data.get("total_latency_ms", 0) or 0
    latency_distribution: list[dict] = []

    _collect_latencies(chain_data.get("spans", []), total_latency_ms, latency_distribution)

    # 按 start_offset_ms 排序
    latency_distribution.sort(key=lambda x: x.get("start_offset_ms", 0))

    return latency_distribution


def enrich_chain_data(chain_data: dict) -> dict:
    """为调用链数据添加汇总统计信息"""
    summary = build_chain_summary(chain_data)
    latency_distribution = build_latency_distribution(chain_data)

    chain_data["span_count"] = summary["span_count"]
    chain_data["service_count"] = summary["service_count"]
    chain_data["status"] = summary["status"]
    chain_data["latency_distribution"] = latency_distribution

    return chain_data


def flatten_spans_to_logs(chain_data: dict) -> List[Dict]:
    """将调用链数据中的 spans 扁平化为日志列表"""
    logs = []
    for span in chain_data.get("spans", []):
        logs.append(span_to_log(span))
        logs.extend(span_to_log(child) for child in span.get("children", []))
    return logs


def get_log_fields() -> List[Dict]:
    """获取日志字段定义"""
    return MCP_SERVER_LOG_FIELDS
