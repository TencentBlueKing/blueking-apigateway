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
from django.template.loader import render_to_string
from django.utils.timezone import now as timezone_now
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.support.models import APISDK
from apigateway.biz.sdk.gateway_sdk import GatewaySdkHandler
from apigateway.biz.sdk.models import SdkDocContext
from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.utils.responses import OKJsonResponse

from .serializers import SdkListInputSLZ, SdkUsageExampleInputSLZ, StageSdkOutputSLZ


class SdkListApi(generics.ListAPIView):
    permission_classes = [GatewayDisplayablePermission]

    @swagger_auto_schema(
        query_serializer=SdkListInputSLZ,
        responses={status.HTTP_200_OK: StageSdkOutputSLZ(many=True)},
        tags=["Docs.Gateway.SDK"],
    )
    def list(self, request, gateway_name: str, *args, **kwargs):
        """获取网关SDK列表"""
        slz = SdkListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdks = GatewaySdkHandler.get_stage_sdks(
            gateway_id=request.gateway.id,
            language=slz.validated_data["language"],
        )
        slz = StageSdkOutputSLZ(sdks, many=True)
        return OKJsonResponse(data=slz.data)


class SdkUsageExampleApi(generics.RetrieveAPIView):
    permission_classes = [GatewayDisplayablePermission]

    @swagger_auto_schema(
        query_serializer=SdkUsageExampleInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Docs.Gateway.SDK"],
    )
    def retrieve(self, request, gateway_name: str, *args, **kwargs):
        """获取网关SDK示例"""
        slz = SdkUsageExampleInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        programming_language = slz.validated_data["language"]

        sdk = APISDK.objects.filter(
            gateway_id=request.gateway.id,
            is_recommended=True,
            language=programming_language,
        ).last()

        content = render_to_string(
            f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_usage_example.md",
            context=SdkDocContext(
                gateway_name=request.gateway.name,
                stage_name=slz.validated_data["stage_name"],
                resource_name=slz.validated_data["resource_name"],
                sdk_created_time=(sdk and sdk.created_time) or timezone_now(),
            ).as_dict(),
        )

        return OKJsonResponse(
            data={
                "content": content,
            },
        )
