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
    # /api/v2/inner/ 用于 paasv3 内部调用; 鉴权：来自于网关（主动授权）
    # 所有的接口必须隐藏 + 不允许申请权限（需主动授权）
    # 作为 resource 注册到网关时
    # 1. isPublic: false              不公开
    # 2. allowApplyPermission: false  不允许申请权限 (走的是 主动授权)
    # 3. authConfig:
    #      userVerifiedRequired: false   不需要用户认证
    #      appVerifiedRequired: true     需要应用认证
    #      resourcePermissionRequired: true 需要资源权限
    path(
        "gateways/",
        include(
            [
                # GET /api/v2/inner/gateways/
                path("", views.GatewayListApi.as_view(), name="openapi.v2.inner.gateway.list"),
                path(
                    "<slug:gateway_name>/",
                    include(
                        [
                            # GET /api/v2/inner/gateways/{gateway_name}/
                            path("", views.GatewayRetrieveApi.as_view(), name="openapi.v2.inner.gateway.retrieve"),
                            path(
                                "permissions/",
                                include(
                                    [
                                        # GET /api/v2/inner/gateways/{gateway_name}/permissions/resources/
                                        path(
                                            "resources/",
                                            views.GatewayPermissionResourceListApi.as_view(),
                                            name="openapi.v2.inner.gateway.permission.resource.list",
                                        ),
                                        # GET /api/v2/inner/gateways/{gateway_name}/permissions/app-permissions/allow-apply-by-gateway/
                                        path(
                                            "app-permissions/allow-apply-by-gateway/",
                                            views.GatewayAppPermissionIsAllowedApplyCheckApi.as_view(),
                                            name="openapi.v2.inner.gateway.permission.allow_apply_by_gateway",
                                        ),
                                        # POST /api/v2/inner/gateways/{gateway_name}/permissions/app-permissions/apply/
                                        path(
                                            "app-permissions/apply/",
                                            views.GatewayAppPermissionApplyCreateApi.as_view(),
                                            name="openapi.v2.inner.gateway.permission.apply",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                path(
                    "permissions/",
                    include(
                        [
                            # POST /api/v2/inner/gateways/permissions/renew/
                            path(
                                "renew/",
                                views.AppPermissionRenewApi.as_view(),
                                name="openapi.v2.inner.permission.renew",
                            ),
                            # GET /api/v2/inner/gateways/permissions/app-permissions/
                            path(
                                "app-permissions/",
                                views.AppPermissionListApi.as_view(),
                                name="openapi.v2.inner.permission.app-permissions",
                            ),
                            # GET /api/v2/inner/gateways/permissions/apply-records/
                            path(
                                "apply-records/",
                                views.AppPermissionRecordListApi.as_view(),
                                name="openapi.v2.inner.permission.apply-records",
                            ),
                            # GET /api/v2/inner/gateways/permissions/apply-records/{record_id}/
                            path(
                                "apply-records/<int:record_id>/",
                                views.AppPermissionRecordRetrieveApi.as_view(),
                                name="openapi.v2.inner.permission.apply-record-detail",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "esb/systems/",
        include(
            [
                # GET /api/v2/inner/esb/systems/
                path(
                    "",
                    views.EsbSystemListApi.as_view(),
                    name="openapi.v2.inner.esb.systems.list",
                ),
                path(
                    "<int:system_id>/",
                    include(
                        [
                            # GET /api/v2/inner/esb/systems/{system_id}/permissions/components/
                            path(
                                "permissions/components/",
                                views.EsbPermissionComponentListApi.as_view(),
                                name="openapi.v2.inner.esb.permission.apply",
                            ),
                            # POST /api/v2/inner/esb/systems/{system_id}/permissions/apply/
                            path(
                                "permissions/apply/",
                                views.EsbAppPermissionApplyCreateApi.as_view(),
                                name="openapi.v2.inner.esb.permission.apply",
                            ),
                        ]
                    ),
                ),
                path(
                    "permissions/",
                    include(
                        [
                            # POST /api/v2/inner/esb/systems/permissions/renew/
                            path(
                                "renew/",
                                views.EsbAppPermissionRenewPutApi.as_view(),
                                name="openapi.v2.inner.esb.permission.renew",
                            ),
                            # GET /api/v2/inner/esb/systems/permissions/app-permissions/
                            path(
                                "app-permissions/",
                                views.EsbAppPermissionListApi.as_view(),
                                name="openapi.v2.inner.esb.permission.app-permissions",
                            ),
                            # GET /api/v2/inner/esb/systems/permissions/apply-records/
                            path(
                                "apply-records/",
                                views.EsbAppPermissionApplyRecordListApi.as_view(),
                                name="openapi.v2.inner.esb.permission.apply-records",
                            ),
                            # GET /api/v2/inner/esb/systems/permissions/apply-records/{record_id}/
                            path(
                                "apply-records/<int:record_id>/",
                                views.EsbAppPermissionApplyRecordRetrieveApi.as_view(),
                                name="openapi.v2.inner.esb.permission.apply-record-detail",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "mcp-server/permissions/",
        include(
            [
                # GET /api/v2/inner/mcp-server/permissions/
                path(
                    "",
                    views.MCPServerPermissionListApi.as_view(),
                    name="openapi.v2.inner.mcp_server.permission.list",
                ),
                # POST /api/v2/inner/mcp-server/permissions/apply/
                path(
                    "apply/",
                    views.MCPServerAppPermissionApplyCreateApi.as_view(),
                    name="openapi.v2.inner.mcp_server.permission.apply",
                ),
                # GET /api/v2/inner/mcp-server/permissions/app-permissions/
                path(
                    "app-permissions/",
                    views.MCPServerAppPermissionListApi.as_view(),
                    name="openapi.v2.inner.mcp_server.permission.app-permissions",
                ),
                # GET /api/v2/inner/mcp-server/permissions/apply-records/
                path(
                    "apply-records/",
                    views.MCPServerAppPermissionRecordListApi.as_view(),
                    name="openapi.v2.inner.mcp_server.permission.apply-records",
                ),
                # GET /api/v2/inner/mcp-server/permissions/apply-records/{record_id}/
                path(
                    "apply-records/<int:record_id>/",
                    views.MCPServerAppPermissionRecordRetrieveApi.as_view(),
                    name="openapi.v2.inner.mcp_server.permission.apply-record-detail",
                ),
            ]
        ),
    ),
]
