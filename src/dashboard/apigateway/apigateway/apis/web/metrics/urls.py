# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from .views import QueryInstantApi, QueryRangeApi, QuerySummaryApi, QuerySummaryCallerListApi, QuerySummaryExportApi

urlpatterns = [
    path("query-range/", QueryRangeApi.as_view(), name="metrics.query_range"),
    path("query-instant/", QueryInstantApi.as_view(), name="metrics.query_instant"),
    path(
        "query-summary/",
        include(
            [
                path("", QuerySummaryApi.as_view(), name="metrics.query_summary"),
                path("caller/", QuerySummaryCallerListApi.as_view(), name="metrics.query_summary_caller"),
                path("export/", QuerySummaryExportApi.as_view(), name="metrics.query_summary_export"),
            ]
        ),
    ),
]
