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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.support.models import APISDK
from apigateway.biz.sdk.models import DummySdkDocContext
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Release, ResourceVersion
from apigateway.utils.responses import OKJsonResponse

from .serializers import SdkDocInputSLZ, SdkDocOutputSLZ, SdkListInputSLZ, SdkListOutputSLZ


class SdkListApi(generics.ListAPIView):
    @swagger_auto_schema(
        query_serializer=SdkListInputSLZ,
        responses={status.HTTP_200_OK: SdkListOutputSLZ(many=True)},
        tags=["Docs.Gateway.SDK"],
    )
    def list(self, request, *args, **kwargs):
        """所有网关SDK"""
        slz = SdkListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdks = list(
            APISDK.objects.filter(
                gateway__is_public=True,
                gateway__status=GatewayStatusEnum.ACTIVE.value,
                is_recommended=True,
                language=slz.validated_data["language"],
            ).prefetch_related("gateway")
        )
        resource_version_ids = {sdk.resource_version_id for sdk in sdks}

        slz = SdkListOutputSLZ(
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
        return OKJsonResponse(data=slz.data)


class SdkDocApi(generics.RetrieveAPIView):
    @swagger_auto_schema(
        query_serializer=SdkDocInputSLZ,
        responses={status.HTTP_200_OK: SdkDocOutputSLZ},
        tags=["Docs.Gateway.SDK"],
    )
    def retrieve(self, request, *args, **kwargs):
        """获取网关SDK说明文档"""
        slz = SdkDocInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        programming_language = slz.validated_data["language"]

        output_slz = SdkDocOutputSLZ(
            {
                "content": render_to_string(
                    f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_doc.md",
                    context=DummySdkDocContext().as_dict(),
                ),
            }
        )

        return OKJsonResponse(data=output_slz.data)
