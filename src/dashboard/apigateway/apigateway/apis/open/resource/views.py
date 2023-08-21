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
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

from apigateway.apis.open.resource import serializers
from apigateway.apis.web.resource.importer import ResourcesImporter
from apigateway.apis.web.resource.views import ResourceViewSet
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Resource
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class ResourceV1ViewSet(ResourceViewSet):
    api_permission_exempt = True

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: serializers.ResourceListV1SLZ(many=True)},
        tags=["OpenAPI.Resource"],
    )
    def list(self, request, *args, **kwargs):
        resources = Resource.objects.filter(api_id=request.gateway.id)
        resource_count = resources.count()
        paginator = LimitOffsetPaginator(count=resource_count, offset=0, limit=resource_count)

        slz = serializers.ResourceListV1SLZ(resources, many=True)
        return V1OKJsonResponse("OK", data=paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ResourceListV1SLZ()},
        tags=["OpenAPI.Resource"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ResourceListV1SLZ(instance)
        return V1OKJsonResponse("OK", data=slz.data)


class ResourceSyncV1ViewSet(ResourceViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @transaction.atomic
    def sync(self, request, *args, **kwargs):
        slz = serializers.ResourceSyncSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 1. 获取导入的资源配置
        importer = ResourcesImporter(
            gateway=request.gateway,
            allow_overwrite=True,
            need_delete_unspecified_resources=data["delete"],
            username=request.user.username,
        )
        importer.load_importing_resources_by_swagger(content=data["content"])

        # 2. 导入资源
        importer.import_resources()

        # 3. 分析出已创建或更新的资源
        added_resources = []
        updated_resources = []
        for resource in importer.imported_resources:
            if resource.get("_is_created"):
                added_resources.append({"id": resource["id"]})
            elif resource.get("_is_updated"):
                updated_resources.append({"id": resource["id"]})

        return V1OKJsonResponse(
            "OK",
            data={
                "added": added_resources,
                "updated": updated_resources,
                "deleted": importer.get_deleted_resources(),
            },
        )
