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
from pydantic import TypeAdapter
from rest_framework import generics, serializers, status

from apigateway.apis.open.permissions import (
    OpenAPIGatewayIdPermission,
    OpenAPIGatewayNamePermission,
    OpenAPIGatewayRelatedAppPermission,
    OpenAPIPermission,
)
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway.saver import GatewayData, GatewaySaver
from apigateway.biz.gateway_related_app import GatewayRelatedAppHandler
from apigateway.biz.release import ReleaseHandler
from apigateway.common.constants import (
    CACHE_MAXSIZE,
    CACHE_TIME_5_MINUTES,
)
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.tenant.constants import (
    TENANT_MODE_SINGLE_DEFAULT_TENANT_ID,
    TenantModeEnum,
)
from apigateway.components.bkauth import get_app_info, list_all_apps_of_tenant
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import JWT, Gateway
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import V1OKJsonResponse

from .serializers import (
    GatewayListV1InputSLZ,
    GatewayListV1OutputSLZ,
    GatewayMaintainerUpdateInputSLZ,
    GatewayRelatedAppsAddInputSLZ,
    GatewayRetrieveV1OutputSLZ,
    GatewaySyncInputSLZ,
    GatewayUpdateStatusInputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表，网关需公开且已发布",
        query_serializer=GatewayListV1InputSLZ,
        responses={status.HTTP_200_OK: GatewayListV1OutputSLZ(many=True)},
        tags=["OpenAPI.V1"],
    ),
)
class GatewayListApi(generics.ListAPIView):
    serializer_class = GatewayListV1OutputSLZ
    permission_classes = [OpenAPIPermission]

    def get_queryset(self):
        return Gateway.objects.all()

    def list(self, request, *args, **kwargs):
        slz = GatewayListV1InputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        # 多租户环境，需要获取 tenant_mode/tenant_id作为过滤条件，是必传的
        tenant_id = None
        if settings.ENABLE_MULTI_TENANT_MODE:
            if not request.tenant_id:
                raise serializers.ValidationError("tenant_id is required in multi-tenant mode")
            tenant_id = request.tenant_id

        queryset = self._filter_list_queryset(
            name=data.get("name"),
            query=data.get("query"),
            user_auth_type=data.get("user_auth_type"),
            fuzzy=data.get("fuzzy"),
            tenant_id=tenant_id,
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
        tenant_id: Optional[str] = None,
    ) -> QuerySet:
        """
        获取可用的网关列表
        - 1. 已启用
        - 2. 公开
        - 3. 已发布
        - 4. 满足 name、query, user_auth_type 等过滤条件
        """
        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        # 可以申请全租户网关接口 + 本租户网关接口的权限
        if tenant_id:
            queryset = queryset.filter(
                Q(tenant_mode=TenantModeEnum.GLOBAL.value)
                | Q(tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=tenant_id)
            )

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
        responses={status.HTTP_200_OK: GatewayRetrieveV1OutputSLZ()},
        tags=["OpenAPI.V1"],
    ),
)
class GatewayIdRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIGatewayIdPermission]
    serializer_class = GatewayRetrieveV1OutputSLZ
    lookup_url_kwarg = "gateway_id"
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return V1OKJsonResponse(data=slz.data)


class GatewayPublicKeyRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIGatewayNamePermission]

    @swagger_auto_schema(tags=["OpenAPI.V1"])
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
    permission_classes = [OpenAPIGatewayRelatedAppPermission]
    allow_gateway_not_exist = True
    serializer_class = GatewaySyncInputSLZ

    @swagger_auto_schema(request_body=GatewaySyncInputSLZ, tags=["OpenAPI.V1"])
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

        # assign the tenant_mode and tenant_id
        if settings.ENABLE_MULTI_TENANT_MODE:
            app_info = get_app_info(request.app.app_code)
            slz.validated_data["tenant_mode"] = app_info["tenant_mode"]
            slz.validated_data["tenant_id"] = app_info["tenant_id"]
        else:
            slz.validated_data["tenant_mode"] = TenantModeEnum.SINGLE.value
            slz.validated_data["tenant_id"] = TENANT_MODE_SINGLE_DEFAULT_TENANT_ID

        # save gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        saver = GatewaySaver(
            id=gateway and gateway.id,
            data=TypeAdapter(GatewayData).validate_python(slz.validated_data),
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


class GatewayRelatedAppUpdateStatusApi(generics.CreateAPIView):
    permission_classes = [OpenAPIGatewayRelatedAppPermission]
    serializer_class = GatewayUpdateStatusInputSLZ

    @swagger_auto_schema(request_body=GatewayUpdateStatusInputSLZ, tags=["OpenAPI.V1"])
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
    permission_classes = [OpenAPIGatewayRelatedAppPermission]
    serializer_class = GatewayRelatedAppsAddInputSLZ

    @swagger_auto_schema(request_body=GatewayRelatedAppsAddInputSLZ, tags=["OpenAPI.V1"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        target_app_codes = slz.validated_data["target_app_codes"]

        # check if all the target_app_codes are in the same tenant
        apps_of_tenant = list_all_apps_of_tenant(request.gateway.tenant_mode, request.gateway.tenant_id)
        app_codes_of_tenant = {app["bk_app_code"] for app in apps_of_tenant}
        for app_code in target_app_codes:
            if app_code not in app_codes_of_tenant:
                raise serializers.ValidationError(
                    {"target_app_codes": f"app_code {app_code} not belong to the tenant {request.gateway.tenant_id}"}
                )

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


class GatewayMaintainerUpdateApi(generics.UpdateAPIView):
    permission_classes = [OpenAPIGatewayIdPermission]
    serializer_class = GatewayMaintainerUpdateInputSLZ

    lookup_url_kwarg = "gateway_id"
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    @swagger_auto_schema(request_body=GatewayMaintainerUpdateInputSLZ, tags=["OpenAPI.V1"])
    def put(self, request, *args, **kwargs):
        slz = self.get_serializer(request.gateway, data=request.data)
        slz.is_valid(raise_exception=True)

        maintainers = slz.validated_data["maintainers"]

        # record audit log
        # gateway = request.gateway
        instance = self.get_object()

        # FIXME: if multi tenant mode, the maintainers should be the same tenant of the gateway
        # currently, the gateway list filtered by tenant_id, so it's not so important for now

        data_before = instance.maintainers
        instance.maintainers = maintainers
        instance.save()

        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={"maintainers": data_before},
            data_after={"maintainers": maintainers},
        )

        return V1OKJsonResponse()


class GatewayIdUpdateStatusApi(generics.UpdateAPIView):
    permission_classes = [OpenAPIGatewayIdPermission]
    serializer_class = GatewayUpdateStatusInputSLZ

    lookup_url_kwarg = "gateway_id"
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    @swagger_auto_schema(request_body=GatewayUpdateStatusInputSLZ, tags=["OpenAPI.V1"])
    def put(self, request, *args, **kwargs):
        # FIXME: should check it has the right to update the gateway status
        instance = self.get_object()

        status_before = instance.status

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        # record audit log
        # gateway = request.gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=instance.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={"status": status_before},
            data_after={"status": slz.validated_data["status"]},
        )

        return V1OKJsonResponse()
