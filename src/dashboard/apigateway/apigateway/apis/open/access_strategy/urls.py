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
    path(
        "apis/<int:gateway_id>/access_strategies/ip-groups/",
        views.IPGroupV1ViewSet.as_view({"post": "post"}),
        name="openapi.access-strategies.ip-groups",
    ),
    path(
        "apis/<int:gateway_id>/access_strategies/add-ip-groups-to-strategies/",
        views.AccessStrategyAddIPGroupsV1APIView.as_view(),
        name="openapi.access-strategies.add-ip-groups-to-strategies",
    ),
    path(
        "apis/<int:gateway_id>/access_strategies/<int:access_strategy_id>/bindings/",
        views.AccessStrategyBindingsV1ViewSet.as_view({"post": "bind"}),
        name="openapi.access-strategies.bind-access-strategies",
    ),
    path(
        "apis/<slug:gateway_name>/access_strategies/sync/",
        views.AccessStrategySyncViewSet.as_view({"post": "sync"}),
        name="openapi.access-strategies.sync",
    ),
]
