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
from django.urls import include, path

from .views import (
    MCPServerLogChainApi,
    MCPServerLogDetailApi,
    MCPServerLogExportApi,
    MCPServerLogTimeChartRetrieveApi,
    MCPServerLogTraceApi,
    MCPServerSearchLogListApi,
)

urlpatterns = [
    path("", MCPServerSearchLogListApi.as_view(), name="mcp_server_log.logs"),
    path("export/", MCPServerLogExportApi.as_view(), name="mcp_server_log.export"),
    path("timechart/", MCPServerLogTimeChartRetrieveApi.as_view(), name="mcp_server_log.logs.time_chart"),
    path(
        "<slug:request_id>/",
        include(
            [
                path("", MCPServerLogDetailApi.as_view(), name="mcp_server_log.logs.detail"),
                path("chain/", MCPServerLogChainApi.as_view(), name="mcp_server_log.logs.chain"),
            ]
        ),
    ),
    path("trace/<slug:x_request_id>/", MCPServerLogTraceApi.as_view(), name="mcp_server_log.logs.trace"),
]
