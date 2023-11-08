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
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.stage import serializers
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Release, Stage
from apigateway.utils.django import get_object_or_None
from apigateway.utils.responses import OKJsonResponse


class StageViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StageV1SLZ
    lookup_field = "id"
    api_permission_exempt = True

    def get_queryset(self):
        return Stage.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.StageV1SLZ(many=True)},
        tags=["OpenAPI.Stage"],
    )
    def list(self, request, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        queryset = self.get_queryset()
        queryset = queryset.filter(
            status=StageStatusEnum.ACTIVE.value,
            is_public=True,
        )

        slz = self.get_serializer(queryset, many=True)
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.StageV1SLZ(many=True)},
        tags=["OpenAPI.Stage"],
    )
    def list_by_gateway_name(self, request, gateway_name: str, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_permissions(self):
        if self.action == "list_by_gateway_name":
            permission_classes = [GatewayRelatedAppPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()


class StageV1ViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.StageWithResourceVersionV1SLZ(many=True)},
        tags=["OpenAPI.Stage"],
    )
    def list_stages_with_resource_version(self, request, gateway_name: str, *args, **kwargs):
        queryset = Stage.objects.filter(api=self.request.gateway)
        slz = serializers.StageWithResourceVersionV1SLZ(
            queryset, many=True, context={"stage_release": Release.objects.get_stage_release(gateway=request.gateway)}
        )
        return OKJsonResponse(data=slz.data)


class StageSyncViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=serializers.StageSyncInputSLZ, tags=["OpenAPI.Stage"])
    def sync(self, request, gateway_name: str, *args, **kwargs):
        instance = get_object_or_None(Stage, api=request.gateway, name=request.data.get("name", ""))
        slz = serializers.StageSyncInputSLZ(
            instance,
            data=request.data,
            context={
                "request": request,
                "allow_var_not_exist": True,
            },
        )
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse(
            "OK",
            data={
                "id": slz.instance.id,
                "name": slz.instance.name,
            },
        )
