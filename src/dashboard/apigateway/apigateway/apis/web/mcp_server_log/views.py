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

from .serializers import (
    MCPServerLogChainOutputSLZ,
    MCPServerLogOutputSLZ,
    MCPServerLogQueryInputSLZ,
    MCPServerLogTimeChartOutputSLZ,
)


def _build_mcp_server_log_client(request, data) -> MCPServerLogSearchClient:
    """根据请求参数构建 MCP Server 日志搜索客户端"""
    return MCPServerLogSearchClient(
        gateway_name=request.gateway.name,
        mcp_server_name=data.get("mcp_server_name"),
        mcp_method=data.get("mcp_method"),
        tool_name=data.get("tool_name"),
        app_code=data.get("app_code"),
        request_id=data.get("request_id"),
        x_request_id=data.get("x_request_id"),
        session_id=data.get("session_id"),
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
        query_serializer=MCPServerLogQueryInputSLZ,
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

        time_start_dt = datetime.fromtimestamp(int(data.get("time_start")))
        time_end_dt = datetime.fromtimestamp(int(data.get("time_end")))

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

    支持通过 request_id 查询完整的 MCP 请求日志，
    也支持通过 x_request_id 关联查询全链路日志。
    """

    def retrieve(self, request, request_id, *args, **kwargs):
        client = MCPServerLogSearchClient(request_id=request_id)
        total_count, logs = client.search_logs()

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
    """

    def retrieve(self, request, x_request_id, *args, **kwargs):
        client = MCPServerLogSearchClient(x_request_id=x_request_id)
        total_count, logs = client.search_logs()

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
    并关联上游 bk-apigateway 的日志，组装成调用链路树结构，
    用于前端瀑布图展示各环节耗时。

    返回结构包含:
    - spans: 按层级组织的调用链路 span 列表（含 latency_ms、start_offset_ms 等瀑布图绘制所需数据）
    - gateway_log: 上游 bk-apigateway 的日志详情（如果能关联到）
    """

    def retrieve(self, request, request_id, *args, **kwargs):
        client = MCPServerLogChainSearchClient(request_id=request_id)
        chain_data = client.search_chain()

        slz = MCPServerLogChainOutputSLZ(instance=chain_data)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: MCPServerLogOutputSLZ(many=True)},
        operation_description="根据 request_id 查询 MCP Server 日志（工具箱，无需网关权限）",
        tags=["WebAPI.MCPServer.Log"],
    ),
)
class MCPServerLogQueryApi(MCPServerLogDetailApi):
    """工具箱中根据 request_id 查询 MCP Server 日志

    该接口注册在不带 gateway_id 的顶层路径，供平台工具箱使用。
    仅需登录认证，跳过网关权限校验（与 LogDetailInfoApi 对齐）。
    """

    gateway_permission_exempt = True
