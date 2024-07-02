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

from apigateway.apps.esb.component.views import (
    ComponentReleaseHistoryStatusViewSet,
    ComponentReleaseHistoryViewSet,
    ComponentSyncViewSet,
    ESBChannelBatchViewSet,
    ESBChannelViewSet,
)

urlpatterns = [
    path("", ESBChannelViewSet.as_view({"get": "list", "post": "create"}), name="apigateway.apps.esb.components"),
    path(
        "<int:id>/",
        ESBChannelViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="apigateway.apps.esb.components.detail",
    ),
    path("batch/", ESBChannelBatchViewSet.as_view({"delete": "destroy"}), name="apigateway.apps.esb.components.batch"),
    path(
        "gateway/",
        ComponentSyncViewSet.as_view({"get": "retrieve_esb_gateway"}),
        name="apigateway.apps.esb.components.gateway",
    ),
    path(
        "sync/need-new-release/",
        ComponentSyncViewSet.as_view({"get": "need_new_release"}),
        name="apigateway.apps.esb.components.need_new_release",
    ),
    path(
        "sync/check/",
        ComponentSyncViewSet.as_view({"post": "sync_check"}),
        name="apigateway.apps.esb.components.sync_check",
    ),
    path(
        "sync/release/status/",
        ComponentSyncViewSet.as_view({"get": "get_release_status"}),
        name="apigateway.apps.esb.components.get_release_status",
    ),
    path(
        "sync/release/",
        ComponentSyncViewSet.as_view({"post": "sync_and_release"}),
        name="apigateway.apps.esb.components.sync_and_release",
    ),
    path(
        "sync/release/histories/",
        ComponentReleaseHistoryViewSet.as_view({"get": "list"}),
        name="apigateway.apps.esb.components.release.histories",
    ),
    path(
        "sync/release/histories/<int:id>/",
        ComponentReleaseHistoryViewSet.as_view({"get": "retrieve"}),
        name="apigateway.apps.esb.components.release.history",
    ),
    path(
        "sync/release/histories/status/<int:id>/",
        ComponentReleaseHistoryStatusViewSet.as_view({"get": "retrieve"}),
        name="apigateway.apps.esb.components.release.histories.status",
    ),
]
