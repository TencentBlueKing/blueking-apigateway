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
from django.urls import path

from apigateway.apis.open.released import views

v1_open_api_patterns = [
    path(
        "apis/<slug:gateway_name>/released/stages/<slug:stage_name>/resources/",
        views.ReleasedResourceListByGatewayNameApi.as_view(),
        name="openapi.released.stage_resources_by_gateway_name",
    ),
    path(
        "apis/<slug:gateway_name>/released/stages/<slug:stage_name>/resources/<slug:resource_name>/",
        views.ReleasedResourceRetrieveApi.as_view(),
        name="openapi.released.resources.detail_by_gateway_name",
    ),
]

urlpatterns = v1_open_api_patterns
