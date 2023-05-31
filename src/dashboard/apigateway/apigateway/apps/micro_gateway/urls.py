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

from .bcs.views import BcsViewSet
from .views import MicroGatewayViewSet

urlpatterns = [
    path("", MicroGatewayViewSet.as_view({"get": "list", "post": "create"}), name="apigateway.apps.micro_gateway"),
    path(
        "<slug:id>/",
        MicroGatewayViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="apigateway.apps.micro_gateway.detail",
    ),
    # bcs
    path(
        "bcs/projects/", BcsViewSet.as_view({"get": "get_projects"}), name="apigateway.apps.micro_gateway.bcs.projects"
    ),
    path(
        "bcs/clusters/", BcsViewSet.as_view({"get": "get_clusters"}), name="apigateway.apps.micro_gateway.bcs.clusters"
    ),
    path(
        "bcs/namespaces/",
        BcsViewSet.as_view({"get": "get_namespaces"}),
        name="apigateway.apps.micro_gateway.bcs.namespaces",
    ),
    path(
        "bcs/releases/", BcsViewSet.as_view({"get": "get_releases"}), name="apigateway.apps.micro_gateway.bcs.releases"
    ),
]
