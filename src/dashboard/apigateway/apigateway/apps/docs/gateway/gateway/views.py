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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.docs.helper import support_helper
from apigateway.common.error_codes import error_codes
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

from .serializers import GatewayQuerySLZ, GatewaySLZ


class GatewayViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=GatewayQuerySLZ,
        responses={status.HTTP_200_OK: GatewaySLZ(many=True)},
        tags=["Docs.APIGateway.Gateway"],
    )
    def list(self, request, *args, **kwargs):
        """获取网关列表"""
        slz = GatewayQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        gateways = support_helper.get_gateways(
            user_auth_type=data.get("user_auth_type"),
            query=data.get("query"),
            fuzzy=True,
        )
        paginator = LimitOffsetPaginator(count=len(gateways), offset=0, limit=len(gateways))
        slz = GatewaySLZ(
            sorted(gateways, key=lambda x: (x["api_type"], x["name"])),
            many=True,
        )

        return V1OKJsonResponse("OK", data=paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GatewaySLZ},
        tags=["Docs.APIGateway.Gateway"],
    )
    def retrieve(self, request, gateway_name: str, *args, **kwargs):
        """根据网关名称，获取网关详情"""
        gateway = support_helper.get_gateway_by_name(gateway_name)
        if not gateway:
            raise error_codes.NOT_FOUND

        slz = GatewaySLZ(gateway)
        return V1OKJsonResponse("OK", data=slz.data)
