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

from apigateway.apis.open.permission import views

v1_open_api_patterns = [
    path(
        "apis/<slug:gateway_name>/permissions/apply/",
        views.AppPermissionApplyV1APIView.as_view(),
        name="openapi.permission.apply.api",
    ),
    path(
        "apis/<slug:gateway_name>/permissions/grant/",
        views.AppPermissionGrantViewSet.as_view({"post": "grant"}),
        name="openapi.permission.grant",
    ),
    path(
        "apis/<slug:gateway_name>/permissions/revoke/",
        views.RevokeAppPermissionViewSet.as_view({"delete": "revoke"}),
        name="openapi.permission.revoke",
    ),
]

v1_inner_api_patterns = [
    path(
        "apis/<int:gateway_id>/permissions/resources/",
        views.ResourceViewSet.as_view({"get": "list"}),
        name="openapi.permission.resource",
    ),
    path(
        "apis/<int:gateway_id>/permissions/app-permissions/allow-apply-by-api/",
        views.AppGatewayPermissionViewSet.as_view({"get": "allow_apply_by_gateway"}),
        name="openapi.permission.allow_apply_by_api",
    ),
    path(
        "apis/<int:gateway_id>/permissions/app-permissions/apply/",
        views.PaaSAppPermissionApplyAPIView.as_view(),
        name="openapi.permission.apply.paas",
    ),
    path(
        "apis/permissions/renew/",
        views.AppPermissionRenewAPIView.as_view(),
        name="openapi.permission.renew",
    ),
    path(
        "apis/permissions/app-permissions/",
        views.AppPermissionViewSet.as_view({"get": "list"}),
        name="openapi.permission.app-permissions",
    ),
    path(
        "apis/permissions/apply-records/",
        views.AppPermissionRecordViewSet.as_view({"get": "list"}),
        name="openapi.permission.app-records",
    ),
    path(
        "apis/permissions/apply-records/<int:record_id>/",
        views.AppPermissionRecordViewSet.as_view({"get": "retrieve"}),
        name="openapi.permission.app-record-detail",
    ),
]

urlpatterns = v1_open_api_patterns + v1_inner_api_patterns
