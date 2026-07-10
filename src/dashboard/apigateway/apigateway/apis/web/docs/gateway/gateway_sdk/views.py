# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from apigateway.apis.web.docs.gateway.mixins import GatewayDocsPermissionMixin
from apigateway.apps.support.models import GatewaySDK
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.biz.sdk import GatewaySDKHandler, SDKDocContext, SDKFactory
from apigateway.common.django.translation import get_current_language_code
from apigateway.core.models import Release
from apigateway.service.resource_version import get_resource_schema
from apigateway.utils import openapi
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
class SDKListApi(GatewayDocsPermissionMixin, generics.ListAPIView):
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
class SDKUsageExampleApi(GatewayDocsPermissionMixin, generics.RetrieveAPIView):
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
        display_sdk = SDKFactory.create(sdk) if sdk else None

        stage_name = slz.validated_data["stage_name"]
        resource_name = slz.validated_data["resource_name"]
        resource_id = slz.validated_data.get("resource_id")

        resource_version_id = Release.objects.get_released_resource_version_id(request.gateway.id, stage_name)

        example = {}
        # 如果前端没有传resource_id,通过资源版本获取一下
        if not resource_id and resource_version_id:
            resource_id = ResourceVersionHandler.get_resource_id(resource_version_id, resource_name)
            # 获取对应资源的schema
            resource_schema = get_resource_schema(resource_version_id, resource_id)
            example = openapi.get_openapi_example(resource_schema)

        content = render_to_string(
            f"api_sdk/{get_current_language_code()}/{programming_language}_sdk_usage_example.md",
            context=SDKDocContext(
                gateway_name=request.gateway.name,
                stage_name=stage_name,
                resource_name=resource_name,
                sdk_created_time=(sdk and sdk.created_time) or timezone_now(),
                body_example=example.get("body_example", {}),
                path_params=example.get("path_params", {}),
                query_params=example.get("query_params", {}),
                headers=example.get("headers", {}),
                bk_api_url_tmpl=GatewayHandler.get_bk_api_url_tmpl(request.gateway.id),
                install_command=display_sdk.install_command if display_sdk else "",
                artifact_url=display_sdk.url if display_sdk else "",
                package_name=display_sdk.package_name if display_sdk else "",
            ).as_dict(),
        )

        output_slz = SDKUsageExampleOutputSLZ({"content": content})
        return OKJsonResponse(data=output_slz.data)
