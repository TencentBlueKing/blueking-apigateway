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

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.esb.permission import serializers
from apigateway.apps.esb.bkcore.models import (
    AppPermissionApplyRecord,
    ComponentSystem,
    ESBChannel,
)
from apigateway.biz.esb.permissions import ComponentPermissionManager
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import V1OKJsonResponse

logger = logging.getLogger(__name__)


class ComponentViewSet(viewsets.GenericViewSet):
    request_from_gateway_required = True
    serializer_class = serializers.AppPermissionComponentSLZ

    @swagger_auto_schema(
        query_serializer=serializers.AppPermissionComponentQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionComponentSLZ(many=True)},
        tags=["OpenAPI.ESB.Permission"],
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
        return V1OKJsonResponse("OK", data=output_slz.data)


class AppPermissionApplyV1APIView(viewsets.GenericViewSet):
    request_from_gateway_required = True
    serializer_class = serializers.AppPermissionApplySLZ

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
        manager.create_apply_record(
            data["target_app_code"],
            system,
            data["component_ids"],
            data["reason"],
            data["expire_days"],
            request.user.username,
        )

        return V1OKJsonResponse("OK")


class AppPermissionRenewAPIView(viewsets.GenericViewSet):
    """
    权限续期
    """

    request_from_gateway_required = True
    serializer_class = serializers.AppPermissionRenewSLZ

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

        return V1OKJsonResponse("OK")


class AppPermissionViewSet(viewsets.ViewSet):
    request_from_gateway_required = True

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
        return V1OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("system_name", "name")))


class AppPermissionApplyRecordViewSet(viewsets.GenericViewSet):
    request_from_gateway_required = True
    serializer_class = serializers.AppPermissionApplyRecordQuerySLZ

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

        slz = serializers.AppPermissionApplyRecordV1SLZ(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(slz.data))

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
        return V1OKJsonResponse("OK", data=slz.data)
