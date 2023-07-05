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
from typing import List

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apigateway.apis.iam.authentication import IAMBasicAuthentication
from apigateway.apis.iam.providers import IAMResourceProviderFactory
from apigateway.apis.iam.serializers import QueryIAMResourceSLZ
from apigateway.iam.constants import ResourceTypeEnum


class IAMResourceAPIView(APIView):
    """统一入口: 提供给权限中心拉取各类资源"""

    authentication_classes = (IAMBasicAuthentication,)
    permission_classes: List = []

    def _get_options(self, request):
        request.LANGUAGE_CODE = request.META.get("HTTP_BLUEKING_LANGUAGE", settings.LANGUAGE_CODE)
        return {"language": request.LANGUAGE_CODE}

    def post(self, request, *args, **kwargs):
        slz = QueryIAMResourceSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        validated_data = slz.validated_data
        provider = IAMResourceProviderFactory(resource_type=ResourceTypeEnum(validated_data["type"]))
        resp_data = provider.provide(
            method=validated_data["method"],
            data=validated_data,
            **self._get_options(request),
        )
        return Response({"code": 0, "message": "OK", "data": resp_data})
