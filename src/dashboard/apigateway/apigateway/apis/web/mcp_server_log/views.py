# -*- coding: utf-8 -*-
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
import csv
from datetime import datetime
from io import StringIO

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.biz.mcp_server_log.chain_search import MCPServerLogChainSearchClient
from apigateway.biz.mcp_server_log.constants import MCP_SERVER_LOG_FIELDS
from apigateway.biz.mcp_server_log.log_search import MCPServerLogSearchClient
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse
from apigateway.utils.time import SmartTimeRange

from .serializers import (
    MCPServerLogChainOutputSLZ,
    MCPServerLogOutputSLZ,
    MCPServerLogQueryInputSLZ,
    MCPServerLogQuerySummaryOutputSLZ,
    MCPServerLogTimeChartOutputSLZ,
)


def _span_to_log(span: dict) -> dict:
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


def _build_mcp_server_log_client(request, data) -> MCPServerLogSearchClient:
    """根据请求参数构建 MCP Server 日志搜索客户端"""
    return MCPServerLogSearchClient(
        gateway_name=request.gateway.name,
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


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=MCPServerLogQueryInputSLZ,
        responses={status.HTTP_200_OK: MCPServerLogTimeChartOutputSLZ()},
        operation_description="查询 MCP Server 日志时间分布图",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogTimeChartRetrieveApi(generics.RetrieveAPIView):
    """MCP Server 日志时间分布图"""

    def retrieve(self, request, *args, **kwargs):
        slz = MCPServerLogQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        client = _build_mcp_server_log_client(request, data)
        slz = MCPServerLogTimeChartOutputSLZ(instance=client.get_time_chart())
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogOutputSLZ(many=True)},
        operation_description="查询 MCP Server 日志列表",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerSearchLogListApi(generics.ListAPIView):
    """MCP Server 日志列表"""

    def list(self, request, *args, **kwargs):
        slz = MCPServerLogQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        client = _build_mcp_server_log_client(request, data)
        total_count, logs = client.search_logs(
            offset=data["offset"],
            limit=data["limit"],
        )

        paginator = LimitOffsetPaginator(total_count, data["offset"], data["limit"])

        results = paginator.get_paginated_data(logs)
        results["fields"] = MCP_SERVER_LOG_FIELDS

        return OKJsonResponse(data=results)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=MCPServerLogQueryInputSLZ,
        responses={status.HTTP_200_OK: "file/csv"},
        operation_description="导出 MCP Server 日志",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogExportApi(generics.RetrieveAPIView):
    """MCP Server 日志导出"""

    def get(self, request, *args, **kwargs):
        limit = 10000
        slz = MCPServerLogQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        client = _build_mcp_server_log_client(request, data)
        total_count, logs = client.search_logs(
            offset=0,
            limit=limit,
        )

        gateway = request.gateway

        # Handle both time_start+time_end and time_range scenarios
        smart_time_range = SmartTimeRange(
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            time_range=data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        time_start_dt = datetime.fromtimestamp(time_start)
        time_end_dt = datetime.fromtimestamp(time_end)

        formatted_time_start = time_start_dt.strftime("%Y%m%d%H%M%S")
        formatted_time_end = time_end_dt.strftime("%Y%m%d%H%M%S")

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(field_dict["field"] for field_dict in MCP_SERVER_LOG_FIELDS)
        for log in logs:
            writer.writerow([log.get(field_dict["field"]) for field_dict in MCP_SERVER_LOG_FIELDS])

        content = output.getvalue()
        output.close()

        response = DownloadableResponse(
            content, filename=f"{gateway.name}-mcp-server-{formatted_time_start}-{formatted_time_end}-logs.csv"
        )
        response.charset = "utf-8-sig" if "windows" in request.headers.get("User-Agent", "").lower() else "utf-8"
        return response


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogOutputSLZ(many=True)},
        operation_description="根据 request_id 获取 MCP Server 日志详情",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogDetailApi(generics.RetrieveAPIView):
    """根据 request_id 获取 MCP Server 日志详情

    支持通过 request_id 查询完整的 MCP 请求日志。
    如需通过 x_request_id 关联查询全链路日志，请使用 MCPServerLogTraceApi。

    注意：此接口查询所有层级的日志（HTTP 层、MCP 协议层、审计日志），
    不强制要求 mcp_method 字段存在。
    """

    def retrieve(self, request, request_id, *args, **kwargs):
        # 使用 MCPServerLogChainSearchClient 查询所有层级的日志
        # 因为它不强制过滤 mcp_method，可以查到 HTTP 层和审计日志
        client = MCPServerLogChainSearchClient(request_id=request_id)
        chain_data = client.search_chain()

        # 如果没找到数据，尝试作为 x_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(x_request_id=request_id)
            chain_data = client.search_chain_by_x_request_id()

        # 如果还是没找到数据，尝试作为 upstream_request_id 查询
        # upstream_request_id 是上游 API 返回的 request_id，存储在 MCP 层日志中
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(upstream_request_id=request_id)
            chain_data = client.search_chain_by_upstream_request_id()

        # 将 spans 扁平化为日志列表
        logs = []
        for span in chain_data.get("spans", []):
            logs.append(_span_to_log(span))
            logs.extend(_span_to_log(child) for child in span.get("children", []))

        total_count = len(logs)
        paginator = LimitOffsetPaginator(total_count, 0, total_count)

        results = paginator.get_paginated_data(logs)
        results["fields"] = MCP_SERVER_LOG_FIELDS

        return OKJsonResponse(data=results)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogOutputSLZ(many=True)},
        operation_description="根据 x_request_id 查询全链路关联日志",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogTraceApi(generics.RetrieveAPIView):
    """根据 x_request_id（全链路请求 ID）查询关联日志

    可以关联 MCP Proxy 的请求日志与上下游网关的日志，
    实现跨服务的请求追踪。

    注意：此接口查询所有层级的日志（HTTP 层、MCP 协议层、审计日志），
    不强制要求 mcp_method 字段存在。
    """

    def retrieve(self, request, x_request_id, *args, **kwargs):
        # 使用 MCPServerLogChainSearchClient 查询所有层级的日志
        # 因为它不强制过滤 mcp_method，可以查到 HTTP 层和审计日志
        client = MCPServerLogChainSearchClient(request_id="", x_request_id=x_request_id)
        chain_data = client.search_chain_by_x_request_id()

        # 将 spans 扁平化为日志列表
        logs = []
        for span in chain_data.get("spans", []):
            logs.append(_span_to_log(span))
            logs.extend(_span_to_log(child) for child in span.get("children", []))

        # 添加网关日志到列表开头（如果有）
        if chain_data.get("upstream_gateway_log"):
            upstream_log = chain_data["upstream_gateway_log"]
            upstream_log["layer"] = "gateway_upstream"
            logs.insert(0, upstream_log)

        if chain_data.get("downstream_gateway_log"):
            downstream_log = chain_data["downstream_gateway_log"]
            downstream_log["layer"] = "gateway_downstream"
            logs.insert(0, downstream_log)

        total_count = len(logs)
        paginator = LimitOffsetPaginator(total_count, 0, total_count)

        results = paginator.get_paginated_data(logs)
        results["fields"] = MCP_SERVER_LOG_FIELDS

        return OKJsonResponse(data=results)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogChainOutputSLZ()},
        operation_description="根据 request_id 查询 MCP Server 调用链路（瀑布图数据）",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogChainApi(generics.RetrieveAPIView):
    """MCP Server 调用链路查询

    通过 request_id 查询同一请求的所有层级日志（HTTP 层、MCP 协议层），
    并关联上游 bk-apigateway 和下游 biz-gateway 的日志，组装成调用链路树结构，
    用于前端瀑布图展示各环节耗时。

    返回结构包含:
    - spans: 按层级组织的调用链路 span 列表（含 latency_ms、start_offset_ms 等瀑布图绘制所需数据）
    - upstream_gateway_log: 上游 bk-apigateway 的日志详情（如果能关联到）
    - downstream_gateway_log: 下游 biz-gateway 的日志详情（如果能关联到）
    - span_count: Span 总数
    - service_count: 服务总数
    - status: 请求状态 (success/failed)
    - latency_distribution: 耗时分布（各服务耗时统计）
    """

    def retrieve(self, request, request_id, *args, **kwargs):
        client = MCPServerLogChainSearchClient(request_id=request_id)
        chain_data = client.search_chain()

        # 如果没找到数据，尝试作为 x_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(x_request_id=request_id)
            chain_data = client.search_chain_by_x_request_id()

        # 如果还是没找到数据，尝试作为 upstream_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(upstream_request_id=request_id)
            chain_data = client.search_chain_by_upstream_request_id()

        # 添加汇总统计信息
        chain_data = _enrich_chain_data(chain_data)

        slz = MCPServerLogChainOutputSLZ(instance=chain_data)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogOutputSLZ(many=True)},
        operation_description="根据 request_id 或 x_request_id 查询 MCP Server 日志（工具箱，无需网关权限）",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogQueryApi(generics.RetrieveAPIView):
    """工具箱中根据 request_id 或 x_request_id 查询 MCP Server 日志

    该接口注册在不带 gateway_id 的顶层路径，供平台工具箱使用。
    仅需登录认证，跳过网关权限校验（与 LogDetailInfoApi 对齐）。

    支持通过 request_id（X-Bkapi-Request-ID）或 x_request_id（X-Request-Id）查询。
    接口会自动识别传入的 ID 类型并进行相应查询。

    注意：此接口查询所有层级的日志（HTTP 层、MCP 协议层、审计日志），
    不强制要求 mcp_method 字段存在。
    """

    gateway_permission_exempt = True

    def retrieve(self, request, request_id, *args, **kwargs):
        # 使用 MCPServerLogChainSearchClient 查询所有层级的日志
        # 因为它不强制过滤 mcp_method，可以查到 HTTP 层和审计日志

        # 尝试作为 request_id 查询
        client = MCPServerLogChainSearchClient(request_id=request_id)
        chain_data = client.search_chain()

        # 如果没找到数据，尝试作为 x_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(x_request_id=request_id)
            chain_data = client.search_chain_by_x_request_id()

        # 如果还是没找到数据，尝试作为 upstream_request_id 查询
        # upstream_request_id 是上游 API 返回的 request_id，存储在 MCP 层日志中
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(upstream_request_id=request_id)
            chain_data = client.search_chain_by_upstream_request_id()

        # 将 spans 扁平化为日志列表
        logs = []
        for span in chain_data.get("spans", []):
            logs.append(_span_to_log(span))
            logs.extend(_span_to_log(child) for child in span.get("children", []))

        # 添加网关日志到列表开头（如果有）
        # 注意：不同查询方式返回的网关日志字段名可能不同
        if chain_data.get("upstream_gateway_log"):
            upstream_log = chain_data["upstream_gateway_log"]
            upstream_log["layer"] = "gateway_upstream"
            logs.insert(0, upstream_log)

        if chain_data.get("downstream_gateway_log"):
            downstream_log = chain_data["downstream_gateway_log"]
            downstream_log["layer"] = "gateway_downstream"
            logs.insert(0, downstream_log)

        total_count = len(logs)
        paginator = LimitOffsetPaginator(total_count, 0, total_count)

        results = paginator.get_paginated_data(logs)
        results["fields"] = MCP_SERVER_LOG_FIELDS

        return OKJsonResponse(data=results)


