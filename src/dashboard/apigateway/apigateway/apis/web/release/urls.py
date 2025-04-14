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
from django.urls import include, path

from .views import (
    DeployCreateApi,
    DeployRetrieveApi,
    ReleaseAvailableResourceListApi,
    ReleaseAvailableResourceSchemaRetrieveApi,
    ReleaseCreateApi,
    ReleaseHistoryListApi,
    ReleaseHistoryRetrieveApi,
    RelishHistoryEventsRetrieveAPI,
)

urlpatterns = [
    path("", ReleaseCreateApi.as_view(), name="gateway.release.create"),
    path(
        "deploy/",
        include(
            [
                path("", DeployCreateApi.as_view(), name="gateway.deploy.create"),
                path("<str:deploy_id>/", DeployRetrieveApi.as_view(), name="gateway.deploy.get"),
            ]
        ),
    ),
    path(
        "stages/<int:stage_id>/resources/",
        include(
            [
                path("", ReleaseAvailableResourceListApi.as_view(), name="gateway.releases.available_resources"),
                path(
                    "<int:resource_id>/schema/",
                    ReleaseAvailableResourceSchemaRetrieveApi.as_view(),
                    name="gateway.releases.available_resource.schema",
                ),
            ]
        ),
    ),
    path(
        "histories/",
        include(
            [
                path("", ReleaseHistoryListApi.as_view(), name="gateway.release_histories.list"),
                path("latest/", ReleaseHistoryRetrieveApi.as_view(), name="gateway.release_histories.retrieve_latest"),
                path(
                    "<int:history_id>/events/",
                    RelishHistoryEventsRetrieveAPI.as_view(),
                    name="gateway.release_histories.events",
                ),
            ]
        ),
    ),
]
