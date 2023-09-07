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
from django.conf import settings
from django.template.loader import render_to_string
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apps.docs.esb.decorators import check_board_exist
from apigateway.apps.docs.esb.sdk_helpers import DocTemplates, DummyComponentForSDK, NormalComponentForSDK, SDKFactory
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse

from .serializers import SDKSLZ, SDKDocConditionSLZ, SDKQuerySLZ, SDKUsageExampleConditionSLZ


class SDKViewSet(viewsets.GenericViewSet):
    @swagger_auto_schema(
        query_serializer=SDKQuerySLZ,
        responses={status.HTTP_200_OK: SDKSLZ(many=True)},
        tags=["Docs.ESB.SDK"],
    )
    def list(self, request, *args, **kwargs):
        """获取SDK列表"""
        slz = SDKQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdks = []

        for board in settings.ESB_BOARD_CONFIGS:
            sdk = SDKFactory.get_sdk(board, slz.validated_data["language"])
            if not sdk:
                continue
            sdks.append(sdk)

        # TODO: 不同语言SDK配置，可能需要不同的 serializer
        slz = SDKSLZ(sorted(sdks, key=lambda x: x.sdk_name), many=True)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        query_serializer=SDKQuerySLZ,
        responses={status.HTTP_200_OK: SDKSLZ},
        tags=["Docs.ESB.SDK"],
    )
    @check_board_exist
    def retrieve(self, request, board: str, *args, **kwargs):
        """获取SDK"""
        slz = SDKQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdk = SDKFactory.get_sdk(board, slz.validated_data["language"])
        if not sdk:
            return V1FailJsonResponse("SDK 获取失败，请稍后重试")

        slz = SDKSLZ(sdk)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        query_serializer=SDKUsageExampleConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Docs.ESB.SDK"],
    )
    @check_board_exist
    def get_usage_example(self, request, board: str, system_name: str, component_name: str, *args, **kwargs):
        """获取网关SDK示例"""
        slz = SDKUsageExampleConditionSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        component = NormalComponentForSDK(
            board,
            system_name,
            component_name,
        )
        doc_templates = DocTemplates(
            board,
            language_code=get_current_language_code(),
            programming_language=slz.validated_data["language"],
        )
        return V1OKJsonResponse(
            "OK",
            data={
                "content": render_to_string(
                    doc_templates.templates["sdk_usage_example"],
                    context=dict(component.as_dict(), doc_templates=doc_templates.templates),
                )
            },
        )

    @swagger_auto_schema(
        query_serializer=SDKDocConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Docs.ESB.SDK"],
    )
    def get_doc(self, request, *args, **kwargs):
        """获取ESB SDK说明文档"""
        slz = SDKDocConditionSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        component = DummyComponentForSDK()
        doc_templates = DocTemplates(
            component.board,
            language_code=get_current_language_code(),
            programming_language=slz.validated_data["language"],
        )

        return V1OKJsonResponse(
            "OK",
            data={
                "content": render_to_string(
                    doc_templates.templates["sdk_doc"],
                    context=dict(component.as_dict(), doc_templates=doc_templates.templates),
                )
            },
        )
