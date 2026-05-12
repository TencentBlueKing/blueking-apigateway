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
from django.urls import path

from .views import (
    WorkbenchHandledGatewayPermissionListApi,
    WorkbenchHandledMCPPermissionListApi,
    WorkbenchMyApplyGatewayPermissionListApi,
    WorkbenchMyApplyMCPPermissionListApi,
    WorkbenchPendingGatewayPermissionListApi,
    WorkbenchPendingMCPPermissionListApi,
)

urlpatterns = [
    # 我的代办
    path(
        "pending/gateway-permissions/",
        WorkbenchPendingGatewayPermissionListApi.as_view(),
        name="personal_workbench.pending.gateway_permissions",
    ),
    path(
        "pending/mcp-permissions/",
        WorkbenchPendingMCPPermissionListApi.as_view(),
        name="personal_workbench.pending.mcp_permissions",
    ),
    # 我的申请
    path(
        "my-apply/gateway-permissions/",
        WorkbenchMyApplyGatewayPermissionListApi.as_view(),
        name="personal_workbench.my_apply.gateway_permissions",
    ),
    path(
        "my-apply/mcp-permissions/",
        WorkbenchMyApplyMCPPermissionListApi.as_view(),
        name="personal_workbench.my_apply.mcp_permissions",
    ),
    # 我的已办
    path(
        "handled/gateway-permissions/",
        WorkbenchHandledGatewayPermissionListApi.as_view(),
        name="personal_workbench.handled.gateway_permissions",
    ),
    path(
        "handled/mcp-permissions/",
        WorkbenchHandledMCPPermissionListApi.as_view(),
        name="personal_workbench.handled.mcp_permissions",
    ),
]
