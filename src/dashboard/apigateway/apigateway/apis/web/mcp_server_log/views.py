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

from apigateway.biz.mcp_server_log.chain_query import (
    search_chain_logs_by_any_id,
    search_chain_logs_with_gateway_by_any_id,
    search_chain_summary_by_any_id,
    search_chain_with_summary_by_any_id,
)
from apigateway.biz.mcp_server_log.constants import MCP_SERVER_LOG_FIELDS
from apigateway.biz.mcp_server_log.utils import build_mcp_server_log_client
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

        client = build_mcp_server_log_client(request.gateway.name, data)
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

        client = build_mcp_server_log_client(request.gateway.name, data)
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

        client = build_mcp_server_log_client(request.gateway.name, data)
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
        result = search_chain_logs_by_any_id(request_id)
        return OKJsonResponse(data=result)


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
        result = search_chain_logs_with_gateway_by_any_id(x_request_id)
        return OKJsonResponse(data=result)


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
        chain_data = search_chain_with_summary_by_any_id(request_id)
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
        result = search_chain_logs_with_gateway_by_any_id(request_id)
        return OKJsonResponse(data=result)


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
        summary = search_chain_summary_by_any_id(request_id)
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
        chain_data = search_chain_with_summary_by_any_id(request_id)
        slz = MCPServerLogChainOutputSLZ(instance=chain_data)
        return OKJsonResponse(data=slz.data)