def _build_chain_summary(chain_data: dict) -> dict:
    """从调用链数据构建汇总信息"""
    spans = chain_data.get("spans", [])

    # 计算服务数（去重）
    services = set()
    span_count = 0

    def count_spans(span_list):
        nonlocal span_count
        for span in span_list:
            span_count += 1
            if span.get("service"):
                services.add(span["service"])
            count_spans(span.get("children", []))

    count_spans(spans)

    # 计算状态：如果有任何 error 则为 failed
    status = "success"
    for span in spans:
        if span.get("detail", {}).get("error"):
            status = "failed"
            break

    # 从 HTTP 入口 span 提取公共信息，从第一个 MCP 子 span 提取 MCP 特有信息
    first_span = spans[0] if spans else {}
    first_detail = first_span.get("detail", {})

    # 递归查找第一个 MCP 层 span（含 mcp_method / tool_name）
    def find_first_mcp_span(span_list):
        for span in span_list:
            if span.get("layer") == "mcp":
                return span
            result = find_first_mcp_span(span.get("children", []))
            if result:
                return result
        return None

    mcp_span = find_first_mcp_span(spans)
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


def _build_latency_distribution(chain_data: dict) -> list:
    """从调用链数据构建耗时分布

    返回各服务的耗时统计列表，按 start_offset_ms 排序
    """
    spans = chain_data.get("spans", [])
    total_latency_ms = chain_data.get("total_latency_ms", 0) or 0
    latency_distribution = []

    def collect_latencies(span_list):
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

            collect_latencies(span.get("children", []))

    collect_latencies(spans)

    # 按 start_offset_ms 排序
    latency_distribution.sort(key=lambda x: x.get("start_offset_ms", 0))

    return latency_distribution


