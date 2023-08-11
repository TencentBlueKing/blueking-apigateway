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

from apigateway.apps.docs.esb.constants import COMPONENT_SEARCH_LIMIT
from apigateway.apps.docs.esb.decorators import check_board_exist
from apigateway.apps.esb.bkcore.models import ESBChannel
from apigateway.utils.responses import V1OKJsonResponse

from .serializers import ComponentSearchResultSLZ, ComponentSearchSLZ, ComponentSLZ


class ComponentViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        query_serializer=ComponentSearchSLZ,
        responses={status.HTTP_200_OK: ComponentSearchResultSLZ(many=True)},
        tags=["ESB.Component"],
    )
    @check_board_exist
    def search(self, request, board: str, *args, **kwargs):
        """模糊搜索组件API"""
        slz = ComponentSearchSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        qs = ESBChannel.objects.filter_public_components(
            board,
            query=slz.validated_data.get("query"),
            order_by=("system_id", "name"),
        )

        slz = ComponentSearchResultSLZ(qs[:COMPONENT_SEARCH_LIMIT], many=True)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ComponentSLZ(many=True)},
        tags=["ESB.Component"],
    )
    @check_board_exist
    def list(self, request, board: str, system_name: str, *args, **kwargs):
        """查询系统下组件API列表"""
        qs = ESBChannel.objects.filter_public_components(board, system_name=system_name, order_by=("name",))
        slz = ComponentSLZ(qs, many=True)
        return V1OKJsonResponse("OK", data=slz.data)
