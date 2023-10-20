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
import operator
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from drf_yasg.utils import swagger_auto_schema
from pydantic import parse_obj_as
from rest_framework import generics, status

from apigateway.apis.open.gateway import serializers
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway.synchronizer import GatewaySyncData, GatewaySynchronizer
from apigateway.biz.gateway_related_app import GatewayRelatedAppHandler
from apigateway.biz.release import ReleaseHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import JWT, Gateway, GatewayRelatedApp
from apigateway.utils.responses import V1OKJsonResponse


class GatewayListApi(generics.ListAPIView):
    serializer_class = serializers.GatewayListV1OutputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    @swagger_auto_schema(
        query_serializer=serializers.GatewayListV1InputSLZ,
        responses={status.HTTP_200_OK: serializers.GatewayListV1OutputSLZ(many=True)},
        tags=["OpenAPI.Gateway"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.GatewayListV1InputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self._filter_list_queryset(
            name=data.get("name"),
            query=data.get("query"),
            fuzzy=data.get("fuzzy"),
        )
        gateway_ids = list(queryset.values_list("id", flat=True))

        slz = self.get_serializer(
            queryset,
            many=True,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(scope_ids=gateway_ids),
            },
        )
        return V1OKJsonResponse(data=sorted(slz.data, key=operator.itemgetter("name")))

    def _filter_list_queryset(
        self,
        name: Optional[str] = None,
        query: Optional[str] = None,
        fuzzy: Optional[bool] = None,
    ) -> QuerySet:
        """
        获取可用的网关列表
        - 1. 已启用
        - 2. 公开
        - 3. 已发布
        - 4. 满足 name、query 过滤条件
        """
        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        if name:
            # 模糊匹配，查询名称中包含 name 的网关 or 精确匹配，查询名称为 name 的网关
            queryset = queryset.filter(name__contains=name) if fuzzy else queryset.filter(name=name)

        if query and fuzzy:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        # 过滤出已发布的网关 ID
        gateway_ids = list(queryset.values_list("id", flat=True))
        released_gateway_ids = ReleaseHandler.filter_released_gateway_ids(gateway_ids)

        return queryset.filter(id__in=released_gateway_ids)


class GatewayRetrieveApi(generics.RetrieveAPIView):
    serializer_class = serializers.GatewayRetrieveV1OutputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.GatewayRetrieveV1OutputSLZ()}, tags=["OpenAPI.Gateway"]
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return V1OKJsonResponse(data=slz.data)


class GatewayPublicKeyRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [GatewayRelatedAppPermission]
    gateway_permission_exempt = True

    @swagger_auto_schema(tags=["OpenAPI.Gateway"])
    def get(self, request, gateway_name: str, *args, **kwargs):
        jwt = JWT.objects.get(gateway=request.gateway)
        return V1OKJsonResponse(
            "OK",
            data={
                "issuer": getattr(settings, "JWT_ISSUER", ""),
                "public_key": jwt.public_key,
            },
        )


class GatewaySyncApi(generics.CreateAPIView):
    serializer_class = serializers.GatewaySyncInputSLZ
    permission_classes = [GatewayRelatedAppPermission]
    allow_gateway_not_exist = True

    @swagger_auto_schema(request_body=serializers.GatewaySyncInputSLZ, tags=["OpenAPI.Gateway"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        request.data["name"] = gateway_name
        slz = self.get_serializer(getattr(request, "gateway", None), data=request.data)
        slz.is_valid(raise_exception=True)

        # sync gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        synchronizer = GatewaySynchronizer(
            gateway=slz.instance,
            gateway_data=parse_obj_as(GatewaySyncData, slz.validated_data),
            bk_app_code=request.app.app_code,
            username=username,
        )
        gateway = synchronizer.sync()

        # record audit log
        GatewayHandler.record_audit_log_success(
            username=username,
            gateway_id=gateway.id,
            op_type=OpTypeEnum.CREATE if slz.instance else OpTypeEnum.MODIFY,
            instance_id=gateway.id,
            instance_name=gateway.name,
        )

        return V1OKJsonResponse(
            "OK",
            data={
                "id": gateway.id,
                "name": gateway.name,
            },
        )


class GatewayUpdateStatusApi(generics.CreateAPIView):
    serializer_class = serializers.GatewayUpdateStatusInputSLZ
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=serializers.GatewayUpdateStatusInputSLZ, tags=["OpenAPI.Gateway"])
    def post(self, request, *args, **kwargs):
        slz = self.get_serializer(self.request.gateway, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        return V1OKJsonResponse()


class GatewayRelatedAppAddApi(generics.CreateAPIView):
    serializer_class = serializers.AddRelatedAppsAddInputSLZ
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=serializers.AddRelatedAppsAddInputSLZ, tags=["OpenAPI.Gateway"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        exist_app_codes = self._get_exist_app_codes(slz.validated_data["target_app_codes"])
        for bk_app_code in set(slz.validated_data["target_app_codes"]) - set(exist_app_codes):
            GatewayRelatedAppHandler.add_related_app(request.gateway.id, bk_app_code)

        return V1OKJsonResponse()

    def _get_exist_app_codes(self, bk_app_code_list: List[str]) -> List[str]:
        return list(
            GatewayRelatedApp.objects.filter(
                gateway=self.request.gateway,
                bk_app_code__in=bk_app_code_list,
            ).values_list("bk_app_code", flat=True)
        )
