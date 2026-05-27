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
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, serializers, status

from apigateway.apis.open.permissions import (
    OpenAPIGatewayRelatedAppPermission,
)
from apigateway.biz.resource.importer.sync import sync_openapi_resources_from_content
from apigateway.core.models import Resource
from apigateway.utils.responses import V1OKJsonResponse

from .serializers import ResourceImportInputSLZ, ResourceSyncOutputSLZ


class ResourceSyncApi(generics.CreateAPIView):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]

    def get_queryset(self):
        return Resource.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        request_body=ResourceImportInputSLZ,
        responses={status.HTTP_200_OK: ResourceSyncOutputSLZ()},
        tags=["OpenAPI.V1"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
            },
        )
        slz.is_valid(raise_exception=True)

        result = sync_openapi_resources_from_content(
            gateway=request.gateway,
            username=request.user.username,
            content=slz.validated_data["content"],
            delete_missing_resources=slz.validated_data["delete"],
            doc_language=slz.validated_data.get("doc_language", ""),
        )
        if not result.ok:
            raise serializers.ValidationError({"content": _("{err}").format(err=result.message)})

        slz = ResourceSyncOutputSLZ(
            {
                "added": result.added,
                "updated": result.updated,
                "deleted": result.deleted,
            }
        )

        return V1OKJsonResponse(data=slz.data)
