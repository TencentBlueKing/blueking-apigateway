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
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.sdk.models import DummySDKDocContext
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Release, ResourceVersion
from apigateway.utils.responses import OKJsonResponse

from .serializers import SDKDocInputSLZ, SDKDocOutputSLZ, SDKListInputSLZ, SDKListOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=SDKListInputSLZ,
        responses={status.HTTP_200_OK: SDKListOutputSLZ(many=True)},
        tags=["WebAPI.Docs.Gateway.SDK"],
    ),
)
class SDKListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        """所有网关SDK"""
        slz = SDKListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdks = list(
            GatewaySDK.objects.filter(
                gateway__is_public=True,
                gateway__status=GatewayStatusEnum.ACTIVE.value,
                is_recommended=True,
                language=slz.validated_data["language"],
            ).prefetch_related("gateway")
        )
        resource_version_ids = {sdk.resource_version_id for sdk in sdks}

        output_slz = SDKListOutputSLZ(
            sdks,
            many=True,
            context={
                "released_stages": Release.objects.get_released_stages(resource_version_ids=resource_version_ids),
                "resource_versions": {
                    version["id"]: version
                    for version in ResourceVersion.objects.filter(id__in=resource_version_ids).values(
                        "id", "version", "title", "name"
                    )
                },
            },
        )
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=SDKDocInputSLZ,
        responses={status.HTTP_200_OK: SDKDocOutputSLZ},
        tags=["WebAPI.Docs.Gateway.SDK"],
    ),
)
class SDKDocApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        """获取网关SDK说明文档"""
        slz = SDKDocInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        programming_language = slz.validated_data["language"]

        output_slz = SDKDocOutputSLZ(
            {
                "content": render_to_string(
                    f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_doc.md",
                    context=DummySDKDocContext().as_dict(),
                ),
            }
        )

        return OKJsonResponse(data=output_slz.data)
