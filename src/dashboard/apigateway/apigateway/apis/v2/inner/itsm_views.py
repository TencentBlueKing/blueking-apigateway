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
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.v2.permissions import OpenAPIV2Permission
from apigateway.biz.bk_itsm import ItsmCallbackResultHandler
from apigateway.common.error_codes import error_codes

from . import serializers

logger = logging.getLogger(__name__)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="ITSM 工单审批结果回调",
        request_body=serializers.ItsmCallbackInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class ItsmCallbackApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2Permission]

    def create(self, request, *args, **kwargs):
        slz = serializers.ItsmCallbackInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        self._validate_callback_request_context(request)

        ItsmCallbackResultHandler().handle(
            ticket=slz.validated_data["ticket"],
            callback_token=slz.validated_data["callback_token"],
        )

        return JsonResponse({"result": True, "message": "success"})

    @staticmethod
    def _validate_callback_request_context(request):
        app_code = request.app.app_code
        if app_code not in settings.BK_ITSM4_CALLBACK_ALLOWED_APP_CODES:
            logger.warning("ITSM callback app_code not allowed, app_code=%s", app_code)
            raise error_codes.INVALID_ARGUMENT.format("invalid callback source app")
