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
    path("", views.StageListCreateApi.as_view(), name="stage.list-create"),
    path(
        "<int:id>/",
        views.StageRetrieveUpdateDestroyApi.as_view(),
        name="stage.retrieve-update-destroy",
    ),
    path(
        "<int:id>/programmable/",
        views.ProgrammableStageDeployRetrieveApi.as_view(),
        name="stage.programmable.retrieve-update-destroy",
    ),
    path(
        "<int:id>/vars/",
        views.StageVarsRetrieveUpdateApi.as_view(),
        name="stage.vars-retrieve-update",
    ),
    path(
        "<int:id>/backends/",
        views.StageBackendListApi.as_view(),
        name="stage.backend-list",
    ),
    path(
        "<int:id>/backends/<int:backend_id>/",
        views.StageBackendRetrieveUpdateApi.as_view(),
        name="stage.backend-retrieve-update",
    ),
    path(
        "<int:id>/status/",
        views.StageStatusUpdateApi.as_view(),
        name="stage.status-update",
    ),
]
