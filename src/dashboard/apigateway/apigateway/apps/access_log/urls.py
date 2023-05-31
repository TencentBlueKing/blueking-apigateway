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

from apigateway.apps.access_log import views

urlpatterns = [
    path("", views.SearchLogsAPIView.as_view(), name="access_log.logs"),
    path("timechart/", views.LogTimeChartAPIView.as_view(), name="access_log.logs.timechart"),
    path("<slug:request_id>/link/", views.LogViewSet.as_view({"post": "link"}), name="access_log.logs.link"),
    path(
        "<slug:request_id>/",
        views.LogViewSet.as_view({"get": "retrieve"}, api_permission_exempt=True),
        name="access_log.logs.detail",
    ),
]
