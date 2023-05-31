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
from typing import Optional

from cachetools import TTLCache, cached
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.gateway import serializers
from apigateway.common.constants import CACHE_MAXSIZE, CacheTimeLevel
from apigateway.common.contexts import APIAuthContext
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.constants import APIStatusEnum
from apigateway.core.models import JWT, APIRelatedApp, Gateway, Release
from apigateway.utils.responses import OKJsonResponse


class GatewayViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.GatewayV1SLZ
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_SHORT.value))
    def _filter_available_gateways(
        self,
        queryset,
        name: Optional[str] = None,
        query: Optional[str] = None,
        user_auth_type: Optional[str] = None,
        fuzzy: Optional[bool] = None,
    ):
        """
        获取可用的网关列表
        """
        if name:
            if fuzzy:
                # 模糊匹配，查询名称中包含 name 的网关
                queryset = queryset.filter(name__contains=name)
            else:
                # 精确匹配，查询名称为 name 的网关
                queryset = queryset.filter(name=name)

        if query and fuzzy:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        gateway_ids = list(queryset.values_list("id", flat=True))
        # 过滤出用户类型为指定类型的网关
        if user_auth_type:
            scope_id_config_map = APIAuthContext().filter_scope_id_config_map(scope_ids=gateway_ids)
            gateway_ids = [
                scope_id
                for scope_id, config in scope_id_config_map.items()
                if config["user_auth_type"] == user_auth_type
            ]
        # 过滤出已发布的网关ID
        released_gateway_ids = Release.objects.filter_released_gateway_ids(gateway_ids)

        return queryset.filter(id__in=released_gateway_ids)

    @swagger_auto_schema(
        query_serializer=serializers.GatewayQueryV1SLZ,
        responses={status.HTTP_200_OK: serializers.GatewayV1SLZ(many=True)},
        tags=["OpenAPI.Gateway"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.GatewayQueryV1SLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        # 过滤出状态为 active，且公开的网关
        queryset = queryset.filter(status=APIStatusEnum.ACTIVE.value, is_public=True)

        gateway_queryset = self._filter_available_gateways(
            queryset,
            name=data.get("name"),
            query=data.get("query"),
            user_auth_type=data.get("user_auth_type"),
            fuzzy=data.get("fuzzy"),
        )
        gateway_ids = list(gateway_queryset.values_list("id", flat=True))

        slz_class = self.get_serializer_class()
        slz = slz_class(
            gateway_queryset,
            many=True,
            context={
                "api_auth_contexts": APIAuthContext().filter_scope_id_config_map(scope_ids=gateway_ids),
            },
        )
        return OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("name")))

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.GatewayV1DetailSLZ()}, tags=["OpenAPI.Gateway"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.GatewayV1DetailSLZ(instance)
        return OKJsonResponse("OK", data=slz.data)


class GatewayPublicKeyViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]
    api_permission_exempt = True

    @swagger_auto_schema(tags=["OpenAPI.Gateway"])
    def get_public_key(self, request, gateway_name: str, *args, **kwargs):
        jwt = JWT.objects.get(api=request.gateway)
        return OKJsonResponse(
            "OK",
            data={
                "issuer": getattr(settings, "JWT_ISSUER", ""),
                "public_key": jwt.public_key,
            },
        )


class GatewaySyncViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]
    allow_api_not_exist = True

    @swagger_auto_schema(request_body=serializers.GatewaySyncSLZ, tags=["OpenAPI.Gateway"])
    @transaction.atomic
    def sync(self, request, gateway_name: str, *args, **kwargs):
        request.data["name"] = gateway_name
        slz = serializers.GatewaySyncSLZ(
            getattr(request, "gateway", None),
            data=request.data,
            context={
                "bk_app_code": request.app.app_code,
            },
        )
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username or settings.GATEWAY_DEFAULT_CREATOR,
            updated_by=request.user.username,
        )

        return OKJsonResponse(
            "OK",
            data={
                "id": slz.instance.id,
                "name": slz.instance.name,
            },
        )


class GatewayUpdateStatusViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=serializers.GatewayUpdateStatusSLZ, tags=["OpenAPI.Gateway"])
    def update_status(self, request, *args, **kwargs):
        slz = serializers.GatewayUpdateStatusSLZ(self.request.gateway, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        return OKJsonResponse()


class GatewayRelatedAppViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(request_body=serializers.GatewaySyncSLZ, tags=["OpenAPI.Gateway"])
    @transaction.atomic
    def add_related_apps(self, request, gateway_name: str, *args, **kwargs):
        slz = serializers.AddRelatedAppsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        for bk_app_code in slz.validated_data["target_app_codes"]:
            APIRelatedApp.objects.get_or_create(api=request.gateway, bk_app_code=bk_app_code)

        return OKJsonResponse("OK")
