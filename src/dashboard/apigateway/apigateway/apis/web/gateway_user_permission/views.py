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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.rbac.constants import GatewayActionEnum
from apigateway.utils.responses import OKJsonResponse

from .serializers import GatewayUserPermissionOutputSLZ


class GatewayUserPermissionRetrieveApi(generics.RetrieveAPIView):
    gateway_action = GatewayActionEnum.OPERATE_GATEWAY.value

    @swagger_auto_schema(
        operation_description="获取当前用户在该网关的角色",
        responses={status.HTTP_200_OK: GatewayUserPermissionOutputSLZ()},
        tags=["WebAPI.Gateway"],
    )
    def get(self, request, *args, **kwargs):
        slz = GatewayUserPermissionOutputSLZ(request.gateway_member)
        return OKJsonResponse(data=slz.data)
