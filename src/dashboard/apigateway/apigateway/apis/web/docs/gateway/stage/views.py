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
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Stage
from apigateway.utils.responses import OKJsonResponse

from .serializers import StageOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关公开、可用的环境列表",
        responses={status.HTTP_200_OK: StageOutputSLZ(many=True)},
        tags=["WebAPI.Docs.Stage"],
    ),
)
class StageListApi(generics.ListAPIView):
    permission_classes = [GatewayDisplayablePermission]

    def list(self, request, gateway_name: str, *args, **kwargs):
        """获取网关公开、可用的环境列表"""
        stages = Stage.objects.filter(
            gateway=request.gateway,
            status=StageStatusEnum.ACTIVE.value,
            is_public=True,
        )
        slz = StageOutputSLZ(stages, many=True)
        return OKJsonResponse(data=slz.data)
