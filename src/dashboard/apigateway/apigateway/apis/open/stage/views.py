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
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.stage import serializers
from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.stage.serializers import StageSLZ
from apigateway.biz.released_resource import ReleasedResourceDataHandler
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Stage
from apigateway.utils.django import get_object_or_None
from apigateway.utils.responses import V1OKJsonResponse


class StageViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.StageV1SLZ
    lookup_field = "id"
    api_permission_exempt = True

    def get_queryset(self):
        return Stage.objects.filter(gateway=self.request.gateway)

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
        return V1OKJsonResponse("OK", data=slz.data)

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
        queryset = Stage.objects.filter(gateway=self.request.gateway)
        slz = serializers.StageWithResourceVersionV1SLZ(
            queryset,
            many=True,
            context={"stage_release": ReleasedResourceDataHandler().get_stage_release(gateway=request.gateway)},
        )
        return V1OKJsonResponse(data=slz.data)


class StageSyncViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=StageSLZ, tags=["OpenAPI.Stage"])
    def sync(self, request, gateway_name: str, *args, **kwargs):
        instance = get_object_or_None(Stage, gateway=request.gateway, name=request.data.get("name", ""))
        slz = StageSLZ(
            instance,
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)

        stage = slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.STAGE.value,
            op_object_id=stage.id,
            op_object=stage.name,
            comment=_("创建环境"),
        )

        return V1OKJsonResponse(
            "OK",
            data={
                "id": slz.instance.id,
                "name": slz.instance.name,
            },
        )
