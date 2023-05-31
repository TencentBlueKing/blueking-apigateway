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

from apigateway.apps.esb.status import views

urlpatterns = [
    path(
        "systems/summary/",
        views.SysAllSummaryView.as_view(),
        name="apigateway.apps.esb.status.api.systems.summary",
    ),
    path(
        "systems/unstable/",
        views.SysUnstableSystemsView.as_view(),
        name="apigateway.apps.esb.status.api.systems.unstable",
    ),
    path(
        "systems/events/timeline/",
        views.SysEventsTimeline.as_view(),
        name="apigateway.apps.esb.status.api.systems.events.timeline",
    ),
    path(
        "systems/<slug:system_name>/summary/",
        views.SysSummaryView.as_view(),
        name="apigateway.apps.esb.status.api.systems.summary",
    ),
    path(
        "systems/<slug:system_name>/details/group_by/",
        views.SysDetailsGroupByView.as_view(),
        name="apigateway.apps.esb.status.api.systems.details.group_by",
    ),
    path(
        "systems/<slug:system_name>/date_histogram/",
        views.SysDateHistogramView.as_view(),
        name="apigateway.apps.esb.status.api.systems.date_histogram",
    ),
    path(
        "systems/<slug:system_name>/errors/",
        views.SysErrorsView.as_view(),
        name="apigateway.apps.esb.status.api.systems.errors",
    ),
]
