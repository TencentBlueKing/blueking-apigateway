# -*- coding: utf-8 -*-
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
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.biz.esb.decorators import check_board_exist
from apigateway.biz.esb.doc.generators import ComponentDocFactory
from apigateway.utils.responses import OKJsonResponse

from .serializers import ComponentDocOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取组件 API 文档，仅获取当前语言（中文/英文）的文档",
        responses={status.HTTP_200_OK: ComponentDocOutputSLZ},
        tags=["WebAPI.Docs.ESB.Component"],
    ),
)
class DocRetrieveApi(generics.RetrieveAPIView):
    @check_board_exist
    def retrieve(self, request, board: str, system_name: str, component_name: str, *args, **kwargs):
        """获取组件API文档"""
        factory = ComponentDocFactory(board, system_name, component_name)
        slz = ComponentDocOutputSLZ(factory.get_doc())
        return OKJsonResponse(data=slz.data)
