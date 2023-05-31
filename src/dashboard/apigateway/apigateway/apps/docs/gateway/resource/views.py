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
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

from .serializers import ResourceSLZ


class ResourceViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: ResourceSLZ(many=True)},
        tags=["APIGateway.Resource"],
    )
    def list(self, request, gateway_name: str, stage_name: str, *args, **kwargs):
        """获取网关环境下的资源列表"""
        api = support_helper.get_gateway_by_name(gateway_name)
        if not api:
            raise error_codes.NOT_FOUND_ERROR

        data = support_helper.get_released_resources(api["id"], stage_name)
        slz = ResourceSLZ(sorted(data["results"], key=lambda x: x["name"]), many=True)
        data["results"] = slz.data
        return OKJsonResponse("OK", data=data)
