# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import logging
import operator
from typing import List

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, viewsets
from rest_framework.views import APIView

from apigateway.apis.v2.permissions import OpenAPIV2GatewayNamePermission, OpenAPIV2Permission
from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord, ComponentSystem, ESBChannel
from apigateway.apps.permission.constants import GrantDimensionEnum, GrantTypeEnum, PermissionApplyExpireDaysEnum
from apigateway.apps.permission.models import AppPermissionRecord, AppResourcePermission
from apigateway.apps.permission.tasks import send_mail_for_perm_apply
from apigateway.biz.esb.permissions import ComponentPermissionManager
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway
from apigateway.utils.responses import OKJsonResponse

from . import serializers
from .helpers import AppPermissionBuilder, ResourcePermissionBuilder

logger = logging.getLogger(__name__)


# 注意：请使用 OpenAPIV2Permission / OpenAPIV2GatewayNamePermission, 有特殊情况请在类注释中说明


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表，网关需公开且已发布",
        query_serializer=serializers.GatewayListInputSLZ,
        responses={status.HTTP_200_OK: serializers.GatewayListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayListApi(generics.ListAPIView):
    serializer_class = serializers.GatewayListOutputSLZ
    permission_classes = [OpenAPIV2Permission]

    def get_queryset(self):
        return Gateway.objects.all()

    def list(self, request, *args, **kwargs):
        """
        获取可用的网关列表
        - 1. 已启用
        - 2. 公开
        - 3. 已发布
        - 4. 满足 name 过滤条件
        """
        slz = serializers.GatewayListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        name = slz.validated_data.get("name")
        fuzzy = slz.validated_data.get("fuzzy")

        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)
        if name:
            # 模糊匹配，查询名称中包含 name 的网关 or 精确匹配，查询名称为 name 的网关
            queryset = queryset.filter(name__contains=name) if fuzzy else queryset.filter(name=name)

        # 过滤出用户类型为指定类型的网关
        all_gateway_ids = list(queryset.values_list("id", flat=True))
        # 过滤出已发布的网关 ID
        released_gateway_ids = ReleaseHandler.filter_released_gateway_ids(all_gateway_ids)

        queryset = queryset.filter(id__in=released_gateway_ids)
        output_slz = self.get_serializer(queryset, many=True)
        output_data = sorted(output_slz.data, key=operator.itemgetter("name"))

        return OKJsonResponse(data=output_data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.GatewayRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.GatewayRetrieveOutputSLZ
    lookup_url_kwarg = "gateway_name"
    lookup_field = "name"

    def get_queryset(self):
        return Gateway.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse(data=slz.data)


class ResourceViewSet(viewsets.ViewSet):
    permission_classes = [OpenAPIV2GatewayNamePermission]

    @swagger_auto_schema(
        query_serializer=serializers.AppResourcePermissionInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppResourcePermissionOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            return OKJsonResponse(data=[])

        slz = serializers.AppResourcePermissionInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        resources = ResourceVersionHandler.get_released_public_resources(request.gateway.id)

        # 过滤掉不允许主动申请权限的资源
        resources = list(filter(lambda x: x["allow_apply_permission"], resources))

        resource_permissions = ResourcePermissionBuilder(
            self.request.gateway,
            slz.validated_data["target_app_code"],
        ).build(resources)

        slz = serializers.AppResourcePermissionOutputSLZ(
            sorted(resource_permissions, key=operator.itemgetter("permission_level", "name")),
            many=True,
        )
        return OKJsonResponse(data=slz.data)


class AppGatewayPermissionViewSet(viewsets.GenericViewSet):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.AppGatewayPermissionInputSLZ

    @swagger_auto_schema(
        query_serializer=serializers.AppGatewayPermissionInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppGatewayPermissionOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def allow_apply_by_gateway(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        allow, reason = PermissionDimensionManager.get_manager(GrantDimensionEnum.API.value).allow_apply_permission(
            request.gateway.id, slz.validated_data["target_app_code"]
        )

        return OKJsonResponse(
            data={
                "allow_apply_by_api": allow,
                "reason": reason,
            }
        )


class PaaSAppPermissionApplyAPIView(APIView):
    """
    PaaS 中应用申请访问网关 API 的权限
    - 提供给 paas3 开发者中心的接口
    """

    permission_classes = [OpenAPIV2GatewayNamePermission]

    @swagger_auto_schema(request_body=serializers.PaaSAppPermissionApplyInputSLZ, tags=["OpenAPI.V2.Inner"])
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        创建申请资源权限的申请单据
        """
        slz = serializers.PaaSAppPermissionApplyInputSLZ(
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = PermissionDimensionManager.get_manager(data["grant_dimension"])
        record = manager.create_apply_record(
            data["target_app_code"],
            request.gateway,
            data.get("resource_ids") or [],
            data["grant_dimension"],
            data["reason"],
            data.get("expire_days", PermissionApplyExpireDaysEnum.FOREVER.value),
            request.user.username,
        )

        try:
            apply_async_on_commit(send_mail_for_perm_apply, args=[record.id])
        except Exception:
            logger.exception("send mail to gateway manager fail. apply_record_id=%s", record.id)

        return OKJsonResponse(
            data={
                "record_id": record.id,
            }
        )


class AppPermissionRenewAPIView(APIView):
    """
    权限续期
    """

    permission_classes = [OpenAPIV2Permission]

    @swagger_auto_schema(request_body=serializers.AppPermissionRenewInputSLZ, tags=["OpenAPI.V2.Inner"])
    def post(self, request, *args, **kwargs):
        slz = serializers.AppPermissionRenewInputSLZ(
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        for gateway_id, resource_ids in ResourceHandler.group_by_gateway_id(data["resource_ids"]).items():
            gateway = Gateway.objects.get(id=gateway_id)
            # 如果应用 - 资源权限不存在，则将按网关的权限同步到应用 - 资源权限
            AppResourcePermission.objects.sync_from_gateway_permission(
                gateway=gateway,
                bk_app_code=data["target_app_code"],
                resource_ids=resource_ids,
            )
            AppResourcePermission.objects.renew_by_resource_ids(
                gateway=gateway,
                bk_app_code=data["target_app_code"],
                resource_ids=resource_ids,
                grant_type=GrantTypeEnum.RENEW.value,
                expire_days=data["expire_days"],
            )

        return OKJsonResponse()


class AppPermissionViewSet(viewsets.ViewSet):
    permission_classes = [OpenAPIV2Permission]

    @swagger_auto_schema(
        query_serializer=serializers.AppPermissionInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppResourcePermissionOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, *args, **kwargs):
        """已申请权限列表"""
        slz = serializers.AppPermissionInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permissions = AppPermissionBuilder(data["target_app_code"]).build()
        slz = serializers.AppResourcePermissionOutputSLZ(permissions, many=True)
        return OKJsonResponse(data=sorted(slz.data, key=operator.itemgetter("api_name", "name")))


class AppPermissionRecordViewSet(viewsets.GenericViewSet):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionRecordInputSLZ

    @swagger_auto_schema(
        query_serializer=serializers.AppPermissionRecordInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionRecordSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AppPermissionRecord.objects.all()
        queryset = AppPermissionRecord.objects.filter_record(
            queryset,
            bk_app_code=data["target_app_code"],
            applied_by=data.get("applied_by"),
            applied_time_start=data.get("applied_time_start"),
            applied_time_end=data.get("applied_time_end"),
            status=data.get("apply_status"),
            query=data.get("query"),
            order_by="-id",
        )

        page = self.paginate_queryset(queryset)
        slz = serializers.AppPermissionRecordSLZ(page, many=True)
        return OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.AppPermissionRecordOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    )
    def retrieve(self, request, record_id: int, *args, **kwargs):
        slz = serializers.AppPermissionRecordInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        try:
            record = AppPermissionRecord.objects.get(bk_app_code=data["target_app_code"], id=record_id)
        except AppPermissionRecord.DoesNotExist:
            raise error_codes.NOT_FOUND

        slz = serializers.AppPermissionRecordOutputSLZ(
            record,
            context={
                "resource_id_map": ResourceHandler.get_id_to_resource(gateway_id=record.gateway.id),
            },
        )
        return OKJsonResponse(data=slz.data)


class EsbSystemViewSet(viewsets.GenericViewSet):
    permission_classes = [OpenAPIV2Permission]

    def _filter_active_and_public_systems(self, boards: List[str]):
        """
        获取可用的组件系统列表
        """
        system_ids = ESBChannel.objects.filter_active_and_public_system_ids(
            boards=boards,
            allow_apply_permission=True,
        )

        return ComponentSystem.objects.filter(board__in=boards, id__in=system_ids)

    @swagger_auto_schema(
        query_serializer=serializers.SystemQueryV2SLZ,
        responses={status.HTTP_200_OK: serializers.SystemV2SLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.SystemQueryV2SLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = self._filter_active_and_public_systems(boards=slz.validated_data["boards"])

        slz = serializers.SystemV2SLZ(queryset.order_by("board", "name"), many=True)
        return OKJsonResponse(data=slz.data)


class EsbComponentViewSet(viewsets.GenericViewSet):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionComponentSLZ

    @swagger_auto_schema(
        query_serializer=serializers.AppPermissionComponentQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionComponentSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, system_id: int, *args, **kwargs):
        slz = serializers.AppPermissionComponentQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = ESBChannel.objects.filter_active_and_public_components(system_id=system_id)
        components = ESBChannel.objects.get_components(queryset)

        manager = ComponentPermissionManager.get_manager()
        component_permissions = manager.list_permissions(slz.validated_data["target_app_code"], system_id, components)

        output_slz = self.get_serializer(
            sorted(component_permissions, key=operator.itemgetter("permission_level", "name")),
            many=True,
        )
        return OKJsonResponse(data=output_slz.data)


class EsbAppPermissionApplyV2APIView(viewsets.GenericViewSet):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionApplySLZ

    @swagger_auto_schema(request_body=serializers.AppPermissionApplySLZ, tags=["OpenAPI.V2.Inner"])
    @transaction.atomic
    def apply(self, request, system_id: int, *args, **kwargs):
        """创建申请资源权限的申请单据"""
        try:
            system = ComponentSystem.objects.get(id=system_id)
        except ComponentSystem.DoesNotExist:
            raise error_codes.NOT_FOUND

        slz = self.get_serializer(
            data=request.data,
            context={
                "system_id": system.id,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ComponentPermissionManager.get_manager()
        record = manager.create_apply_record(
            data["target_app_code"],
            system,
            data["component_ids"],
            data["reason"],
            data["expire_days"],
            request.user.username,
        )

        return OKJsonResponse(data={"record_id": record.id})


class EsbAppPermissionRenewAPIView(viewsets.GenericViewSet):
    """
    权限续期
    """

    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionRenewSLZ

    @swagger_auto_schema(request_body=serializers.AppPermissionRenewSLZ, tags=["OpenAPI.V2.Inner"])
    def renew(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ComponentPermissionManager.get_manager()
        manager.renew_permission(
            data["target_app_code"],
            data["component_ids"],
            data["expire_days"],
        )

        return OKJsonResponse()


class EsbAppPermissionViewSet(viewsets.ViewSet):
    permission_classes = [OpenAPIV2Permission]

    @swagger_auto_schema(
        query_serializer=serializers.AppPermissionQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionComponentSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, *args, **kwargs):
        """已申请权限列表"""
        slz = serializers.AppPermissionQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ComponentPermissionManager.get_manager()
        component_permissions = manager.list_applied_permissions(
            data["target_app_code"],
            data.get("expire_days_range"),
        )

        slz = serializers.AppPermissionComponentSLZ(component_permissions, many=True)
        return OKJsonResponse(data=sorted(slz.data, key=operator.itemgetter("system_name", "name")))


class EsbAppPermissionApplyRecordViewSet(viewsets.GenericViewSet):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionApplyRecordQuerySLZ

    @swagger_auto_schema(
        query_serializer=serializers.AppPermissionApplyRecordQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionApplyRecordV2SLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    )
    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AppPermissionApplyRecord.objects.all()
        queryset = AppPermissionApplyRecord.objects.filter_record(
            queryset=queryset,
            bk_app_code=data["target_app_code"],
            applied_by=data.get("applied_by"),
            applied_time_start=data.get("applied_time_start"),
            applied_time_end=data.get("applied_time_end"),
            status=data.get("apply_status"),
            query=data.get("query"),
            order_by="-id",
        )

        page = list(self.paginate_queryset(queryset))

        manager = ComponentPermissionManager.get_manager()
        manager.patch_permission_apply_records(page)

        slz = serializers.AppPermissionApplyRecordV2SLZ(page, many=True)
        return OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(response_serializer=serializers.AppPermissionApplyRecordDetailSLZ, tags=["OpenAPI.V2.Inner"])
    def retrieve(self, request, record_id: int, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        try:
            record = AppPermissionApplyRecord.objects.get(bk_app_code=data["target_app_code"], id=record_id)
        except AppPermissionApplyRecord.DoesNotExist:
            raise error_codes.NOT_FOUND

        manager = ComponentPermissionManager.get_manager()
        manager.patch_permission_apply_records([record])

        slz = serializers.AppPermissionApplyRecordDetailSLZ(record)
        return OKJsonResponse(data=slz.data)
