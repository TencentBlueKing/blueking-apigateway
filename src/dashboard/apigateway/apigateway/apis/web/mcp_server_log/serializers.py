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
from typing import List, Tuple

from django.utils.translation import gettext as _
from rest_framework import serializers


class MCPServerLogQueryInputSLZ(serializers.Serializer):
    """MCP Server 日志查询输入"""

    mcp_server_name = serializers.CharField(allow_blank=True, required=False, help_text="MCP Server 名称")
    mcp_method = serializers.CharField(
        allow_blank=True, required=False, help_text="MCP 方法 (initialize, tools/call, tools/list, etc.)"
    )
    tool_name = serializers.CharField(allow_blank=True, required=False, help_text="工具名称")
    app_code = serializers.CharField(allow_blank=True, required=False, help_text="蓝鲸应用编码")
    request_id = serializers.CharField(allow_blank=True, required=False, help_text="请求 ID")
    x_request_id = serializers.CharField(allow_blank=True, required=False, help_text="全链路请求 ID")
    session_id = serializers.CharField(allow_blank=True, required=False, help_text="会话 ID")
    query = serializers.CharField(
        label="查询条件", required=False, allow_blank=True, help_text="ES query_string 查询条件"
    )
    # ?include=xxx:yyy&include=aaa:bbb
    include = serializers.ListField(child=serializers.CharField(), required=False, help_text="包含条件")
    # ?exclude=xxx:yyy&exclude=aaa:bbb
    exclude = serializers.ListField(child=serializers.CharField(), required=False, help_text="排除条件")
    time_range = serializers.IntegerField(label="时间范围", required=False, min_value=0, help_text="时间范围（秒）")
    time_start = serializers.IntegerField(
        label="起始时间", required=False, min_value=0, help_text="起始时间（时间戳）"
    )
    time_end = serializers.IntegerField(label="结束时间", required=False, min_value=0, help_text="结束时间（时间戳）")
    offset = serializers.IntegerField(label="偏移量", required=False, min_value=0, default=0, help_text="偏移量")
    limit = serializers.IntegerField(label="限制条数", required=False, min_value=1, default=10, help_text="限制条数")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.MCPServerLogQueryInputSLZ"

    def validate(self, data):
        if not (data.get("time_start") and data.get("time_end") or data.get("time_range")):
            raise serializers.ValidationError(_("参数 time_start+time_end, time_range 必须一组有效。"))
        return data

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        include_conditions: List[Tuple[str, str]] = []
        if data.get("include"):
            for expr in data["include"]:
                if ":" not in expr:
                    continue
                k, v = expr.split(":", 1)
                include_conditions.append((k, v))

        if include_conditions:
            data["include_conditions"] = include_conditions

        exclude_conditions: List[Tuple[str, str]] = []
        if data.get("exclude"):
            for expr in data["exclude"]:
                if ":" not in expr:
                    continue
                k, v = expr.split(":", 1)
                exclude_conditions.append((k, v))

        if exclude_conditions:
            data["exclude_conditions"] = exclude_conditions

        return data


class MCPServerLogTimeChartOutputSLZ(serializers.Serializer):
    """时间分布图输出"""

    series = serializers.ListField(child=serializers.IntegerField(), help_text="时间序列数据")
    timeline = serializers.ListField(child=serializers.IntegerField(), help_text="时间轴")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.MCPServerLogTimeChartOutputSLZ"


class MCPServerLogOutputSLZ(serializers.Serializer):
    """MCP Server 日志输出"""

    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求 ID")
    x_request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="全链路请求 ID")
    timestamp = serializers.IntegerField(required=False, allow_null=True, help_text="请求时间戳")
    gateway_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="网关名称")
    mcp_server_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, help_text="MCP Server 名称"
    )
    mcp_method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="MCP 方法")
    tool_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="工具名称")
    app_code = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="蓝鲸应用编码")
    bk_username = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="蓝鲸用户")
    client_ip = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="客户端 IP")
    client_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="客户端 ID")
    session_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="会话 ID")
    params = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求参数")
    response = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="响应内容")
    request_body_size = serializers.IntegerField(required=False, allow_null=True, help_text="请求体大小")
    response_body_size = serializers.IntegerField(required=False, allow_null=True, help_text="响应体大小")
    latency = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="耗时")
    trace_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="Trace ID")
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="错误信息")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.MCPServerLogOutputSLZ"


class SpanDetailOutputSLZ(serializers.Serializer):
    """Span 详情输出"""

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.SpanDetailOutputSLZ"

    def to_representation(self, instance):
        # detail 是动态字典，直接返回
        return instance


class SpanOutputSLZ(serializers.Serializer):
    """调用链路 Span 输出"""

    span_id = serializers.CharField(help_text="Span ID")
    parent_span_id = serializers.CharField(allow_null=True, help_text="父 Span ID")
    layer = serializers.CharField(help_text="日志层级: http / mcp")
    service = serializers.CharField(help_text="服务名称")
    operation = serializers.CharField(help_text="操作名称")
    latency = serializers.CharField(allow_null=True, allow_blank=True, help_text="耗时(原始字符串)")
    latency_ms = serializers.FloatField(allow_null=True, help_text="耗时(毫秒)")
    start_offset_ms = serializers.FloatField(help_text="相对于入口请求开始的偏移量(毫秒)")
    status = serializers.IntegerField(allow_null=True, help_text="HTTP 状态码(仅 HTTP 层)")
    detail = SpanDetailOutputSLZ(help_text="Span 详情")
    children = serializers.SerializerMethodField(help_text="子 Span 列表")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.SpanOutputSLZ"

    def get_children(self, obj):
        children = obj.get("children", [])
        if not children:
            return []
        return SpanOutputSLZ(children, many=True).data


class GatewayLogOutputSLZ(serializers.Serializer):
    """上游网关日志输出"""

    layer = serializers.CharField(help_text="日志层级")
    service = serializers.CharField(help_text="服务名称")
    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求 ID")
    method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求方法")
    http_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求域名")
    http_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求路径")
    status = serializers.IntegerField(required=False, allow_null=True, help_text="响应状态码")
    request_duration = serializers.IntegerField(required=False, allow_null=True, help_text="请求总耗时(ms)")
    backend_duration = serializers.IntegerField(required=False, allow_null=True, help_text="后端请求耗时(ms)")
    stage = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="环境")
    resource_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="资源名称")
    backend_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端域名")
    backend_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端路径")
    backend_method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求方法")
    backend_scheme = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求协议")
    app_code = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="蓝鲸应用编码")
    client_ip = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="客户端 IP")
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="错误信息")
    code_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="错误编码名称")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.GatewayLogOutputSLZ"


class MCPServerLogChainOutputSLZ(serializers.Serializer):
    """MCP Server 调用链路输出"""

    request_id = serializers.CharField(help_text="请求 ID (X-Bkapi-Request-ID)")
    x_request_id = serializers.CharField(allow_blank=True, help_text="全链路请求 ID (X-Request-Id)")
    total_latency_ms = serializers.FloatField(help_text="总耗时(毫秒)")
    spans = SpanOutputSLZ(many=True, help_text="调用链路 Span 列表")
    gateway_log = GatewayLogOutputSLZ(allow_null=True, help_text="上游网关日志")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server_log.serializers.MCPServerLogChainOutputSLZ"
