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
"""apigateway URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path, re_path
from django.views.i18n import set_language

from apigateway.apis.web.monitor.views import AlarmRecordSummaryListApi
from apigateway.common.swagger import schema_view

urlpatterns = [
    # /metrics
    path("", include("django_prometheus.urls")),
    # /healthz
    path("backend/", include("apigateway.healthz.urls")),
    # /admin42
    path("backend/admin42/", admin.site.urls),
    # /userinfo
    path("backend/accounts/", include("apigateway.account.urls")),
    # esb
    path("backend/esb/", include("apigateway.apps.esb.urls")),
    # open api
    path("backend/api/v1/", include("apigateway.apis.open.urls")),
    # api-support backend/docs urls
    path("backend/docs/", include("apigateway.apis.web.docs.urls")),
    # web api
    path("backend/i18n/setlang/", set_language, name="set_language"),
    path("backend/version-log/", include("apigateway.apis.web.version_log.urls")),
    path("backend/settings/", include("apigateway.apis.web.setting.urls")),
    path("backend/gateways/", include("apigateway.apis.web.gateway.urls")),
    path("backend/gateways/<int:gateway_id>/logs/", include("apigateway.apis.web.access_log.urls")),
    path("backend/gateways/<int:gateway_id>/tests/", include("apigateway.apis.web.api_test.urls")),
    path("backend/gateways/<int:gateway_id>/resources/", include("apigateway.apis.web.resource.urls")),
    path("backend/gateways/<int:gateway_id>/labels/", include("apigateway.apis.web.label.urls")),
    path("backend/gateways/<int:gateway_id>/metrics/", include("apigateway.apis.web.metrics.urls")),
    path("backend/gateways/<int:gateway_id>/monitors/", include("apigateway.apis.web.monitor.urls")),
    path("backend/gateways/<int:gateway_id>/permissions/", include("apigateway.apis.web.permission.urls")),
    path("backend/gateways/<int:gateway_id>/backends/", include("apigateway.apis.web.backend.urls")),
    path("backend/gateways/<int:gateway_id>/stages/", include("apigateway.apis.web.stage.urls")),
    path("backend/gateways/<int:gateway_id>/docs/", include("apigateway.apis.web.resource_doc.urls")),
    path("backend/gateways/<int:gateway_id>/releases/", include("apigateway.apis.web.release.urls")),
    path("backend/gateways/<int:gateway_id>/plugins/", include("apigateway.apis.web.plugin.urls")),
    path("backend/gateways/<int:gateway_id>/resource-versions/", include("apigateway.apis.web.resource_version.urls")),
    path("backend/gateways/<int:gateway_id>/sdks/", include("apigateway.apis.web.sdk.urls")),
    path("backend/gateways/<int:gateway_id>/audits/", include("apigateway.apis.web.audit.urls")),
    # todo 不应该放在顶层，后续要想办法挪到下层
    path(
        "backend/gateways/monitors/alarm/records/summary/",
        AlarmRecordSummaryListApi.as_view(),
        name="monitors.alarm_records.summary",
    ),
    # notice
    path("backend/notice/", include(("bk_notice_sdk.urls", "notice"), namespace="notice")),
]


# backend/docs/
urlpatterns += [
    # drf-yasg automatically generated documents
    re_path(
        r"^backend/docs/auto/swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^backend/docs/auto/swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"
    ),
    re_path(r"^backend/docs/auto/redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
