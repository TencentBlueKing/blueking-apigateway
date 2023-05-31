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

from apigateway.apps.permission import views

urlpatterns = [
    # app-permission
    path(
        "app-permissions/",
        views.AppPermissionViewSet.as_view({"get": "list", "post": "create"}),
        name="permissions.app-permissions",
    ),
    path(
        "app-permissions/batch/",
        views.AppPermissionBatchViewSet.as_view({"post": "renew"}),
        name="permissions.app-permissions.renew",
    ),
    # app-permission export
    path(
        "app-permissions/export/",
        views.AppPermissionViewSet.as_view({"post": "export_permissions"}),
        name="permissions.app-permissions.export",
    ),
    path(
        "app-permissions/bk-app-codes/",
        views.AppPermissionViewSet.as_view({"get": "get_bk_app_codes"}),
        name="permissions.app-permissions.get_bk_app_codes",
    ),
    # delete 不支持传参，改用 post
    path(
        "app-permissions/delete/",
        views.AppPermissionBatchViewSet.as_view({"post": "destroy"}),
        name="permissions.app-permissions.delete",
    ),
    # app-permission-apply
    path(
        "app-permission-apply/",
        views.AppPermissionApplyViewSet.as_view({"get": "list"}),
        name="permissions.app-permission-apply",
    ),
    path(
        "app-permission-apply/<int:id>/",
        views.AppPermissionApplyViewSet.as_view({"get": "retrieve"}),
        name="permissions.app-permission-apply.detail",
    ),
    path(
        "app-permission-apply/batch/",
        views.AppPermissionApplyBatchViewSet.as_view({"post": "post"}),
        name="permissions.app-permission-apply.batch",
    ),
    # app-permission-record
    path(
        "app-permission-records/",
        views.AppPermissionRecordViewSet.as_view({"get": "list"}),
        name="permissions.app-permission-records",
    ),
    path(
        "app-permission-records/<int:id>/",
        views.AppPermissionRecordViewSet.as_view({"get": "retrieve"}),
        name="permissions.app-permission-records.detail",
    ),
]
