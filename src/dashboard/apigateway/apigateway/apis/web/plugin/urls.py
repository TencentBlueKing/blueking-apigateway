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

from .views import (
    PluginBindingListApi,
    PluginConfigCreateApi,
    PluginConfigRetrieveUpdateDestroyApi,
    PluginFormRetrieveApi,
    PluginTypeListApi,
    ScopePluginConfigListApi,
)

urlpatterns = [
    # plugins
    # list plugin types (global)
    path("", PluginTypeListApi.as_view(), name="plugins.types"),
    # list plugin configs (by stage or resource)
    path("<str:scope_type>/<int:scope_id>/", ScopePluginConfigListApi.as_view(), name="plugins.config.scope"),
    # create a binding (by stage or resource)
    path(
        "<str:scope_type>/<int:scope_id>/<str:code>/configs/",
        PluginConfigCreateApi.as_view(),
        name="plugins.config.create",
    ),
    # get, update or delete a plugin config (delete equals delete bindings)
    path(
        "<str:scope_type>/<int:scope_id>/<str:code>/configs/<int:id>/",
        PluginConfigRetrieveUpdateDestroyApi.as_view(),
        name="plugins.config.details",
    ),
    path("<str:code>/form/", PluginFormRetrieveApi.as_view(), name="plugins.form"),
    path("<str:code>/bindings/", PluginBindingListApi.as_view(), name="plugins.bindings"),
]
