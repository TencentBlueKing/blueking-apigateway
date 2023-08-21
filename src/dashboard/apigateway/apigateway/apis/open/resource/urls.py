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

from apigateway.apis.open.released.views import ReleasedResourceViewSet
from apigateway.apis.open.resource import views

urlpatterns = [
    path(
        "apis/<int:gateway_id>/resources/",
        views.ResourceV1ViewSet.as_view({"get": "list"}),
        name="openapi.resources",
    ),
    path(
        "apis/<int:gateway_id>/resources/<int:id>/",
        views.ResourceV1ViewSet.as_view({"get": "retrieve"}),
        name="openapi.resources.detail",
    ),
    path(
        "apis/<slug:gateway_name>/resources/sync/",
        views.ResourceSyncV1ViewSet.as_view({"post": "sync"}),
        name="openapi.resources.sync",
    ),
    # TODO: 待API帮助中心更新后，需删除此接口
    path(
        "apis/<int:gateway_id>/resources/released/",
        ReleasedResourceViewSet.as_view({"get": "list"}),
        name="openapi.resources.list_released",
    ),
]
