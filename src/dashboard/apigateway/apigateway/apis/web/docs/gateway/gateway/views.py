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
from typing import List

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, Release
from apigateway.utils.responses import OKJsonResponse

from .serializers import GatewayOutputSLZ


class GatewayListApi(generics.ListAPIView):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GatewayOutputSLZ(many=True)},
        tags=["WebAPI.Docs.Gateway"],
    )
    def list(self, request, *args, **kwargs):
        """获取网关列表"""
        gateways = self._get_displayable_gateways()
        gateway_ids = [gateway.id for gateway in gateways]
        slz = GatewayOutputSLZ(
            gateways,
            many=True,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids),
            },
        )

        return OKJsonResponse(data=sorted(slz.data, key=lambda x: (-x["is_official"], x["name"])))

    def _get_displayable_gateways(self) -> List[Gateway]:
        """
        查询可显示的网关
        - 网关公开
        - 网关启用中
        - 网关存在已发布的版本
        """
        released_gateway_ids = Release.objects.all().values_list("gateway_id", flat=True)

        return list(
            Gateway.objects.filter(
                status=GatewayStatusEnum.ACTIVE.value,
                is_public=True,
                id__in=released_gateway_ids,
            )
        )


class GatewayRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [GatewayDisplayablePermission]

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GatewayOutputSLZ},
        tags=["WebAPI.Docs.Gateway"],
    )
    def retrieve(self, request, gateway_name: str, *args, **kwargs):
        """根据网关名称，获取网关详情"""
        slz = GatewayOutputSLZ(
            request.gateway,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config([request.gateway.id]),
            },
        )
        return OKJsonResponse(data=slz.data)