def _enrich_chain_data(chain_data: dict) -> dict:
    """为调用链数据添加汇总统计信息"""
    summary = _build_chain_summary(chain_data)
    latency_distribution = _build_latency_distribution(chain_data)

    chain_data["span_count"] = summary["span_count"]
    chain_data["service_count"] = summary["service_count"]
    chain_data["status"] = summary["status"]
    chain_data["latency_distribution"] = latency_distribution

    return chain_data


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogQuerySummaryOutputSLZ()},
        operation_description="根据 request_id 或 x_request_id 查询 MCP Server 调用链汇总信息（工具箱，无需网关权限）",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogQuerySummaryApi(generics.RetrieveAPIView):
    """工具箱中根据 request_id 或 x_request_id 查询 MCP Server 调用链汇总信息

    该接口注册在不带 gateway_id 的顶层路径，供平台工具箱使用。
    仅需登录认证，跳过网关权限校验。

    返回调用链的汇总信息，包括：
    - 产生时间、总耗时、服务数、Span 总数、状态等
    """

    gateway_permission_exempt = True

    def retrieve(self, request, request_id, *args, **kwargs):
        # 尝试作为 request_id 查询
        client = MCPServerLogChainSearchClient(request_id=request_id)
        chain_data = client.search_chain()

        # 如果没找到数据，尝试作为 x_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(x_request_id=request_id)
            chain_data = client.search_chain_by_x_request_id()

        # 如果还是没找到数据，尝试作为 upstream_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(upstream_request_id=request_id)
            chain_data = client.search_chain_by_upstream_request_id()

        # 构建汇总信息
        summary = _build_chain_summary(chain_data)
        summary["latency_distribution"] = _build_latency_distribution(chain_data)

        slz = MCPServerLogQuerySummaryOutputSLZ(instance=summary)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogChainOutputSLZ()},
        operation_description="根据 request_id 或 x_request_id 查询 MCP Server 调用链路详情（工具箱，无需网关权限）",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogQueryChainApi(generics.RetrieveAPIView):
    """工具箱中根据 request_id 或 x_request_id 查询 MCP Server 调用链路详情

    该接口注册在不带 gateway_id 的顶层路径，供平台工具箱使用。
    仅需登录认证，跳过网关权限校验。

    返回完整的调用链路数据，包括：
    - spans: 调用链路 Span 列表（含 latency_ms、start_offset_ms 等瀑布图绘制所需数据）
    - upstream_gateway_log: 上游网关日志（如果能关联到）
    - downstream_gateway_log: 下游网关日志（如果能关联到）
    - span_count: Span 总数
    - service_count: 服务总数
    - status: 请求状态 (success/failed)
    - latency_distribution: 耗时分布（各服务耗时统计）
    """

    gateway_permission_exempt = True

    def retrieve(self, request, request_id, *args, **kwargs):
        # 尝试作为 request_id 查询
        client = MCPServerLogChainSearchClient(request_id=request_id)
        chain_data = client.search_chain()

        # 如果没找到数据，尝试作为 x_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(x_request_id=request_id)
            chain_data = client.search_chain_by_x_request_id()

        # 如果还是没找到数据，尝试作为 upstream_request_id 查询
        if not chain_data.get("spans"):
            client = MCPServerLogChainSearchClient(upstream_request_id=request_id)
            chain_data = client.search_chain_by_upstream_request_id()

        # 添加汇总统计信息
        chain_data = _enrich_chain_data(chain_data)

        slz = MCPServerLogChainOutputSLZ(instance=chain_data)
        return OKJsonResponse(data=slz.data)
