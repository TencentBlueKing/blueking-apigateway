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

from .views import SDKViewSet

urlpatterns = [
    path("<slug:board>/sdks/latest/", SDKViewSet.as_view({"get": "retrieve"}), name="esb.sdks.latest"),
    path(
        "<slug:board>/systems/<slug:system_name>/components/<slug:component_name>/sdks/usage-example/",
        SDKViewSet.as_view({"get": "get_usage_example"}),
        name="esb.sdk.usage_example",
    ),
    path("sdks/", SDKViewSet.as_view({"get": "list"}), name="esb.sdks.list"),
    path("sdks/doc/", SDKViewSet.as_view({"get": "get_doc"}), name="esb.sdks.doc"),
]
