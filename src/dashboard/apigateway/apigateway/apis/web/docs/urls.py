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
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    # 所有网关 sdk
    path("sdks/", include("apigateway.apis.web.docs.gateway.sdk.urls")),
    # 网关
    path("gateways/", include("apigateway.apis.web.docs.gateway.gateway.urls")),
    path("gateways/<slug:gateway_name>/resources/", include("apigateway.apis.web.docs.gateway.resource.urls")),
    path("gateways/<slug:gateway_name>/stages/", include("apigateway.apis.web.docs.gateway.stage.urls")),
    path("gateways/<slug:gateway_name>/sdks/", include("apigateway.apis.web.docs.gateway.gateway_sdk.urls")),
]


# 非多租户模式才会有 esb 相关的接口
if not settings.ENABLE_MULTI_TENANT_MODE:
    urlpatterns += [
        # esb
        path("esb/boards/<slug:board>/systems/", include("apigateway.apis.web.docs.esb.system.urls")),
        path(
            "esb/boards/<slug:board>/systems/<slug:system_name>/components/",
            include("apigateway.apis.web.docs.esb.component.urls"),
        ),
        path("esb/boards/<slug:board>/sdks/", include("apigateway.apis.web.docs.esb.sdk.urls")),
    ]
