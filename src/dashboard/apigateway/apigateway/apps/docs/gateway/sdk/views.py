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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.docs.helper import support_helper
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import V1OKJsonResponse

from .helpers import DummyResourceForSDK, ReleasedResourceForSDK
from .serializers import GatewaySDKSLZ, SDKDocConditionSLZ, SDKQuerySLZ, SDKUsageExampleConditionSLZ, StageSDKSLZ


class SDKViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        query_serializer=SDKQuerySLZ,
        responses={status.HTTP_200_OK: GatewaySDKSLZ(many=True)},
        tags=["APIGateway.APISDK"],
    )
    def list(self, request, *args, **kwargs):
        """所有网关SDK"""
        slz = SDKQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = support_helper.get_latest_sdks(language=slz.validated_data["language"])
        slz = GatewaySDKSLZ(sorted(data or [], key=lambda x: x["api_name"]), many=True)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        query_serializer=SDKQuerySLZ,
        responses={status.HTTP_200_OK: StageSDKSLZ(many=True)},
        tags=["APIGateway.APISDK"],
    )
    def list_api_sdks(self, request, gateway_name: str, *args, **kwargs):
        """获取网关SDK列表"""
        slz = SDKQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        gateway = support_helper.get_gateway_by_name(gateway_name)
        if not gateway:
            raise error_codes.NOT_FOUND

        sdks = support_helper.get_stage_sdks(
            gateway["id"],
            language=slz.validated_data["language"],
        )
        slz = StageSDKSLZ(sorted(sdks or [], key=lambda x: x["stage_name"]), many=True)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        query_serializer=SDKUsageExampleConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["APIGateway.APISDK"],
    )
    def get_usage_example(self, request, gateway_name: str, stage_name: str, resource_name: str, *args, **kwargs):
        """获取网关SDK示例"""
        slz = SDKUsageExampleConditionSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        programming_language = slz.validated_data["language"]

        sdks = support_helper.get_latest_sdks(
            language=programming_language,
            gateway_name=gateway_name,
        )

        content = ""
        if sdks:
            sdk = sdks[0]
            resource = ReleasedResourceForSDK(
                api_id=sdk["api_id"],
                api_name=sdk["api_name"],
                stage_name=stage_name,
                resource_name=resource_name,
                sdk_created_time_str=sdk["sdk_created_time"],
            )
            content = render_to_string(
                f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_usage_example.md",
                context=resource.as_dict(),
            )

        return V1OKJsonResponse(
            "OK",
            data={
                "content": content,
            },
        )

    @swagger_auto_schema(
        query_serializer=SDKDocConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["APIGateway.APISDK"],
    )
    def get_doc(self, request, *args, **kwargs):
        """获取网关SDK说明文档"""
        slz = SDKDocConditionSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        programming_language = slz.validated_data["language"]

        return V1OKJsonResponse(
            "OK",
            data={
                "content": render_to_string(
                    f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_doc.md",
                    context=DummyResourceForSDK().as_dict(),
                ),
            },
        )
