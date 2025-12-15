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
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.GatewayListCreateApi.as_view(), name="gateways.list_create"),
    path("check-name-available/", views.GatewayCheckNameAvailableApi.as_view(), name="gateways.check_name_available"),
    path(
        # 使用 gateway_id，复用 GatewayPermission 的权限校验
        "<int:gateway_id>/",
        include(
            [
                path("", views.GatewayRetrieveUpdateDestroyApi.as_view(), name="gateways.retrieve_update_destroy"),
                path("status/", views.GatewayUpdateStatusApi.as_view(), name="gateways.update_status"),
                path("tenant-apps/", views.GatewayTenantAppListApi.as_view(), name="gateway.tenant.apps"),
                path("dev-guideline/", views.GatewayDevGuidelineRetrieveApi.as_view(), name="gateways.dev_guideline"),
                path(
                    "releasing-status/",
                    views.GatewayReleasingStatusApi.as_view(),
                    name="gateways.releasing_status",
                ),
            ]
        ),
    ),
]
