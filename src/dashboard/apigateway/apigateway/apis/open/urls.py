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

from apigateway.apis.open.esb.permission import views as esb_permission_views
from apigateway.apis.open.metrics.views import StatisticsV1ViewSet
from apigateway.apis.open.support.views import APISDKV1ViewSet

urlpatterns = [
    # NOTE: deprecated
    path("apis/", include("apigateway.apis.open.gateway.urls")),
    path("gateways/", include("apigateway.apis.open.gateway.urls")),
    # TODO: why?
    path(
        "apis/latest-sdks/", APISDKV1ViewSet.as_view({"get": "list_latest_sdks"}), name="openapi.support.latest_sdks"
    ),
    path(
        "apis/metrics/statistics/query-api-metrics/",
        StatisticsV1ViewSet.as_view({"get": "query_api_metrics"}, name="openapi.metrics.query_api_metrics"),
    ),
    path("", include("apigateway.apis.open.released.urls")),
    path("", include("apigateway.apis.open.support.urls")),
    path("", include("apigateway.apis.open.permission.urls")),
    path("", include("apigateway.apis.open.stage.urls")),
    path("", include("apigateway.apis.open.resource.urls")),
    path("", include("apigateway.apis.open.resource_version.urls")),
    path("", include("apigateway.apis.open.monitor.urls")),
]

urlpatterns += [
    path("esb/systems/", include("apigateway.apis.open.esb.system.urls")),
    path("esb/systems/<int:system_id>/permissions/", include("apigateway.apis.open.esb.permission.urls")),
    path(
        "esb/systems/permissions/renew/",
        esb_permission_views.AppPermissionRenewAPIView.as_view({"post": "renew"}),
        name="openapi.esb.permission.renew",
    ),
    path(
        "esb/systems/permissions/app-permissions/",
        esb_permission_views.AppPermissionViewSet.as_view({"get": "list"}),
        name="openapi.esb.permission.app-permissions",
    ),
    path(
        "esb/systems/permissions/apply-records/",
        esb_permission_views.AppPermissionApplyRecordViewSet.as_view({"get": "list"}),
        name="openapi.esb.permission.app-records",
    ),
    path(
        "esb/systems/permissions/apply-records/<int:record_id>/",
        esb_permission_views.AppPermissionApplyRecordViewSet.as_view({"get": "retrieve"}),
        name="openapi.esb.permission.app-record-detail",
    ),
]
