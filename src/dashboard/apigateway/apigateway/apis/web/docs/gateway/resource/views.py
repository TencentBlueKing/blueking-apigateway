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

from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.resource_label import ResourceLabelHandler
from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.utils.responses import OKJsonResponse

from .serializers import ResourceListInputSLZ, ResourceOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关环境下已发布的资源列表",
        query_serializer=ResourceListInputSLZ,
        responses={status.HTTP_200_OK: ResourceOutputSLZ(many=True)},
        tags=["WebAPI.Docs.Resource"],
    ),
)
class ResourceListApi(generics.ListAPIView):
    permission_classes = [GatewayDisplayablePermission]

    def list(self, request, gateway_name: str, *args, **kwargs):
        """获取网关环境下已发布的资源列表"""
        slz = ResourceListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        resources = ReleasedResourceHandler.get_public_released_resource_data_list(
            request.gateway.id, slz.validated_data["stage_name"]
        )
        resource_ids = [resource.id for resource in resources]
        output_slz = ResourceOutputSLZ(
            resources,
            many=True,
            context={
                "labels": ResourceLabelHandler.get_labels(resource_ids),
            },
        )
        return OKJsonResponse(data=output_slz.data)
