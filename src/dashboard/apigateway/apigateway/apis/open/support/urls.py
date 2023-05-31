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

from . import views

urlpatterns = [
    # TODO: for api-support, should be removed after the frontend merge is completed
    path(
        "apis/<int:gateway_id>/support/resources/<int:resource_id>/doc/",
        views.ResourceDocViewSet.as_view({"get": "retrieve"}),
        name="openapi.support.resource_doc",
    ),
    path(
        "apis/<int:gateway_id>/support/stages/<slug:stage_name>/resources/<slug:resource_name>/doc/",
        views.ResourceDocViewSet.as_view({"get": "get_doc"}),
        name="openapi.support.resource_doc.stage",
    ),
    path(
        "apis/<int:gateway_id>/support/stages/sdks/",
        views.APISDKV1ViewSet.as_view({"get": "list_stage_sdks"}),
        name="openapi.support.sdk.stage",
    ),
    # for apigw-manager
    path(
        "apis/<slug:gateway_name>/resource-docs/import/by-archive/",
        views.ResourceDocImportViewSet.as_view({"post": "import_by_archive"}),
        name="openapi.support.resource_doc.import_by_archive",
    ),
    path(
        "apis/<slug:gateway_name>/resource-docs/import/by-swagger/",
        views.ResourceDocImportViewSet.as_view({"post": "import_by_swagger"}),
        name="openapi.support.resource_doc.import_by_swagger",
    ),
    path(
        "apis/<slug:gateway_name>/sdk/",
        views.SDKGenerateViewSet.as_view({"post": "generate"}),
        name="openapi.support.sdk.generate",
    ),
]
