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

from apigateway.apps.esb.bkcore.models import ESBChannel
from apigateway.biz.esb.decorators import check_board_exist
from apigateway.utils.responses import OKJsonResponse

from .serializers import ComponentOutputSLZ, ComponentSearchInputSLZ, ComponentSearchOutputSLZ

# 组件API模糊搜索时，结果数据限制大小
COMPONENT_SEARCH_LIMIT = 30


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description=f"查询组件 API，根据筛选条件模糊搜索，仅返回前 {COMPONENT_SEARCH_LIMIT} 条记录",
        query_serializer=ComponentSearchInputSLZ,
        responses={status.HTTP_200_OK: ComponentSearchOutputSLZ(many=True)},
        tags=["WebAPI.Docs.ESB.Component"],
    ),
)
class ComponentSearchApi(generics.ListAPIView):
    @check_board_exist
    def list(self, request, board: str, *args, **kwargs):
        """模糊搜索组件API"""
        slz = ComponentSearchInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = ESBChannel.objects.filter_public_components(
            board,
            keyword=slz.validated_data.get("keyword"),
            order_by=("system_id", "name"),
        )

        output_slz = ComponentSearchOutputSLZ(queryset[:COMPONENT_SEARCH_LIMIT], many=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="查询指定组件系统下的组件 API 列表，仅返回公开的组件",
        responses={status.HTTP_200_OK: ComponentOutputSLZ(many=True)},
        tags=["WebAPI.Docs.ESB.Component"],
    ),
)
class ComponentListApi(generics.ListAPIView):
    @check_board_exist
    def list(self, request, board: str, system_name: str, *args, **kwargs):
        """查询系统下组件API列表"""
        queryset = ESBChannel.objects.filter_public_components(board, system_name=system_name, order_by=("name",))
        slz = ComponentOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=slz.data)
