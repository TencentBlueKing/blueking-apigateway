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
from typing import Optional

from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.released import serializers
from apigateway.apps.label.models import ResourceLabel
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Release, ReleasedResource
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class ReleasedResourceViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ReleasedResourceSLZ
    lookup_field = "id"
    api_permission_exempt = True

    def get_queryset(self):
        return ReleasedResource.objects.filter(api=self.request.gateway)

    def retrieve(self, request, gateway_id: int, stage_name: str, resource_name: str, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resource_version_id = Release.objects.get_released_resource_version_id(request.gateway.id, stage_name)
        if not resource_version_id:
            raise Http404

        resource = ReleasedResource.objects.get_released_resource(
            request.gateway.id, resource_version_id, resource_name
        )
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"]:
            raise Http404

        slz = serializers.ReleasedResourceSLZ(resource)
        return V1OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: serializers.ReleasedResourceListV1SLZ(many=True)},
        tags=["OpenAPI.Resource"],
    )
    def list(self, request, stage_name: Optional[str] = None, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resources = ResourceVersionHandler().get_released_public_resources(
            request.gateway.id,
            stage_name=stage_name,
        )
        resource_ids = [resource["id"] for resource in resources]
        paginator = LimitOffsetPaginator(count=len(resources), offset=0, limit=len(resources))

        slz = serializers.ReleasedResourceListV1SLZ(
            resources,
            many=True,
            context={
                "resource_labels": ResourceLabel.objects.get_labels(resource_ids),
            },
        )
        return V1OKJsonResponse("OK", data=paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: serializers.ListReleasedResourceV2SLZ(many=True)},
        tags=["OpenAPI.Resource"],
    )
    def list_by_gateway_name(self, request, gateway_name: str, stage_name: str, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resources = ResourceVersionHandler().get_released_public_resources(request.gateway.id, stage_name=stage_name)
        paginator = LimitOffsetPaginator(count=len(resources), offset=0, limit=len(resources))

        slz = serializers.ListReleasedResourceV2SLZ(
            resources,
            many=True,
            context={
                "resource_url_tmpl": ResourceURLHandler.get_resource_url_tmpl(self.request.gateway.name, stage_name),
                "api_name": self.request.gateway.name,
                "stage_name": stage_name,
            },
        )
        return V1OKJsonResponse("OK", data=paginator.get_paginated_data(slz.data))

    def get_permissions(self):
        if self.action == "list_by_gateway_name":
            permission_classes = [GatewayRelatedAppPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()
