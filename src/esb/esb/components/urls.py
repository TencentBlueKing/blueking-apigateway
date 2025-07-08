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

from django.conf.urls import url

from esb import routers

urlpatterns = [
    url(r"^compapi/(.*?)$", routers.api_router_view, name="component.api"),
    url(r"^self-service-api/(.*?)$", routers.buffet_component_view, name="component.buffet"),
]


# 处理404和500请求
handler404 = "esb.views.handler_404_view"
handler500 = "esb.views.handler_500_view"
