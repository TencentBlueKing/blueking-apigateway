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
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.open.released import serializers
from apigateway.apps.label.models import ResourceLabel
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Release, ReleasedResource
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import V1OKJsonResponse


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ReleasedResourceOutputSLZ()},
        tags=["OpenAPI.Resource"],
    ),
)
class ReleasedResourceRetrieveApi(generics.RetrieveAPIView):
    serializer_class = serializers.ReleasedResourceOutputSLZ
    lookup_field = "id"
    api_permission_exempt = True

    def get_queryset(self):
        return ReleasedResource.objects.filter(gateway=self.request.gateway)

    def get_object(self):
        if not self.request.gateway.is_active_and_public:
            raise Http404

        stage_name = self.kwargs["stage_name"]
        resource_name = self.kwargs["resource_name"]

        resource_version_id = Release.objects.get_released_resource_version_id(self.request.gateway.id, stage_name)
        if not resource_version_id:
            raise Http404

        resource = ReleasedResource.objects.get_released_resource(
            self.request.gateway.id, resource_version_id, resource_name
        )
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"]:
            raise Http404

        return resource

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return V1OKJsonResponse("OK", data=serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ReleasedResourceListV1OutputSLZ(many=True)},
        tags=["OpenAPI.Resource"],
    ),
)
class ReleasedResourceListApi(generics.ListAPIView):
    lookup_field = "id"
    api_permission_exempt = True

    def get_queryset(self):
        return ReleasedResource.objects.filter(gateway=self.request.gateway)

    def list(self, request, stage_name: Optional[str] = None, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resources = ResourceVersionHandler.get_released_public_resources(
            request.gateway.id,
            stage_name=stage_name,
        )
        resource_ids = [resource["id"] for resource in resources]
        paginator = LimitOffsetPaginator(count=len(resources), offset=0, limit=len(resources))

        slz = serializers.ReleasedResourceListV1OutputSLZ(
            resources,
            many=True,
            context={
                "resource_labels": ResourceLabel.objects.get_labels(resource_ids),
            },
        )
        return V1OKJsonResponse("OK", data=paginator.get_paginated_data(slz.data))


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ReleasedResourceListV1InputSLZ(many=True)},
        tags=["OpenAPI.Resource"],
    ),
)
class ReleasedResourceListByGatewayNameApi(generics.ListAPIView):
    lookup_field = "id"
    api_permission_exempt = True

    permission_classes = [GatewayRelatedAppPermission]

    def get_queryset(self):
        return ReleasedResource.objects.filter(gateway=self.request.gateway)

    def list(self, request, gateway_name, stage_name, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resources = ResourceVersionHandler.get_released_public_resources(request.gateway.id, stage_name=stage_name)
        paginator = LimitOffsetPaginator(count=len(resources), offset=0, limit=len(resources))

        slz = serializers.ReleasedResourceListV1InputSLZ(
            resources,
            many=True,
            context={
                "resource_url_tmpl": ResourceURLHandler.get_resource_url_tmpl(self.request.gateway.name, stage_name),
                "api_name": self.request.gateway.name,
                "stage_name": stage_name,
            },
        )
        return V1OKJsonResponse("OK", data=paginator.get_paginated_data(slz.data))
