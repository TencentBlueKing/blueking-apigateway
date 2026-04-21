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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.mcp_server.metrics_constants import (
    MCPServerMetricsInstantEnum,
    MCPServerMetricsRangeEnum,
)
from apigateway.apps.metrics.constants import MetricsStepEnum
from apigateway.service.prometheus.mcp_server_dimension import (
    MCPServerMetricsInstantFactory,
    MCPServerMetricsRangeFactory,
)
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.time import MetricsSmartTimeRange

from .serializers import (
    MCPServerMetricsQueryInstantInputSLZ,
    MCPServerMetricsQueryRangeInputSLZ,
)


class MCPServerQueryRangeApi(generics.ListAPIView):
    """MCP Server 时序图指标查询 API

    支持的 metrics 类型:
    - requests: 请求总量趋势
    - requests_2xx: 2XX 状态码请求趋势
    - non_2xx_status: 非 2XX 状态码请求趋势（按 error_code 分组）
    - app_requests: 按 app_code 分组的请求趋势
    - tool_requests: 按 tool_name 分组的请求趋势
    - response_time_95th: P95 响应时间分布
    - method_requests: 按 MCP 方法分组的请求趋势
    """

    @swagger_auto_schema(
        query_serializer=MCPServerMetricsQueryRangeInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        operation_description="查询 MCP Server 时序图 metrics",
        tags=["WebAPI.MCPServer.Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = MCPServerMetricsQueryRangeInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        smart_time_range = MetricsSmartTimeRange(
            data.get("time_start"),
            data.get("time_end"),
            data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        if data.get("step", MetricsStepEnum.AUTO.value) == MetricsStepEnum.AUTO.value:
            step = smart_time_range.get_interval()
        else:
            step = data.get("step")

        metrics = MCPServerMetricsRangeFactory.create_metrics(MCPServerMetricsRangeEnum(data["metrics"]))
        result = metrics.query_range(
            gateway_name=request.gateway.name,
            mcp_server_name=data.get("mcp_server_name"),
            app_code=data.get("app_code"),
            start=time_start,
            end=time_end,
            step=step,
        )

        # Filter out empty series targets
        series = [s for s in result.get("series", []) if s["target"].strip()]
        if series:
            result["series"] = series

        return OKJsonResponse(data=result)


class MCPServerQueryInstantApi(generics.ListAPIView):
    """MCP Server 瞬时值指标查询 API

    支持的 metrics 类型:
    - requests_total: 总请求数
    - non_2xx_total: 非 2XX 请求数
    """

    @swagger_auto_schema(
        query_serializer=MCPServerMetricsQueryInstantInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        operation_description="查询 MCP Server 瞬时值 metrics",
        tags=["WebAPI.MCPServer.Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = MCPServerMetricsQueryInstantInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        smart_time_range = MetricsSmartTimeRange(
            data.get("time_start"),
            data.get("time_end"),
            data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        step = smart_time_range.get_interval()

        metrics = MCPServerMetricsInstantFactory.create_metrics(MCPServerMetricsInstantEnum(data["metrics"]))
        result = metrics.query_instant(
            gateway_name=request.gateway.name,
            mcp_server_name=data.get("mcp_server_name"),
            app_code=data.get("app_code"),
            start=time_start,
            end=time_end,
            step=step,
        )

        return OKJsonResponse(data=result)
