# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
    # app-resource-permission
    path(
        "app-resource-permissions/",
        include(
            [
                path(
                    "", views.AppResourcePermissionListCreateApi.as_view(), name="permissions.app-resource-permissions"
                ),
                path(
                    "renew/",
                    views.AppResourcePermissionRenewApi.as_view(),
                    name="permissions.app-resource-permissions.renew",
                ),
                path(
                    "export/",
                    views.AppResourcePermissionExportApi.as_view(),
                    name="permissions.app-resource-permissions.export",
                ),
                path(
                    "delete/",
                    views.AppResourcePermissionDeleteApi.as_view(),
                    name="permissions.app-resource-permissions.delete",
                ),
                path(
                    "bk-app-codes/",
                    views.AppResourcePermissionAppCodeListApi.as_view(),
                    name="permissions.app-resource-permissions.get_bk_app_codes",
                ),
            ]
        ),
    ),
    # app-gateway-permission
    path(
        "app-gateway-permissions/",
        include(
            [
                path(
                    "", views.AppGatewayPermissionListCreateApi.as_view(), name="permissions.app-gateway-permissions"
                ),
                path(
                    "renew/",
                    views.AppGatewayPermissionRenewApi.as_view(),
                    name="permissions.app-gateway-permissions.renew",
                ),
                path(
                    "export/",
                    views.AppGatewayPermissionExportApi.as_view(),
                    name="permissions.app-gateway-permissions.export",
                ),
                path(
                    "delete/",
                    views.AppGatewayPermissionDeleteApi.as_view(),
                    name="permissions.app-gateway-permissions.delete",
                ),
                path(
                    "bk-app-codes/",
                    views.AppGatewayPermissionAppCodeListApi.as_view(),
                    name="permissions.app-gateway-permissions.get_bk_app_codes",
                ),
            ]
        ),
    ),
    # app-permission-apply
    path(
        "app-permission-apply/",
        include(
            [
                path("", views.AppPermissionApplyListApi.as_view(), name="permissions.app-permission-apply"),
                path(
                    "<int:id>/",
                    views.AppPermissionApplyRetrieveApi.as_view(),
                    name="permissions.app-permission-apply.detail",
                ),
                path(
                    "approval/",
                    views.AppPermissionApplyApprovalApi.as_view(),
                    name="permissions.app-permission-apply.approval",
                ),
            ]
        ),
    ),
    # app-permission-record
    path(
        "app-permission-records/",
        views.AppPermissionRecordListApi.as_view(),
        name="permissions.app-permission-records",
    ),
    path(
        "app-permission-records/<int:id>/",
        views.AppPermissionRecordRetrieveApi.as_view(),
        name="permissions.app-permission-records.detail",
    ),
]
