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

from apigateway.apis.web.resource.views import (
    BackendPathCheckApi,
    ResourceBatchUpdateDestroyApi,
    ResourceExportApi,
    ResourceImportApi,
    ResourceImportCheckApi,
    ResourceLabelUpdateApi,
    ResourceListCreateApi,
    ResourceRetrieveUpdateDestroyApi,
    ResourcesWithVerifiedUserRequiredApi,
)

urlpatterns = [
    path("", ResourceListCreateApi.as_view(), name="resource.list_create"),
    path("<int:id>/", ResourceRetrieveUpdateDestroyApi.as_view(), name="resource.retrieve_update_destroy"),
    path("batch/", ResourceBatchUpdateDestroyApi.as_view(), name="resource.batch_update_destroy"),
    path(
        "<int:resource_id>/",
        include(
            [
                path("labels/", ResourceLabelUpdateApi.as_view(), name="resource.label.update"),
                path("docs/", include("apigateway.apis.web.resource.doc.urls")),
            ]
        ),
    ),
    path(
        "import/",
        include(
            [
                path("check/", ResourceImportCheckApi.as_view(), name="resource.import.check"),
                path("", ResourceImportApi.as_view(), name="resource.import"),
            ]
        ),
    ),
    path("export/", ResourceExportApi.as_view(), name="resource.export"),
    # 资源后端路径校验
    path("backend-path/check/", BackendPathCheckApi.as_view(), name="resource.backend_path.check"),
    # 用于 ”免用户认证应用白名单“ 插件过滤资源
    path(
        "with/verified-user-required/",
        ResourcesWithVerifiedUserRequiredApi.as_view(),
        name="resource.list_with_verified_user_required",
    ),
]
