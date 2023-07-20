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
import csv
import logging
from io import StringIO
from typing import Any, List

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.permission import serializers
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.helpers import AppPermissionHelper, PermissionDimensionManager
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.apps.permission.tasks import send_mail_for_perm_handle
from apigateway.core.constants import ExportTypeEnum
from apigateway.core.models import Resource
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

logger = logging.getLogger(__name__)


class AppPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AppPermissionListSLZ

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AppPermissionQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionListSLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """
        权限列表
        """
        slz = serializers.AppPermissionQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permission_model = AppPermissionHelper().get_permission_model(data["dimension"])
        queryset = permission_model.objects.filter_permission(
            gateway=request.gateway,
            bk_app_code=data.get("bk_app_code"),
            query=data.get("query"),
            grant_type=data["grant_type"],
            resource_ids=[data["resource_id"]] if data.get("resource_id") else None,
            order_by=data.get("order_by") or "-id",
            fuzzy=True,
        )

        page = self.paginate_queryset(queryset)

        page = permission_model.objects.add_extend_data_for_representation(page)

        serializer = serializers.AppPermissionListSLZ(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=serializers.AppPermissionCreateSLZ,
        tags=["Permission"],
    )
    def create(self, request, *args, **kwargs):
        """
        主动授权
        """
        slz = serializers.AppPermissionCreateSLZ(data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permission_model = AppPermissionHelper().get_permission_model(data["dimension"])
        permission_model.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=data["resource_ids"],
            bk_app_code=data["bk_app_code"],
            expire_days=data["expire_days"],
            grant_type=GrantTypeEnum.INITIALIZE.value,
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        request_body=serializers.PermissionExportConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Permission"],
    )
    def export_permissions(self, request, *args, **kwargs):
        slz = serializers.PermissionExportConditionSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        permission_model = AppPermissionHelper().get_permission_model(data["dimension"])

        if data["export_type"] == ExportTypeEnum.ALL.value:
            queryset = permission_model.objects.filter_permission(gateway=request.gateway)
        elif data["export_type"] == ExportTypeEnum.FILTERED.value:
            queryset = permission_model.objects.filter_permission(
                gateway=request.gateway,
                bk_app_code=data.get("bk_app_code"),
                grant_type=data.get("grant_type"),
                resource_ids=[data["resource_id"]] if data.get("resource_id") else None,
                query=data.get("query"),
                fuzzy=True,
            )
        elif data["export_type"] == ExportTypeEnum.SELECTED.value:
            queryset = permission_model.objects.filter_permission(
                gateway=request.gateway,
                ids=data["permission_ids"],
            )

        queryset = permission_model.objects.add_extend_data_for_representation(queryset)
        slz = serializers.AppPermissionListSLZ(queryset, many=True)
        content = self._get_csv_content(data["dimension"], slz.data)

        response = DownloadableResponse(content, filename=f"{self.request.gateway.name}-permissions.csv")
        # FIXME: change to export excel directly, while the exported csv file copy from mac to windows is not ok now!
        # use utf-8-sig for windows
        response.charset = "utf-8-sig" if "windows" in request.headers.get("User-Agent", "").lower() else "utf-8"

        return response

    @swagger_auto_schema(
        query_serializer=serializers.PermissionAppQuerySLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Permission"],
    )
    def get_bk_app_codes(self, request, *args, **kwargs):
        """获取有权限的应用列表"""
        slz = serializers.PermissionAppQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        permission_model = AppPermissionHelper().get_permission_model(data["dimension"])

        app_codes = list(
            permission_model.objects.filter(api=request.gateway)
            .order_by("bk_app_code")
            .distinct()
            .values_list("bk_app_code", flat=True)
        )
        return OKJsonResponse("OK", data=app_codes)

    def _get_csv_content(self, dimension: str, data: List[Any]) -> str:
        """
        将筛选出的权限数据，整理为 csv 格式内容
        """
        if dimension == GrantDimensionEnum.API.value:
            data = sorted(data, key=lambda x: x["bk_app_code"])
            headers = ["bk_app_code", "expires", "grant_type"]
            header_row = {
                "bk_app_code": _("蓝鲸应用ID"),
                "expires": _("过期时间"),
                "grant_type": _("授权类型"),
            }

        else:
            data = sorted(data, key=lambda x: (x["bk_app_code"], x["resource_name"]))
            headers = ["bk_app_code", "resource_name", "resource_path", "resource_method", "expires", "grant_type"]
            header_row = {
                "bk_app_code": _("蓝鲸应用ID"),
                "resource_name": _("资源名称"),
                "resource_path": _("请求路径"),
                "resource_method": _("请求方法"),
                "expires": _("过期时间"),
                "grant_type": _("授权类型"),
            }

        content = StringIO()
        io_csv = csv.DictWriter(content, fieldnames=headers, extrasaction="ignore")
        io_csv.writerow(header_row)
        io_csv.writerows(data)

        return content.getvalue()


class AppPermissionBatchViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AppPermissionBatchSLZ

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.AppPermissionBatchSLZ, tags=["Permission"]
    )
    @transaction.atomic
    def renew(self, request, *args, **kwargs):
        """
        权限续期
        """
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permission_model = AppPermissionHelper().get_permission_model(data["dimension"])
        permission_model.objects.renew_permission(
            gateway=request.gateway,
            ids=data["ids"],
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.AppPermissionBatchSLZ, tags=["Permission"]
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permission_model = AppPermissionHelper().get_permission_model(data["dimension"])
        permission_model.objects.delete_permission(
            gateway=request.gateway,
            ids=data["ids"],
        )

        return OKJsonResponse("OK")


class BaseAppPermissionApplyViewSet(viewsets.ModelViewSet):
    lookup_field = "id"

    def get_queryset(self):
        return AppPermissionApply.objects.filter(api=self.request.gateway).order_by("-id")


class AppPermissionApplyViewSet(BaseAppPermissionApplyViewSet):
    serializer_class = serializers.AppPermissionApplySLZ

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AppPermissionApplyQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionApplySLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """
        获取权限申请单列表
        """
        slz = serializers.AppPermissionApplyQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        queryset = AppPermissionApply.objects.filter_apply(
            queryset,
            bk_app_code=data.get("bk_app_code"),
            applied_by=data.get("applied_by"),
            grant_dimension=data.get("grant_dimension"),
            fuzzy=True,
        )

        page = self.paginate_queryset(queryset)

        serializer = serializers.AppPermissionApplySLZ(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(tags=["Permission"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse("OK", data=slz.data)


class AppPermissionApplyBatchViewSet(BaseAppPermissionApplyViewSet):
    serializer_class = serializers.AppPermissionApplyBatchSLZ

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.AppPermissionApplyBatchSLZ, tags=["Permission"]
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        审批操作
        """
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        part_resource_ids = data.get("part_resource_ids", {})

        queryset = self.get_queryset().filter(id__in=data["ids"])

        for apply in queryset:
            manager = PermissionDimensionManager.get_manager(apply.grant_dimension)
            record = manager.handle_permission_apply(
                gateway=request.gateway,
                apply=apply,
                status=data["status"],
                comment=data["comment"],
                handled_by=request.user.username,
                part_resource_ids=part_resource_ids.get(f"{apply.id}"),
            )

            try:
                apply_async_on_commit(send_mail_for_perm_handle, args=[record.id])
            except Exception:
                logger.exception("send mail to applicant fail. record_id=%s", record.id)

        # 删除申请单
        queryset.delete()

        return OKJsonResponse("OK")


class AppPermissionRecordViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AppPermissionRecordSLZ
    lookup_field = "id"

    def get_queryset(self):
        return AppPermissionRecord.objects.filter(api=self.request.gateway).order_by("-handled_time")

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AppPermissionRecordQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionRecordSLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.AppPermissionRecordQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        queryset = AppPermissionRecord.objects.filter_record(
            queryset,
            bk_app_code=data.get("bk_app_code"),
            handled_time_start=data.get("time_start"),
            handled_time_end=data.get("time_end"),
            grant_dimension=data.get("grant_dimension"),
            fuzzy=True,
        )
        queryset = queryset.exclude(status=ApplyStatusEnum.PENDING.value)
        page = self.paginate_queryset(queryset)

        serializer = serializers.AppPermissionRecordSLZ(
            page,
            many=True,
            context={
                "resource_id_map": Resource.objects.filter_id_object_map(request.gateway.id),
            },
        )
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(tags=["Permission"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.AppPermissionRecordSLZ(
            instance,
            context={
                "resource_id_map": Resource.objects.filter_id_object_map(request.gateway.id),
            },
        )
        return OKJsonResponse("OK", data=slz.data)
