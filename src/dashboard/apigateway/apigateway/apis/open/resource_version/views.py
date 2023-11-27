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
from rest_framework import status, viewsets

from apigateway.apis.open.resource_version import serializers
from apigateway.apps.release.releasers import ReleaseBatchManager, ReleaseError
from apigateway.apps.resource_version.serializers import ResourceVersionSLZ
from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import ResourceVersion, Stage
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class ResourceVersionViewSet(viewsets.GenericViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=ResourceVersionSLZ, tags=["OpenAPI.ResourceVersion"])
    @transaction.atomic
    def create(self, request, gateway_name: str, *args, **kwargs):
        # manager = ResourceVersionManager()
        # instance = manager.create_resource_version(request.gateway, request.data, request.user.username)
        instance = ResourceVersionHandler().create_resource_version(
            request.gateway, request.data, request.user.username
        )

        # 创建文档版本
        if ResourceDoc.objects.doc_exists(request.gateway.id):
            ResourceDocVersion.objects.create(
                api=request.gateway,
                resource_version=instance,
                data=ResourceDocVersion.objects.make_version(request.gateway.id),
            )

        return OKJsonResponse(
            "OK",
            data={
                "id": instance.id,
                "version": instance.version,
                "name": instance.name,
                "title": instance.title,
            },
        )

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.ResourceVersion"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QueryResourceVersionV1SLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        versions = ResourceVersion.objects.filter_objects_fields(
            gateway_id=self.request.gateway.id,
            version=slz.validated_data.get("version"),
        )
        page = self.paginate_queryset(versions)
        slz = serializers.ListResourceVersionV1SLZ(page, many=True)
        return OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(tags=["OpenAPI.ResourceVersion"])
    @transaction.atomic
    def release(self, request, gateway_name: str, *args, **kwargs):
        slz = serializers.ReleaseV1SLZ(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        stage_ids = data["stage_ids"]
        resource_version = ResourceVersion.objects.get_object_fields(data["resource_version_id"])

        manager = ReleaseBatchManager(access_token=get_user_access_token_from_request(request))
        try:
            manager.release_batch(request.gateway, data, request.user.username)
        except ReleaseError as err:
            # 因设置了 transaction，views 中不能直接抛出异常，否则，将导致数据不会写入 db
            return FailJsonResponse(str(err))

        return OKJsonResponse(
            "OK",
            data={
                "version": resource_version["version"],
                "resource_version_name": resource_version["name"],
                "resource_version_title": resource_version["title"],
                "stage_names": list(Stage.objects.filter(id__in=stage_ids).values_list("name", flat=True)),
            },
        )

    @swagger_auto_schema(tags=["OpenAPI.ResourceVersion"])
    def latest(self, request, gateway_name: str, *args, **kwargs):
        resource_version = ResourceVersion.objects.get_latest_version(request.gateway.id)

        if not resource_version:
            return OKJsonResponse("OK", data={})

        return OKJsonResponse(
            "OK",
            data={
                "version": resource_version.version,
                "name": resource_version.name,
                "title": resource_version.title,
            },
        )
