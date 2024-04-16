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
    path("", views.GatewayListCreateApi.as_view(), name="gateways.list_create"),
    path(
        # 使用 gateway_id，复用 GatewayPermission 的权限校验
        "<int:gateway_id>/",
        include(
            [
                path("", views.GatewayRetrieveUpdateDestroyApi.as_view(), name="gateways.retrieve_update_destroy"),
                path("status/", views.GatewayUpdateStatusApi.as_view(), name="gateways.update_status"),
                path("feature-flags/", views.GatewayFeatureFlagsApi.as_view(), name="gateways.feature_flags.list"),
            ]
        ),
    ),
    path(
        "<int:gateway_id>/members/",
        include(
            [
                path("", views.GatewayRoleMembersApi.as_view(), name="gateway_members.list_create_update_destroy"),
            ]
        ),
    ),
    path("<int:gateway_id>/role/", views.GatewayRoleApi.as_view(), name="gateway_role.list"),
]
