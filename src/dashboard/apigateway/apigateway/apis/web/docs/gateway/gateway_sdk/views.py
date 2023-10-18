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
from django.utils.decorators import method_decorator
from django.utils.timezone import now as timezone_now
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.sdk.gateway_sdk import GatewaySDKHandler
from apigateway.biz.sdk.models import SDKDocContext
from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.utils.responses import OKJsonResponse

from .serializers import SDKListInputSLZ, SDKUsageExampleInputSLZ, SDKUsageExampleOutputSLZ, StageSDKOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关 SDK 列表",
        query_serializer=SDKListInputSLZ,
        responses={status.HTTP_200_OK: StageSDKOutputSLZ(many=True)},
        tags=["WebAPI.Docs.Gateway.SDK"],
    ),
)
class SDKListApi(generics.ListAPIView):
    permission_classes = [GatewayDisplayablePermission]

    def list(self, request, gateway_name: str, *args, **kwargs):
        """获取网关SDK列表"""
        slz = SDKListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdks = GatewaySDKHandler.get_stage_sdks(
            gateway_id=request.gateway.id,
            language=slz.validated_data["language"],
        )
        output_slz = StageSDKOutputSLZ(sdks, many=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关 SDK 调用示例",
        query_serializer=SDKUsageExampleInputSLZ,
        responses={status.HTTP_200_OK: SDKUsageExampleOutputSLZ},
        tags=["WebAPI.Docs.Gateway.SDK"],
    ),
)
class SDKUsageExampleApi(generics.RetrieveAPIView):
    permission_classes = [GatewayDisplayablePermission]

    def retrieve(self, request, gateway_name: str, *args, **kwargs):
        """获取网关SDK示例"""
        slz = SDKUsageExampleInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        programming_language = slz.validated_data["language"]

        sdk = GatewaySDK.objects.filter(
            gateway_id=request.gateway.id,
            is_recommended=True,
            language=programming_language,
        ).last()

        content = render_to_string(
            f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_usage_example.md",
            context=SDKDocContext(
                gateway_name=request.gateway.name,
                stage_name=slz.validated_data["stage_name"],
                resource_name=slz.validated_data["resource_name"],
                sdk_created_time=(sdk and sdk.created_time) or timezone_now(),
            ).as_dict(),
        )

        output_slz = SDKUsageExampleOutputSLZ({"content": content})
        return OKJsonResponse(data=output_slz.data)
