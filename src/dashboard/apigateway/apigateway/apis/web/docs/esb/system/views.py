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

from apigateway.apps.esb.bkcore.models import ComponentSystem
from apigateway.biz.esb.decorators import check_board_exist
from apigateway.biz.esb.system_doc_category import SystemDocCategoryHandler
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import OKJsonResponse

from .serializers import SystemListOutputSLZ, SystemRetrieveOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: SystemListOutputSLZ(many=True)},
        tags=["WebAPI.Docs.ESB.System"],
    ),
)
class SystemListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        """获取系统列表"""
        system_categories = SystemDocCategoryHandler.get_system_doc_categories()
        slz = SystemListOutputSLZ(system_categories, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: SystemRetrieveOutputSLZ},
        tags=["WebAPI.Docs.ESB.System"],
    ),
)
class SystemRetrieveApi(generics.RetrieveAPIView):
    @check_board_exist
    def retrieve(self, request, board: str, system_name: str, *args, **kwargs):
        """获取系统信息"""
        system = ComponentSystem.objects.get_by_name(board, system_name)
        if not system:
            raise error_codes.NOT_FOUND

        slz = SystemRetrieveOutputSLZ(system)
        return OKJsonResponse(data=slz.data)
