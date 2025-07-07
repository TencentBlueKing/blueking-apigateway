# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from . import views

urlpatterns = [
    # /api/v2/open/ 用于第三方系统调用查询一些网关信息，正常情况禁止提供`写`接口，避免非网关的 related_app 对网关进行了修改
    # 作为 resource 注册到网关时
    # 1. isPublic: true              公开
    # 2. allowApplyPermission: true  允许申请权限
    # 3. authConfig:
    #      userVerifiedRequired: false   不需要用户认证
    #      appVerifiedRequired: true     需要应用认证
    #      resourcePermissionRequired: true  需要资源权限
    path(
        "gateways/",
        include(
            [
                # GET /api/v2/open/gateways/
                path("", views.GatewayListApi.as_view(), name="openapi.v2.open.gateway.list"),
                path(
                    "<slug:gateway_name>/",
                    include(
                        [
                            # GET /api/v2/open/gateways/{gateway_name}/
                            path("", views.GatewayRetrieveApi.as_view(), name="openapi.v2.open.gateway.retrieve"),
                            # NOTE: this url been redirected to core-api, so no need to implement this
                            # GET /api/v2/open/gateways/{gateway_name}/public_key/
                            # POST /api/v2/open/gateways/{gateway_name}/permissions/apply/
                            path(
                                "permissions/apply/",
                                views.GatewayAppPermissionApplyAPI.as_view(),
                                name="openapi.v2.open.gateway.permissions.apply",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "mcp-servers/",
        include(
            [
                # GET /api/v2/open/mcp-servers/
                path(
                    "",
                    views.MCPServerListApi.as_view(),
                    name="openapi.v2.open.mcp_server.list",
                ),
                # GET /api/v2/open/mcp-servers/{mcp_server_id}/permissions/
                path(
                    "<int:mcp_server_id>/permissions/",
                    views.MCPServerPermissionListApi.as_view(),
                    name="openapi.v2.open.mcp_server.permissions.list",
                ),
                path(
                    "permissions/",
                    include(
                        [
                            # GET /api/v2/open/mcp-servers/permissions/
                            path(
                                "",
                                views.MCPServerAppPermissionListApi.as_view(),
                                name="openapi.v2.open.mcp_server.app.permissions.list",
                            ),
                            # POST /api/v2/open/mcp-servers/permissions/apply/
                            path(
                                "apply/",
                                views.MCPServerAppPermissionApplyCreateApi.as_view(),
                                name="openapi.v2.open.mcp_server.app.permissions.apply",
                            ),
                            # GET /api/v2/open/mcp-servers/permissions/apply-records/
                            path(
                                "apply-records/",
                                views.MCPServerAppPermissionRecordListApi.as_view(),
                                name="openapi.v2.open.mcp_server.app.permissions.apply-records.list",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # GET /api/v2/open/user/mcp-servers/
    path(
        "user/mcp-servers/",
        views.UserMCPServerListApi.as_view(),
        name="openapi.v2.open.user.mcp_server.list",
    ),
]
