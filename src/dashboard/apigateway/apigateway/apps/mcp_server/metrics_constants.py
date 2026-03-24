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
from blue_krill.data_types.enum import EnumField, StructuredEnum


class MCPServerMetricsRangeEnum(StructuredEnum):
    """MCP Server 时序图指标类型"""

    # 请求总量趋势
    REQUESTS = EnumField("requests")
    # 2XX 状态码请求趋势
    REQUESTS_2XX = EnumField("requests_2xx")
    # 非 2XX 状态码请求趋势（按 status 分组）
    NON_2XX_STATUS = EnumField("non_2xx_status")
    # 按 app_code 分组的请求趋势
    APP_REQUESTS = EnumField("app_requests")
    # 按 resource_name/tool_name 分组的请求趋势
    TOOL_REQUESTS = EnumField("tool_requests")
    # 网关到后端响应时间 P95
    RESPONSE_TIME_95TH = EnumField("response_time_95th")
    # 按 method（MCP 方法）分组的请求趋势
    METHOD_REQUESTS = EnumField("method_requests")


class MCPServerMetricsInstantEnum(StructuredEnum):
    """MCP Server 瞬时值指标类型"""

    # 总请求数
    REQUESTS_TOTAL = EnumField("requests_total")
    # 非 2XX 请求数
    NON_2XX_TOTAL = EnumField("non_2xx_total")
