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
from rest_framework import generics, status

from apigateway.apis.open.resource import serializers
from apigateway.apis.web.resource.serializers import ResourceImportInputSLZ
from apigateway.biz.resource.importer.importers import ResourcesImporter
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Resource
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

from .serializers import ResourceListOutputV1SLZ


class ResourceQuerySetMixin:
    def get_queryset(self):
        return Resource.objects.filter(api=self.request.gateway)


class ResourceListApi(ResourceQuerySetMixin, generics.ListAPIView):
    api_permission_exempt = True
    lookup_field = "id"

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: ResourceListOutputV1SLZ(many=True)},
        tags=["OpenAPI.Resource"],
    )
    def list(self, request, *args, **kwargs):
        resources = Resource.objects.filter(api_id=request.gateway.id)
        resource_count = resources.count()
        paginator = LimitOffsetPaginator(count=resource_count, offset=0, limit=resource_count)

        slz = ResourceListOutputV1SLZ(resources, many=True)
        return V1OKJsonResponse(data=paginator.get_paginated_data(slz.data))


class ResourceRetrieveApi(ResourceQuerySetMixin, generics.RetrieveAPIView):
    api_permission_exempt = True
    lookup_field = "id"

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ResourceListV1SLZ()},
        tags=["OpenAPI.Resource"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.ResourceListV1SLZ(instance)
        return V1OKJsonResponse(data=slz.data)


class ResourceSyncApi(ResourceQuerySetMixin, generics.CreateAPIView):
    permission_classes = [GatewayRelatedAppPermission]
    lookup_field = "id"

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        importer = ResourcesImporter.from_resources(
            gateway=request.gateway,
            resources=slz.validated_data["resources"],
            selected_resources=slz.validated_data.get("selected_resources"),
            need_delete_unspecified_resources=slz.validated_data.get("delete", False),
            username=request.user.username,
        )
        importer.import_resources()

        # 分析出已创建或更新的资源
        added_resources = []
        updated_resources = []
        for resource_data in importer.get_selected_resource_data_list():
            if resource_data.metadata.get("is_created"):
                added_resources.append({"id": resource_data.resource.id})
            else:
                updated_resources.append({"id": resource_data.resource.id})

        return V1OKJsonResponse(
            data={
                "added": added_resources,
                "updated": updated_resources,
                "deleted": importer.get_deleted_resources(),
            },
        )
