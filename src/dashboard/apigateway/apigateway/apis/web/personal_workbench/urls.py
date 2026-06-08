# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
    WorkbenchGatewayFilterOptionListApi,
    WorkbenchHandledGatewayPermissionListApi,
    WorkbenchHandledMCPPermissionListApi,
    WorkbenchMCPGatewayFilterOptionListApi,
    WorkbenchMCPServerFilterOptionListApi,
    WorkbenchMyApplyGatewayPermissionListApi,
    WorkbenchMyApplyMCPPermissionListApi,
    WorkbenchPendingGatewayPermissionListApi,
    WorkbenchPendingMCPPermissionListApi,
)

gateway_permission_patterns = [
    path("pending/", WorkbenchPendingGatewayPermissionListApi.as_view(), name="workbench.permissions.gateway.pending"),
    path("applied/", WorkbenchMyApplyGatewayPermissionListApi.as_view(), name="workbench.permissions.gateway.applied"),
    path("handled/", WorkbenchHandledGatewayPermissionListApi.as_view(), name="workbench.permissions.gateway.handled"),
]

mcp_permission_patterns = [
    path("pending/", WorkbenchPendingMCPPermissionListApi.as_view(), name="workbench.permissions.mcp.pending"),
    path("applied/", WorkbenchMyApplyMCPPermissionListApi.as_view(), name="workbench.permissions.mcp.applied"),
    path("handled/", WorkbenchHandledMCPPermissionListApi.as_view(), name="workbench.permissions.mcp.handled"),
]

urlpatterns = [
    path(
        "filter-options/gateways/",
        WorkbenchGatewayFilterOptionListApi.as_view(),
        name="workbench.filter_options.gateways",
    ),
    path(
        "filter-options/mcp-servers/",
        WorkbenchMCPServerFilterOptionListApi.as_view(),
        name="workbench.filter_options.mcp_servers",
    ),
    path(
        "filter-options/mcp-gateways/",
        WorkbenchMCPGatewayFilterOptionListApi.as_view(),
        name="workbench.filter_options.mcp_gateways",
    ),
    path("permissions/gateway/", include(gateway_permission_patterns)),
    path("permissions/mcp/", include(mcp_permission_patterns)),
]
