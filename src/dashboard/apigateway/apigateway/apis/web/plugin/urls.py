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

from apigateway.apis.web.plugin.binding.views import PluginBindingBatchViewSet, PluginBindingViewSet
from apigateway.apis.web.plugin.plugin.views import PluginConfigViewSet, PluginFormViewSet, PluginTypeViewSet

urlpatterns = [
    # plugin
    path("configs/", PluginConfigViewSet.as_view({"get": "list", "post": "create"}), name="plugins.config"),
    path(
        "configs/<int:id>/",
        PluginConfigViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="plugins.config.details",
    ),
    path("types/", PluginTypeViewSet.as_view({"get": "list"}), name="plugins.types"),
    path("forms/<int:type_id>/", PluginFormViewSet.as_view({"get": "retrieve"}), name="plugins.forms"),
    # plugin binding
    path(
        "configs/<int:config_id>/bindings/",
        PluginBindingBatchViewSet.as_view({"get": "list", "post": "bind", "delete": "unbind"}),
        name="plugins.config.bindings",
    ),
    path(
        "bindings/",
        PluginBindingViewSet.as_view({"get": "list"}),
        name="plugins.bindings",
    ),
    path(
        "bindings/<int:pk>/",
        PluginBindingViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="plugins.bindings.details",
    ),
]
