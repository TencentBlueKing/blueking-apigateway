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
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.biz.released_resource_doc import ReleasedResourceDocHandler
from apigateway.biz.released_resource_doc.generators import DocGenerator
from apigateway.biz.resource_doc import ResourceDocHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.utils.responses import OKJsonResponse

from .serializers import DocInputSLZ, DocOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关资源的文档",
        query_serializer=DocInputSLZ,
        responses={status.HTTP_200_OK: DocOutputSLZ},
        tags=["WebAPI.Docs.ResourceDoc"],
    ),
)
class DocRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [GatewayDisplayablePermission]

    def retrieve(self, request, gateway_name: str, resource_name: str, *args, **kwargs):
        """获取网关资源的文档"""
        slz = DocInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            gateway_id=request.gateway.id,
            stage_name=slz.validated_data["stage_name"],
            resource_name=resource_name,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )
        # 不公开的资源，对用户来说，就是一个不存在的资源
        if not (resource_data and resource_data.is_public):
            raise error_codes.NOT_FOUND

        generator = DocGenerator(
            gateway=request.gateway,
            stage_name=slz.validated_data["stage_name"],
            resource_data=resource_data,
            doc_data=doc_data,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )

        doc = generator.get_doc()
        output_slz = DocOutputSLZ(doc)
        return OKJsonResponse(data=output_slz.data)
