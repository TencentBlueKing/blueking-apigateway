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

from apigateway.apps.docs.esb.decorators import check_board_exist
from apigateway.utils.responses import V1OKJsonResponse

from .helpers import ComponentDocFactory
from .serializers import ComponentDocSLZ


class DocViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["Docs.ESB.Doc"],
    )
    @check_board_exist
    def retrieve(self, request, board: str, system_name: str, component_name: str, *args, **kwargs):
        """获取组件API文档"""
        factory = ComponentDocFactory(board, system_name, component_name)
        slz = ComponentDocSLZ(factory.get_doc())
        return V1OKJsonResponse("OK", data=slz.data)
