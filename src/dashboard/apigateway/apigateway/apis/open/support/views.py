# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from apigateway.apis.open.permissions import (
    OpenAPIGatewayRelatedAppPermission,
)
from apigateway.apis.open.support import serializers
from apigateway.biz.sdk.helper import generate_sdks_for_resource_version
from apigateway.core.models import ResourceVersion
from apigateway.utils.responses import V1OKJsonResponse


class SDKGenerateViewSet(viewsets.ViewSet):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]

    @transaction.atomic
    @swagger_auto_schema(
        # todo: 是否需要将 support 改成 sdk？目前只有 sdk 相关的
        tags=["OpenAPI.V1"],
    )
    def generate(self, request, gateway_name: str, *args, **kwargs):
        """创建资源版本对应的 SDK"""

        slz = serializers.SDKGenerateV1SLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.data
        resource_version = get_object_or_404(
            ResourceVersion, gateway=request.gateway, version=data["resource_version"]
        )
        results = generate_sdks_for_resource_version(
            resource_version=resource_version,
            languages=data["languages"],
            version=data["version"],
        )

        return V1OKJsonResponse("OK", data=results)
