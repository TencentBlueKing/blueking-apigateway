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

from . import views

urlpatterns = [
    path("", views.GatewayListApi.as_view(), name="openapi.gateway.list"),
    path("<int:gateway_id>/", views.GatewayRetrieveApi.as_view(), name="openapi.gateway.retrieve"),
    path(
        "<slug:gateway_name>/",
        include(
            [
                path("sync/", views.GatewaySyncApi.as_view(), name="openapi.gateway.sync"),
                path("status/", views.GatewayUpdateStatusApi.as_view(), name="openapi.gateway.update_status"),
                path(
                    "public_key/", views.GatewayPublicKeyRetrieveApi.as_view(), name="openapi.gateway.get_public_key"
                ),
                path(
                    "related-apps/", views.GatewayRelatedAppAddApi.as_view(), name="openapi.gateway.add_related_apps"
                ),
            ]
        ),
    ),
]
