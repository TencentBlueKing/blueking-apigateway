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

from apigateway.apps.esb.permission.views import AppComponentPermissionViewSet, AppPermissionApplyRecordViewSet

urlpatterns = [
    path(
        "apply-records/pending/",
        AppPermissionApplyRecordViewSet.as_view({"get": "list_pending"}),
        name="apigateway.apps.esb.permission.records.pending",
    ),
    path(
        "apply-records/handled/",
        AppPermissionApplyRecordViewSet.as_view({"get": "list_handled"}),
        name="apigateway.apps.esb.permission.records.handled",
    ),
    path(
        "apply-records/<int:id>/",
        AppPermissionApplyRecordViewSet.as_view({"get": "retrieve"}),
        name="apigateway.apps.esb.permission.records.detail",
    ),
    path(
        "apply-records/handle/",
        AppPermissionApplyRecordViewSet.as_view({"post": "batch_handle"}),
        name="apigateway.apps.esb.permissions.handle",
    ),
    path(
        "app-permissions/",
        AppComponentPermissionViewSet.as_view({"get": "list"}),
        name="apigateway.apps.esb.permissions.list",
    ),
    path(
        "app-permissions/renew/",
        AppComponentPermissionViewSet.as_view({"post": "renew"}),
        name="apigateway.apps.esb.permissions.handle",
    ),
    path(
        "app-permissions/delete/",
        AppComponentPermissionViewSet.as_view({"post": "destroy"}),
        name="apigateway.apps.esb.permissions.delete",
    ),
]
