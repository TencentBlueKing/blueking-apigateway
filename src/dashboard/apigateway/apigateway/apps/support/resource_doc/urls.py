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

from apigateway.apps.support.resource_doc import views

urlpatterns = [
    # Deprecated 接口，待前端升级后删除
    path(
        "resources/<int:resource_id>/doc/",
        views.DeprecatedResourceDocViewSet.as_view({"get": "retrieve", "post": "update"}),
        name="support.resource_doc.legacy",
    ),
    # 新版接口
    path(
        "resources/<int:resource_id>/docs/",
        views.ResourceDocViewSet.as_view({"get": "list", "post": "create"}),
        name="support.resource_doc",
    ),
    path(
        "resources/<int:resource_id>/docs/<int:id>/",
        views.ResourceDocViewSet.as_view({"put": "update", "delete": "destroy"}),
        name="support.resource_doc.detail",
    ),
    path("resources/docs/archive/parse/", views.ArchiveDocParseViewSet.as_view({"post": "parse"})),
    path(
        "resources/docs/import/by-archive/",
        views.ResourceDocImportExportViewSet.as_view({"post": "import_by_archive"}),
        name="support.resource_doc.import_by_archive",
    ),
    path(
        "resources/docs/import/by-swagger/",
        views.ResourceDocImportExportViewSet.as_view({"post": "import_by_swagger"}),
        name="support.resource_doc.import_by_swagger",
    ),
    path(
        "resources/docs/export/",
        views.ResourceDocImportExportViewSet.as_view({"post": "export"}),
        name="support.resource_doc.export",
    ),
]
