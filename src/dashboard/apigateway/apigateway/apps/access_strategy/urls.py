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

from apigateway.apps.access_strategy.access_strategy.views import AccessStrategyViewSet
from apigateway.apps.access_strategy.binding.views import AccessStrategyBindingBatchViewSet
from apigateway.apps.access_strategy.ip_group.views import IPGroupViewSet

urlpatterns = [
    # access_strategy
    path("", AccessStrategyViewSet.as_view({"get": "list", "post": "create"}), name="access_strategies"),
    path(
        "<int:id>/",
        AccessStrategyViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="access_strategies.detail",
    ),
    # access_strategy binding
    path(
        "<int:access_strategy_id>/bindings/",
        AccessStrategyBindingBatchViewSet.as_view({"get": "list", "post": "bind", "delete": "unbind"}),
        name="access_strategies.bindings",
    ),
    path(
        "<int:access_strategy_id>/bindings/diff/",
        AccessStrategyBindingBatchViewSet.as_view({"post": "diff"}),
        name="access_strategies.bindings.diff",
    ),
    # ip_group
    path("ip_groups/", IPGroupViewSet.as_view({"get": "list", "post": "create"}), name="access_strategy.ip_groups"),
    path(
        "ip_groups/<int:id>/",
        IPGroupViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="access_strategy.ip_groups.detail",
    ),
]
