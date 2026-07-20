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
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.open.permissions import (
    OpenAPIGatewayRelatedAppPermission,
)
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.resource_version import ResourceVersionArtifactHandler
from apigateway.core.models import ResourceVersion, Stage
from apigateway.utils.responses import V1FailJsonResponse, V1OKJsonResponse

from .serializers import (
    ReleaseV1InputSLZ,
    ResourceVersionCreateV1InputSLZ,
    ResourceVersionListV1OutputSLZ,
    ResourceVersionQueryV1InputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.V1"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=ResourceVersionCreateV1InputSLZ,
        tags=["OpenAPI.V1"],
    ),
)
class ResourceVersionListCreateApi(generics.ListCreateAPIView):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]
    serializer_class = ResourceVersionCreateV1InputSLZ

    def list(self, request, *args, **kwargs):
        slz = ResourceVersionQueryV1InputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        versions = ResourceVersion.objects.filter_objects_fields(
            gateway_id=self.request.gateway.id,
            version=slz.validated_data.get("version"),
        )
        page = self.paginate_queryset(versions)
        slz = ResourceVersionListV1OutputSLZ(page, many=True)
        return V1OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @transaction.atomic
    def create(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)
        data = slz.validated_data
        instance = ResourceVersionArtifactHandler.create_resource_version_with_artifacts(
            gateway=request.gateway,
            data=data,
            username=request.user.username,
        )

        return V1OKJsonResponse(
            "OK",
            data={
                "id": instance.id,
                "version": instance.version,
            },
        )


class ResourceVersionReleaseApi(generics.CreateAPIView):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]
    serializer_class = ReleaseV1InputSLZ

    @swagger_auto_schema(tags=["OpenAPI.V1"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        stage_ids = data["stage_ids"]
        resource_version = ResourceVersion.objects.get_object_fields(data["resource_version_id"])

        ok, message = ReleaseHandler.release_to_stages(
            gateway=request.gateway,
            resource_version_id=data["resource_version_id"],
            stage_ids=stage_ids,
            username=request.user.username,
            comment=data["comment"],
        )
        if not ok:
            return V1FailJsonResponse(message)

        return V1OKJsonResponse(
            "OK",
            data={
                "version": resource_version["version"],
                "resource_version_title": "",
                "stage_names": list(Stage.objects.filter(id__in=stage_ids).values_list("name", flat=True)),
            },
        )


class ResourceVersionGetLatestApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["OpenAPI.V1"])
    def get(self, request, gateway_name: str, *args, **kwargs):
        resource_version = ResourceVersion.objects.get_latest_version(request.gateway.id)

        if not resource_version:
            return V1OKJsonResponse("OK", data={})

        return V1OKJsonResponse(
            "OK",
            data={
                "version": resource_version.version,
                "name": "-",
                "title": "-",
            },
        )
