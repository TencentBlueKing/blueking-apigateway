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
from django.urls import path

from . import views

urlpatterns = [
    # app-resource-permission
    path(
        "app-resource-permissions/",
        views.AppResourcePermissionListCreateApi.as_view({"get": "list", "post": "create"}),
        name="permissions.app-resource-permissions",
    ),
    path(
        "app-resource-permissions/renew/",
        views.AppResourcePermissionRenewApi.as_view({"post": "renew"}),
        name="permissions.app-resource-permissions.renew",
    ),
    # app-permission export
    path(
        "app-resource-permissions/export/",
        views.AppResourcePermissionExportApi.as_view({"post": "export"}),
        name="permissions.app-resource-permissions.export",
    ),
    path(
        "app-resource-permissions/bk-app-codes/",
        views.AppResourcePermissionAppCodeApi.as_view({"get": "list"}),
        name="permissions.app-resource-permissions.get_bk_app_codes",
    ),
    # delete 不支持传参，改用 post
    path(
        "app-resource-permissions/delete/",
        views.AppResourcePermissionDeleteApi.as_view({"post": "destroy"}),
        name="permissions.app-resource-permissions.delete",
    ),
    # app-gateway-permission
    path(
        "app-gateway-permissions/",
        views.AppGatewayPermissionListCreateApi.as_view({"get": "list", "post": "create"}),
        name="permissions.app-gateway-permissions",
    ),
    path(
        "app-gateway-permissions/renew/",
        views.AppGatewayPermissionRenewApi.as_view({"post": "renew"}),
        name="permissions.app-gateway-permissions.renew",
    ),
    # app-permission export
    path(
        "app-gateway-permissions/export/",
        views.AppGatewayPermissionExportApi.as_view({"post": "export"}),
        name="permissions.app-gateway-permissions.export",
    ),
    path(
        "app-gateway-permissions/bk-app-codes/",
        views.AppGatewayPermissionAppCodeApi.as_view({"get": "list"}),
        name="permissions.app-gateway-permissions.get_bk_app_codes",
    ),
    # delete 不支持传参，改用 post
    path(
        "app-gateway-permissions/delete/",
        views.AppGatewayPermissionDeleteApi.as_view({"post": "destroy"}),
        name="permissions.app-gateway-permissions.delete",
    ),
    # app-permission-apply
    path(
        "app-permission-apply/",
        views.AppPermissionApplyListApi.as_view({"get": "list"}),
        name="permissions.app-permission-apply",
    ),
    path(
        "app-permission-apply/<int:id>/",
        views.AppPermissionApplyRetrieveApi.as_view({"get": "retrieve"}),
        name="permissions.app-permission-apply.detail",
    ),
    path(
        "app-permission-apply/approval/",
        views.AppPermissionApplyApprovalApi.as_view({"post": "post"}),
        name="permissions.app-permission-apply.approval",
    ),
    # app-permission-record
    path(
        "app-permission-records/",
        views.AppPermissionRecordListApi.as_view({"get": "list"}),
        name="permissions.app-permission-records",
    ),
    path(
        "app-permission-records/<int:id>/",
        views.AppPermissionRecordRetrieveApi.as_view({"get": "retrieve"}),
        name="permissions.app-permission-records.detail",
    ),
]
