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
from django.utils.translation import gettext_lazy as _

# MCP Server 日志字段定义
# 基于 mcp-proxy LoggingMiddleware 输出的字段
MCP_SERVER_LOG_FIELDS = [
    {
        "label": _("请求ID"),
        "field": "request_id",
        "is_filter": True,
    },
    {
        "label": _("全链路请求ID"),
        "field": "x_request_id",
        "is_filter": True,
    },
    {
        "label": _("请求时间"),
        "field": "timestamp",
        "is_filter": False,
    },
    {
        "label": _("网关名称"),
        "field": "gateway_name",
        "is_filter": True,
    },
    {
        "label": _("MCP Server"),
        "field": "mcp_server_name",
        "is_filter": True,
    },
    {
        "label": _("MCP 方法"),
        "field": "mcp_method",
        "is_filter": True,
    },
    {
        "label": _("工具名称"),
        "field": "tool_name",
        "is_filter": True,
    },
    {
        "label": _("蓝鲸应用"),
        "field": "app_code",
        "is_filter": True,
    },
    {
        "label": _("蓝鲸用户"),
        "field": "bk_username",
        "is_filter": True,
    },
    {
        "label": _("客户端IP"),
        "field": "client_ip",
        "is_filter": True,
    },
    {
        "label": _("客户端ID"),
        "field": "client_id",
        "is_filter": True,
    },
    {
        "label": _("会话ID"),
        "field": "session_id",
        "is_filter": True,
    },
    {
        "label": _("请求参数"),
        "field": "params",
        "is_filter": False,
    },
    {
        "label": _("响应内容"),
        "field": "response",
        "is_filter": False,
    },
    {
        "label": _("请求体大小"),
        "field": "request_body_size",
        "is_filter": False,
    },
    {
        "label": _("响应体大小"),
        "field": "response_body_size",
        "is_filter": False,
    },
    {
        "label": _("耗时"),
        "field": "latency",
        "is_filter": True,
    },
    {
        "label": _("Trace ID"),
        "field": "trace_id",
        "is_filter": True,
    },
    {
        "label": _("错误"),
        "field": "error",
        "is_filter": True,
    },
]

MCP_SERVER_LOG_OUTPUT_FIELDS = [field["field"] for field in MCP_SERVER_LOG_FIELDS]
