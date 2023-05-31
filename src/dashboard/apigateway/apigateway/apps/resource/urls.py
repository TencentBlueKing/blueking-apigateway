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

from .views import (
    ProxyPathViewSet,
    ResourceBatchViewSet,
    ResourceImportExportViewSet,
    ResourceLabelViewSet,
    ResourceReleaseStageViewSet,
    ResourceURLViewSet,
    ResourceViewSet,
    ResourceWithVerifiedUserRequiredViewSet,
)

urlpatterns = [
    path("", ResourceViewSet.as_view({"get": "list", "post": "create"}), name="apigateway.apps.resource"),
    path(
        "<int:id>/",
        ResourceViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="apigateway.apps.resource.detail",
    ),
    path(
        "<int:id>/labels/",
        ResourceLabelViewSet.as_view({"put": "update"}),
        name="apigateway.apps.resource.update.labels",
    ),
    path(
        "batch/",
        ResourceBatchViewSet.as_view({"put": "update", "delete": "destroy"}),
        name="apigateway.apps.resource.batch",
    ),
    path("<int:id>/urls/", ResourceURLViewSet.as_view({"get": "get"})),
    path("<int:id>/stages/", ResourceReleaseStageViewSet.as_view({"get": "get"})),
    path("proxy_paths/", ProxyPathViewSet.as_view({"get": "check"})),
    path(
        "import/check/",
        ResourceImportExportViewSet.as_view({"post": "import_resources_check"}),
        name="apigateway.apps.resource.import_check",
    ),
    path(
        "import/",
        ResourceImportExportViewSet.as_view({"post": "import_resources"}),
        name="apigateway.apps.resource.import",
    ),
    path(
        "export/",
        ResourceImportExportViewSet.as_view({"post": "export_resources"}),
        name="apigateway.apps.resource.export",
    ),
    path(
        "verified-user-required/",
        ResourceWithVerifiedUserRequiredViewSet.as_view({"get": "list"}),
        name="apigateway.apps.resource.with.verified_user_required",
    ),
]
