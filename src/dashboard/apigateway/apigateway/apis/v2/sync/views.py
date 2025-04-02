# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.v2.permissions import OpenAPIV2GatewayRelatedAppPermission
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.permission.constants import FormattedGrantDimensionEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppResourcePermission,
)
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway_related_app import GatewayRelatedAppHandler
from apigateway.core.models import Gateway, Resource
from apigateway.utils.responses import OKJsonResponse

from . import serializers

# 注意：请使用 OpenAPIV2GatewayRelatedAppPermission, 有特殊情况请在类注释中说明


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="添加网关关联的应用",
        request_body=serializers.GatewayRelatedAppsAddInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayRelatedAppAddApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayRelatedAppsAddInputSLZ

    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        input_app_codes = slz.validated_data["related_app_codes"]

        exist_related_app_codes = GatewayRelatedAppHandler.get_related_app_codes(request.gateway.id)
        missing_app_codes = set(input_app_codes) - set(exist_related_app_codes)
        for bk_app_code in missing_app_codes:
            GatewayRelatedAppHandler.add_related_app(request.gateway.id, bk_app_code)

        data_after = GatewayRelatedAppHandler.get_related_app_codes(request.gateway.id)

        # record audit log
        gateway = request.gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before={"related_app_codes": exist_related_app_codes},
            data_after={"related_app_codes": data_after},
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关权限列表",
        query_serializer=serializers.GatewayPermissionListInputSLZ,
        responses={status.HTTP_200_OK: serializers.GatewayPermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayPermissionListInputSLZ

    def _get_queryset(self, gateway: Gateway, bk_app_code: str, grant_dimension: str):
        if grant_dimension == FormattedGrantDimensionEnum.GATEWAY.value:
            gateway_permissions_queryset = AppGatewayPermission.objects.filter(gateway=gateway)

            if bk_app_code:
                gateway_permissions_queryset = gateway_permissions_queryset.filter(bk_app_code=bk_app_code)

            return gateway_permissions_queryset.order_by("-id")

        resource_ids = Resource.objects.filter(gateway=gateway).values_list("id", flat=True)
        resource_permissions_queryset = AppResourcePermission.objects.filter(
            gateway=gateway, resource_id__in=resource_ids
        ).exclude(bk_app_code=settings.DEFAULT_TEST_APP["bk_app_code"])

        if bk_app_code:
            resource_permissions_queryset = resource_permissions_queryset.filter(bk_app_code=bk_app_code)

        return resource_permissions_queryset.order_by("-id")

    def get(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        bk_app_code = slz.validated_data.get("bk_app_code")
        grant_dimension = slz.validated_data.get("grant_dimension")

        queryset = self._get_queryset(request.gateway, bk_app_code, grant_dimension)

        paginated_data = self.paginate_queryset(queryset)
        data = []
        resource_ids = []
        for perm in paginated_data:
            if grant_dimension == FormattedGrantDimensionEnum.GATEWAY.value:
                data.append(
                    {
                        "bk_app_code": perm.bk_app_code,
                        "expires": perm.expires,
                        "grant_dimension": FormattedGrantDimensionEnum.GATEWAY.value,
                        "id": perm.id,
                    }
                )
            else:
                resource_ids.append(perm.resource_id)
                data.append(
                    {
                        "bk_app_code": perm.bk_app_code,
                        # "grant_type": perm.grant_type,
                        "resource_id": perm.resource_id,
                        "expires": perm.expires,
                        "grant_dimension": FormattedGrantDimensionEnum.RESOURCE.value,
                        "id": perm.id,
                    }
                )
        if resource_ids:
            resources = Resource.objects.filter(id__in=resource_ids)
            resource_map = {resource.id: resource for resource in resources}
            for item in data:
                if item.get("resource_id") and resource_map.get(item["resource_id"]):
                    item["resource_name"] = resource_map.get(item["resource_id"]).name

        return self.get_paginated_response(data)
