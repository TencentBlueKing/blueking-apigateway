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
from django.db.models.query import QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from pydantic import parse_obj_as
from rest_framework import generics, status

from apigateway.apis.open.gateway import serializers
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway.saver import GatewayData, GatewaySaver
from apigateway.biz.gateway_related_app import GatewayRelatedAppHandler
from apigateway.biz.release import ReleaseHandler
from apigateway.common.constants import CACHE_MAXSIZE, CACHE_TIME_5_MINUTES
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import JWT, Gateway
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import V1OKJsonResponse


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表，网关需公开且已发布",
        query_serializer=serializers.GatewayListV1InputSLZ,
        responses={status.HTTP_200_OK: serializers.GatewayListV1OutputSLZ(many=True)},
        tags=["OpenAPI.Gateway"],
    ),
)
class GatewayListApi(generics.ListAPIView):
    serializer_class = serializers.GatewayListV1OutputSLZ
    request_from_gateway_required = True

    def get_queryset(self):
        return Gateway.objects.all()

    def list(self, request, *args, **kwargs):
        slz = serializers.GatewayListV1InputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self._filter_list_queryset(
            name=data.get("name"),
            query=data.get("query"),
            user_auth_type=data.get("user_auth_type"),
            fuzzy=data.get("fuzzy"),
        )
        gateway_ids = list(queryset.values_list("id", flat=True))

        slz = self.get_serializer(
            queryset,
            many=True,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids),
            },
        )
        return V1OKJsonResponse(data=sorted(slz.data, key=operator.itemgetter("name")))

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TIME_5_MINUTES))
    def _filter_list_queryset(
        self,
        name: Optional[str] = None,
        query: Optional[str] = None,
        user_auth_type: Optional[str] = None,
        fuzzy: Optional[bool] = None,
    ) -> QuerySet:
        """
        获取可用的网关列表
        - 1. 已启用
        - 2. 公开
        - 3. 已发布
        - 4. 满足 name、query, user_auth_type 等过滤条件
        """
        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        if name:
            # 模糊匹配，查询名称中包含 name 的网关 or 精确匹配，查询名称为 name 的网关
            queryset = queryset.filter(name__contains=name) if fuzzy else queryset.filter(name=name)

        if query and fuzzy:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        # 过滤出用户类型为指定类型的网关
        gateway_ids = list(queryset.values_list("id", flat=True))
        if user_auth_type:
            gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids)
            gateway_ids = [
                gateway_id
                for gateway_id, auth_config in gateway_auth_configs.items()
                if auth_config.user_auth_type == user_auth_type
            ]

        # 过滤出已发布的网关 ID
        released_gateway_ids = ReleaseHandler.filter_released_gateway_ids(gateway_ids)

        return queryset.filter(id__in=released_gateway_ids)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.GatewayRetrieveV1OutputSLZ()},
        tags=["OpenAPI.Gateway"],
    ),
)
class GatewayRetrieveApi(generics.RetrieveAPIView):
    request_from_gateway_required = True
    serializer_class = serializers.GatewayRetrieveV1OutputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

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
    permission_classes = [GatewayRelatedAppPermission]
    serializer_class = serializers.GatewaySyncInputSLZ
    allow_gateway_not_exist = True

    @swagger_auto_schema(request_body=serializers.GatewaySyncInputSLZ, tags=["OpenAPI.Gateway"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        gateway = getattr(request, "gateway", None)

        data_before = get_model_dict(gateway) if gateway else {}

        request.data["name"] = gateway_name
        # gateway 为 None，则应为新建；非 None，则应为更新；
        # slz 中仅校验数据，不保存网关数据，利用 GatewaySaver 处理网关的保存；
        # 抽象出 GatewaySaver，是因 django command 中需要复用此 saver 中保存网关数据的逻辑
        slz = self.get_serializer(gateway, data=request.data)
        slz.is_valid(raise_exception=True)

        # save gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        saver = GatewaySaver(
            id=gateway and gateway.id,
            data=parse_obj_as(GatewayData, slz.validated_data),
            bk_app_code=request.app.app_code,
            username=username,
        )
        gateway = saver.save()

        # record audit log
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY if slz.instance else OpTypeEnum.CREATE,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before=data_before,
            data_after=get_model_dict(gateway),
        )

        return V1OKJsonResponse(
            "OK",
            data={
                "id": gateway.id,
                "name": gateway.name,
            },
        )


class GatewayUpdateStatusApi(generics.CreateAPIView):
    permission_classes = [GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayUpdateStatusInputSLZ

    @swagger_auto_schema(request_body=serializers.GatewayUpdateStatusInputSLZ, tags=["OpenAPI.Gateway"])
    def post(self, request, *args, **kwargs):
        slz = self.get_serializer(request.gateway, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        # record audit log
        gateway = request.gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before={"status": gateway.status},
            data_after={"status": slz.validated_data["status"]},
        )

        return V1OKJsonResponse()


class GatewayRelatedAppAddApi(generics.CreateAPIView):
    permission_classes = [GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayRelatedAppsAddInputSLZ

    @swagger_auto_schema(request_body=serializers.GatewayRelatedAppsAddInputSLZ, tags=["OpenAPI.Gateway"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        target_app_codes = slz.validated_data["target_app_codes"]

        related_app_codes = GatewayRelatedAppHandler.get_related_app_codes(request.gateway.id)
        missing_app_codes = set(target_app_codes) - set(related_app_codes)
        for bk_app_code in missing_app_codes:
            GatewayRelatedAppHandler.add_related_app(request.gateway.id, bk_app_code)

        # record audit log
        gateway = request.gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before={"related_app_codes": related_app_codes},
            data_after={"added_related_app_codes": list(missing_app_codes)},
        )

        return V1OKJsonResponse()
