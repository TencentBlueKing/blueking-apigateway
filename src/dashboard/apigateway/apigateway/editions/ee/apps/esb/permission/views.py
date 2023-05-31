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
from typing import List

from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated

from apigateway.apps.esb.bkcore.models import AppComponentPermission, AppPermissionApplyRecord, ESBChannel
from apigateway.apps.esb.permission import serializers
from apigateway.apps.esb.permission.helpers import PermissionManager
from apigateway.apps.esb.permissions import UserAccessESBPermission
from apigateway.apps.permission.constants import DEFAULT_PERMISSION_EXPIRE_DAYS, ApplyStatusEnum
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class AppPermissionApplyRecordViewSet(viewsets.ModelViewSet):
    """权限申请单 ViewSet"""

    queryset = AppPermissionApplyRecord.objects.all()
    serializer_class = serializers.AppPermissionApplyRecordSLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]
    lookup_field = "id"

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryAppPermissionApplyRecordSLZ,
        response_serializer=serializers.AppPermissionApplyRecordSLZ(many=True),
        tags=["ESB.Permission"],
    )
    def list_pending(self, request, *args, **kwargs):
        """
        获取待审批的申请单列表
        """
        slz = serializers.QueryAppPermissionApplyRecordSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        qs = AppPermissionApplyRecord.objects.filter_record(
            self.get_queryset(),
            bk_app_code=data.get("bk_app_code"),
            applied_by=data.get("applied_by"),
            status=ApplyStatusEnum.PENDING.value,
            order_by="-id",
        )

        page = self.paginate_queryset(qs)
        records = self._serialize_records(page)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(records))

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryAppPermissionApplyRecordSLZ,
        response_serializer=serializers.AppPermissionApplyRecordSLZ(many=True),
        tags=["ESB.Permission"],
    )
    def list_handled(self, request, *args, **kwargs):
        """
        获取已审批的单据
        """
        slz = serializers.QueryAppPermissionApplyRecordSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        qs = AppPermissionApplyRecord.objects.filter_record(
            self.get_queryset(),
            bk_app_code=data.get("bk_app_code"),
            applied_by=data.get("applied_by"),
            handled_time_start=data.get("handled_time_start"),
            handled_time_end=data.get("handled_time_end"),
            order_by="-handled_time",
        )
        qs = qs.exclude(status=ApplyStatusEnum.PENDING.value)

        page = self.paginate_queryset(qs)
        records = self._serialize_records(page)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(records))

    def _serialize_records(self, records: List[AppPermissionApplyRecord]) -> List[dict]:
        component_map = ESBChannel.objects.get_component_map_by_ids(
            list({component_id for record in records for component_id in record.component_ids})
        )
        slz = serializers.AppPermissionApplyRecordSLZ(
            records,
            many=True,
            context={
                "component_map": component_map,
            },
        )

        # sort components
        for record in slz.data:
            record["components"] = sorted(record["components"], key=operator.itemgetter("apply_status", "name"))

        return slz.data

    @swagger_auto_schema(
        response_serializer=serializers.AppPermissionApplyRecordDetailSLZ,
        tags=["ESB.Permission"],
    )
    def retrieve(self, request, id: int, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.AppPermissionApplyRecordDetailSLZ(instance)
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(
        request_body=serializers.BatchHandleAppPermissionApplyRecordSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["ESB.Permission"],
    )
    @transaction.atomic
    def batch_handle(self, request, *args, **kwargs):
        """批量审批"""
        slz = serializers.BatchHandleAppPermissionApplyRecordSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        part_component_ids = data.get("part_component_ids", {})

        for record in AppPermissionApplyRecord.objects.filter(id__in=data["ids"]):
            manager = PermissionManager()
            manager.handle_permission_apply(
                record=record,
                status=data["status"],
                comment=data["comment"],
                handled_by=request.user.username,
                part_component_ids=part_component_ids.get(f"{record.id}"),
            )

        return OKJsonResponse("OK")


class AppComponentPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.BatchAppComponentPermissionSLZ
    permission_classes = [IsAuthenticated, UserAccessESBPermission]

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.QueryAppPermissionSLZ,
        responses={status.HTTP_200_OK: serializers.ESBAppPermissionListSLZ(many=True)},
        tags=["ESB.Permission"],
    )
    def list(self, request, *args, **kwargs):
        """应用权限列表"""
        slz = serializers.QueryAppPermissionSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        qs = AppComponentPermission.objects.filter_permission(
            bk_app_code=data.get("bk_app_code"),
            system_id=data.get("system_id"),
            component_id=data.get("component_id"),
        )

        page = self.paginate_queryset(qs)
        slz = serializers.ESBAppPermissionListSLZ(
            page,
            many=True,
            context={
                "component_map": ESBChannel.objects.get_component_map_by_ids([p.component_id for p in page]),
            },
        )
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(slz.data))

    @swagger_auto_schema(
        request_body=serializers.BatchAppComponentPermissionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["ESB.Permission"],
    )
    @transaction.atomic
    def renew(self, request, *args, **kwargs):
        """
        权限续期
        """
        slz = serializers.BatchAppComponentPermissionSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppComponentPermission.objects.renew_permission_by_ids(
            ids=data["ids"],
            expire_days=DEFAULT_PERMISSION_EXPIRE_DAYS,
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        request_body=serializers.BatchAppComponentPermissionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["ESB.Permission"],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        权限删除
        """
        slz = serializers.BatchAppComponentPermissionSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppComponentPermission.objects.delete_permission_by_ids(
            ids=data["ids"],
        )

        return OKJsonResponse("OK")
