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

from .views import StageViewSet

urlpatterns = [
    path("", StageViewSet.as_view({"get": "list", "post": "create"}), name="apigateway.apps.stage"),
    path("releases/", StageViewSet.as_view({"post": "list_release"}), name="apigateway.apps.stage.releases"),
    path("basic/", StageViewSet.as_view({"get": "list_basic"}), name="apigateway.apps.stage.list_basic"),
    path(
        "<int:id>/",
        StageViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="apigateway.apps.stage.detail",
    ),
    path(
        "<int:id>/status/", StageViewSet.as_view({"put": "update_status"}), name="apigateway.apps.stage.update_status"
    ),
]
