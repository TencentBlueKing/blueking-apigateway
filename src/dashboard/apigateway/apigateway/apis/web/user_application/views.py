#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.components.bkpaas import get_paas_apps_by_username
from apigateway.utils.responses import OKJsonResponse

from .serializers import UserApplicationOutputSLZ


@method_decorator(
    name="get",
    decorator=extend_schema(
        description="获取当前用户可管理的蓝鲸应用列表",
        responses={status.HTTP_200_OK: UserApplicationOutputSLZ(many=True)},
        tags=["WebAPI.Me"],
    ),
)
class UserApplicationListApi(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserApplicationOutputSLZ

    def list(self, request, *args, **kwargs):
        apps = get_paas_apps_by_username(request.user.username, get_user_tenant_id(request))
        output_data = [
            {
                "bk_app_code": app.get("code", ""),
                "name": app.get("name", ""),
                "logo_url": app.get("logo_url", ""),
            }
            for app in apps
        ]

        output_slz = self.get_serializer(output_data, many=True)
        return OKJsonResponse(data=output_slz.data)
