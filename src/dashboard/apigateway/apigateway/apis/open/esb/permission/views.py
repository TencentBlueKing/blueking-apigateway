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

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apis.open.esb.permission import serializers
from apigateway.apis.open.esb.permission.helpers import ComponentPermissionBuilder
from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    AppPermissionApplyStatus,
    ComponentSystem,
    ESBChannel,
)
from apigateway.apps.esb.permission.serializers import AppPermissionApplyRecordDetailSLZ
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.tasks import send_mail_for_perm_apply
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import V1OKJsonResponse

logger = logging.getLogger(__name__)


class ComponentViewSet(viewsets.GenericViewSet):
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

        component_permissions = ComponentPermissionBuilder(
            system_id,
            slz.validated_data["target_app_code"],
        ).build(components)

        slz = self.get_serializer(
            sorted(component_permissions, key=operator.itemgetter("permission_level", "name")),
            many=True,
        )
        return V1OKJsonResponse("OK", data=slz.data)


class AppPermissionApplyV1APIView(viewsets.GenericViewSet):
    @transaction.atomic
    def apply(self, request, system_id: int, *args, **kwargs):
        """创建申请资源权限的申请单据"""
        try:
            system = ComponentSystem.objects.get(id=system_id)
        except ComponentSystem.DoesNotExist:
            raise error_codes.NOT_FOUND

        slz = serializers.AppPermissionApplySLZ(
            data=request.data,
            context={
                "system_id": system.id,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        for component_ids in ESBChannel.objects.group_by_permission_level(data["component_ids"]):
            instance = AppPermissionApplyRecord.objects.create_record(
                board=system.board,
                bk_app_code=data["target_app_code"],
                applied_by=request.user.username,
                system=system,
                component_ids=component_ids,
                status=ApplyStatusEnum.PENDING.value,
                reason=data["reason"],
                expire_days=data["expire_days"],
            )

            if AppPermissionApplyStatus is not None:
                # 删除应用-组件申请状态的历史记录，方便下面批量插入
                AppPermissionApplyStatus.objects.filter(
                    bk_app_code=data["target_app_code"],
                    system=system,
                    component_id__in=component_ids,
                ).delete()
                AppPermissionApplyStatus.objects.batch_create(
                    record=instance,
                    bk_app_code=data["target_app_code"],
                    system=system,
                    component_ids=component_ids,
                    status=ApplyStatusEnum.PENDING.value,
                )

            try:
                apply_async_on_commit(send_mail_for_perm_apply, args=[instance.id])
            except Exception:
                logger.exception("send mail to gateway manager fail. apply_record_id=%s", instance.id)

        return V1OKJsonResponse("OK")


class AppPermissionRenewAPIView(viewsets.GenericViewSet):
    """
    权限续期
    """

    def renew(self, request, *args, **kwargs):
        slz = serializers.AppPermissionRenewSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppComponentPermission.objects.renew_permissions(
            data["target_app_code"],
            data["component_ids"],
            data["expire_days"],
        )

        return V1OKJsonResponse("OK")


class AppPermissionViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        """已申请权限列表"""
        slz = serializers.AppPermissionQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        component_ids = AppComponentPermission.objects.filter_component_ids(
            bk_app_code=data["target_app_code"],
            expire_days_range=data.get("expire_days_range"),
        )
        queryset = ESBChannel.objects.filter_active_and_public_components(
            ids=component_ids,
            allow_apply_permission=True,
        )
        components = ESBChannel.objects.get_components(queryset)

        component_permissions = ComponentPermissionBuilder(
            None,
            data["target_app_code"],
        ).build(components)

        slz = serializers.AppPermissionComponentSLZ(component_permissions, many=True)
        return V1OKJsonResponse("OK", data=sorted(slz.data, key=operator.itemgetter("system_name", "name")))


class AppPermissionApplyRecordViewSet(viewsets.GenericViewSet):
    def list(self, request, *args, **kwargs):
        slz = serializers.AppPermissionApplyRecordQuerySLZ(data=request.query_params)
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

        page = self.paginate_queryset(queryset)
        slz = serializers.AppPermissionApplyRecordV1SLZ(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(slz.data))

    def retrieve(self, request, record_id: int, *args, **kwargs):
        slz = serializers.AppPermissionApplyRecordQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        try:
            record = AppPermissionApplyRecord.objects.get(bk_app_code=data["target_app_code"], id=record_id)
        except AppPermissionApplyRecord.DoesNotExist:
            raise error_codes.NOT_FOUND

        slz = AppPermissionApplyRecordDetailSLZ(record)
        return V1OKJsonResponse("OK", data=slz.data)
