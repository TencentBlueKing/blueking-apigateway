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
    # /api/v2/sync/ 用于 SDK 同步网关; 鉴权：来自于网关+related_apps
    # 问题：是否隐藏 + 不可申请权限？还是说公开 + 说明只能是 related_app 操作？
    # 作为 resource 注册到网关时
    # 1. isPublic: true              公开
    # 2. allowApplyPermission: false  不允许申请权限 (走的是 related_apps 判定)
    # 3. authConfig:
    #      userVerifiedRequired: false   不需要用户认证
    #      appVerifiedRequired: true     需要应用认证
    #      resourcePermissionRequired: false 不需要资源权限
    path(
        "gateways/<slug:gateway_name>/",
        include(
            [
                # POST /api/v2/sync/gateways/{gateway_name}/
                path("", views.GatewaySyncApi.as_view(), name="openapi.v2.sync.gateway.sync"),
                path(
                    "stages/",
                    include(
                        [
                            # POST /api/v2/sync/gateways/{gateway_name}/stages/
                            path(
                                "",
                                views.GatewayStageSyncViewSet.as_view(),
                                name="openapi.v2.sync.gateway.stages.sync",
                            ),
                        ]
                    ),
                ),
                path(
                    "resources/",
                    include(
                        [
                            # POST /api/v2/sync/gateways/{gateway_name}/resources/
                            path(
                                "",
                                views.GatewayResourceSyncApi.as_view(),
                                name="openapi.v2.sync.gateway.resources.sync",
                            ),
                        ]
                    ),
                ),
                path(
                    "resource-docs/",
                    include(
                        [
                            # POST /api/v2/sync/gateways/{gateway_name}/resource-docs/
                            path(
                                "",
                                views.DocImportByArchiveApi.as_view(),
                                name="openapi.v2.sync.resource_doc.import",
                            ),
                        ]
                    ),
                ),
                # POST /api/v2/sync/gateways/{gateway_name}/sdk/
                path(
                    "sdk/",
                    views.SDKGenerateApi.as_view(),
                    name="openapi.v2.sync.sdk.generate",
                ),
                path(
                    "related-apps/",
                    include(
                        [
                            # POST /api/v2/sync/gateways/{gateway_name}/related-apps/
                            path(
                                "",
                                views.GatewayRelatedAppAddApi.as_view(),
                                name="openapi.v2.sync.gateway.add_related_apps",
                            ),
                            # TODO:
                            # DELETE /api/v2/sync/gateways/{gateway_name}/related-apps/{app_code}/
                            # path(
                            #     "{app_code}/",
                            #     views.GatewayRelatedAppDeleteApi.as_view(),
                            #     name="openapi.v2.sync.gateway.delete_related_apps",
                            # ),
                        ]
                    ),
                ),
                path(
                    "permissions/",
                    include(
                        [
                            # GET /api/v2/sync/gateways/{gateway_name}/permissions/
                            path(
                                "",
                                views.GatewayPermissionListApi.as_view(),
                                name="openapi.v2.sync.gateway.permissions.list",
                            ),
                            # POST /api/v2/sync/gateways/{gateway_name}/permissions/grant/
                            path(
                                "grant/",
                                views.GatewayAppPermissionGrantApi.as_view(),
                                name="openapi.v2.sync.gateway.permissions.grant",
                            ),
                        ]
                    ),
                ),
                path(
                    "resource_versions/",
                    include(
                        [
                            # GET /api/v2/sync/gateways/{gateway_name}/resource_versions/latest/
                            path(
                                "latest/",
                                views.ResourceVersionLatestRetrieveApi.as_view(),
                                name="openapi.v2.sync.gateway.resource_versions.latest.retrieve",
                            ),
                            # GET list /api/v2/sync/gateways/{gateway_name}/resource_versions/
                            # POST  creat /api/v2/sync/gateways/{gateway_name}/resource_versions/
                            path(
                                "",
                                views.ResourceVersionListCreateApi.as_view(),
                                name="openapi.v2.sync.resource_versions.list_create",
                            ),
                            # POST /api/v2/sync/gateways/{gateway_name}/resource_versions/release/
                            path(
                                "release/",
                                views.ResourceVersionReleaseApi.as_view(),
                                name="openapi.v2.sync.resource_version.release",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
