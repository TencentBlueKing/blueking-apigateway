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
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.biz.esb.decorators import check_board_exist
from apigateway.biz.esb.sdk.models import DocTemplates, DummySDKDocContext, SDKDocContext
from apigateway.biz.esb.sdk.sdk_factory import SDKFactory
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    SDKDocInputSLZ,
    SDKDocOutputSLZ,
    SDKListInputSLZ,
    SDKOutputSLZ,
    SDKRetrieveInputSLZ,
    SDKUsageExampleInputSLZ,
    SDKUsageExampleOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取所有的组件 SDK 列表，单个 SDK 仅返回最新版本 SDK 信息",
        query_serializer=SDKListInputSLZ,
        responses={status.HTTP_200_OK: SDKOutputSLZ(many=True)},
        tags=["WebAPI.Docs.ESB.SDK"],
    ),
)
class SDKListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        """获取SDK列表"""
        slz = SDKListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdks = []

        for board in settings.ESB_BOARD_CONFIGS:
            sdk = SDKFactory.get_sdk(board, slz.validated_data["language"])
            if not sdk:
                continue
            sdks.append(sdk)

        output_slz = SDKOutputSLZ(sorted(sdks, key=lambda x: x.sdk_name), many=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定语言（python） 组件 SDK 的信息",
        query_serializer=SDKRetrieveInputSLZ,
        responses={status.HTTP_200_OK: SDKOutputSLZ},
        tags=["WebAPI.Docs.ESB.SDK"],
    ),
)
class SDKRetrieveApi(generics.RetrieveAPIView):
    @check_board_exist
    def retrieve(self, request, board, *args, **kwargs):
        """获取SDK"""
        slz = SDKRetrieveInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        sdk = SDKFactory.get_sdk(board, slz.validated_data["language"])
        if not sdk:
            raise error_codes.NOT_FOUND

        output_slz = SDKOutputSLZ(sdk)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定组件的指定语言（python） SDK 的调用示例",
        query_serializer=SDKUsageExampleInputSLZ,
        responses={status.HTTP_200_OK: SDKUsageExampleOutputSLZ},
        tags=["WebAPI.Docs.ESB.SDK"],
    ),
)
class SDKUsageExampleApi(generics.RetrieveAPIView):
    @check_board_exist
    def retrieve(self, request, board, *args, **kwargs):
        """获取网关SDK示例"""
        slz = SDKUsageExampleInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        doc_context = SDKDocContext(
            board,
            slz.validated_data["system_name"],
            slz.validated_data["component_name"],
        )
        doc_templates = DocTemplates(
            board,
            language_code=get_current_language_code(),
            programming_language=slz.validated_data["language"],
        )
        output_slz = SDKUsageExampleOutputSLZ(
            {
                "content": render_to_string(
                    doc_templates.templates["sdk_usage_example"],
                    context=dict(doc_context.as_dict(), doc_templates=doc_templates.templates),
                )
            }
        )
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定语言（python）组件 SDK 的调用样例",
        query_serializer=SDKDocInputSLZ,
        responses={status.HTTP_200_OK: SDKDocOutputSLZ},
        tags=["WebAPI.Docs.ESB.SDK"],
    ),
)
class SDKDocRetrieveApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        """获取ESB SDK说明文档"""
        slz = SDKDocInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        doc_context = DummySDKDocContext()
        doc_templates = DocTemplates(
            doc_context.board,
            language_code=get_current_language_code(),
            programming_language=slz.validated_data["language"],
        )

        output_slz = SDKDocOutputSLZ(
            {
                "content": render_to_string(
                    doc_templates.templates["sdk_doc"],
                    context=dict(doc_context.as_dict(), doc_templates=doc_templates.templates),
                )
            }
        )

        return OKJsonResponse(data=output_slz.data)
