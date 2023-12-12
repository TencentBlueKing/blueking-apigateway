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
import logging
import operator
from abc import ABCMeta, abstractmethod

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.views import APIView

from apigateway.apis.open.permission.helpers import (
    AppPermissionBuilder,
    ResourcePermissionBuilder,
)
from apigateway.apps.permission.constants import (
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionRecord,
    AppResourcePermission,
)
from apigateway.apps.permission.tasks import send_mail_for_perm_apply
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Gateway, Resource
from apigateway.utils.responses import V1OKJsonResponse

from . import serializers

logger = logging.getLogger(__name__)


def get_permission_model(dimension: str):
    if dimension == GrantDimensionEnum.API.value:
        return AppGatewayPermission

    if dimension == GrantDimensionEnum.RESOURCE.value:
        return AppResourcePermission

    raise ValueError(f"unsupported dimension: {dimension}")


class ResourceViewSet(viewsets.ViewSet):
    gateway_permission_exempt = True

    @swagger_auto_schema(
        query_serializer=serializers.AppResourcePermissionInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppResourcePermissionOutputSLZ(many=True)},
        tags=["OpenAPI.Permission"],
    )
    def list(self, request, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            return V1OKJsonResponse("OK", data=[])

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
        return V1OKJsonResponse("OK", data=slz.data)


class AppGatewayPermissionViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.AppGatewayPermissionInputSLZ
    gateway_permission_exempt = True

    def allow_apply_by_gateway(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        allow, reason = PermissionDimensionManager.get_manager(GrantDimensionEnum.API.value).allow_apply_permission(
            request.gateway.id, slz.validated_data["target_app_code"]
        )

        return V1OKJsonResponse(
            "OK",
            data={
                "allow_apply_by_api": allow,
                "reason": reason,
            },
        )


class BaseAppPermissinApplyAPIView(APIView, metaclass=ABCMeta):
    @abstractmethod
    def get_serializer_class(self):
        pass

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        创建申请资源权限的申请单据
        """
        slz = self.get_serializer_class()(
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
            data.get("resource_ids", []),
            data["grant_dimension"],
            data["reason"],
            data.get("expire_days", PermissionApplyExpireDaysEnum.FOREVER.value),
            request.user.username,
        )

        try:
            apply_async_on_commit(send_mail_for_perm_apply, args=[record.id])
        except Exception:
            logger.exception("send mail to gateway manager fail. apply_record_id=%s", record.id)

        return V1OKJsonResponse(
            "OK",
            data={
                "record_id": record.id,
            },
        )


class PaaSAppPermissionApplyAPIView(BaseAppPermissinApplyAPIView):
    """
    PaaS中应用申请访问网关API的权限
    - 提供给 paas3 开发者中心的接口
    """

    gateway_permission_exempt = True

    def get_serializer_class(self):
        return serializers.PaaSAppPermissionApplyInputSLZ


class AppPermissionApplyV1APIView(BaseAppPermissinApplyAPIView):
    """
    普通应用直接申请访问网关API的权限
    - 提供给普通应用的接口
    - 支持应用，申请网关API的权限
    - 暂支持按网关申请，不支持按资源申请
    """

    # 使用 GatewayRelatedAppPermission 中设置request.gateway 的功能，而不需要校验权限
    permission_classes = [GatewayRelatedAppPermission]
    gateway_permission_exempt = True

    def get_serializer_class(self):
        return serializers.AppPermissionApplyV1InputSLZ


class AppPermissionGrantViewSet(viewsets.ViewSet):
    """网关关联应用，主动为应用授权访问网关API的权限"""

    permission_classes = [GatewayRelatedAppPermission]

    def grant(self, request, *args, **kwargs):
        slz = serializers.GrantAppPermissionInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        resource_ids = list(
            Resource.objects.filter(gateway=request.gateway, name__in=data.get("resource_names") or []).values_list(
                "id", flat=True
            )
        )

        permission_model = get_permission_model(data["grant_dimension"])
        permission_model.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=resource_ids,
            bk_app_code=data["target_app_code"],
            expire_days=data.get("expire_days"),
            grant_type=GrantTypeEnum.INITIALIZE.value,
        )

        return V1OKJsonResponse("OK")


class RevokeAppPermissionViewSet(viewsets.ViewSet):
    """网关关联应用，回收应用访问网关API的权限"""

    permission_classes = [GatewayRelatedAppPermission]

    def revoke(self, request, *args, **kwargs):
        slz = serializers.RevokeAppPermissionInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permission_model = get_permission_model(data["grant_dimension"])
        permission_model.objects.filter(
            gateway=request.gateway,
            bk_app_code__in=data["target_app_codes"],
        ).delete()

        return V1OKJsonResponse("OK")


class AppPermissionRenewAPIView(APIView):
    """
    权限续期
    """

    gateway_permission_exempt = True

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
            # 如果应用-资源权限不存在，则将按网关的权限同步到应用-资源权限
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

        return V1OKJsonResponse("OK")


class AppPermissionViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        """已申请权限列表"""
        slz = serializers.AppPermissionInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permissions = AppPermissionBuilder(data["target_app_code"]).build()
        slz = serializers.AppResourcePermissionOutputSLZ(permissions, many=True)
        return V1OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("api_name", "name")))


class AppPermissionRecordViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.AppPermissionRecordInputSLZ

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
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(slz.data))

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
        return V1OKJsonResponse("OK", data=slz.data)
