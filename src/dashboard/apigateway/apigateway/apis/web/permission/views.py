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
from rest_framework import generics, status

from apigateway.apps.permission.constants import ApplyStatusEnum, GrantTypeEnum
from apigateway.apps.permission.models import (
    AppAPIPermission,
    AppPermissionApply,
    AppPermissionRecord,
    AppResourcePermission,
)
from apigateway.apps.permission.tasks import send_mail_for_perm_handle
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.core.constants import ExportTypeEnum
from apigateway.core.models import Resource
from apigateway.utils.responses import DownloadableResponse, V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

from .filters import (
    AppGatewayPermissionFilter,
    AppPermissionApplyFilter,
    AppPermissionRecordFilter,
    AppResourcePermissionFilter,
)
from .serializers import (
    AppGatewayPermissionOutputSLZ,
    AppPermissionApplyApprovalInputSLZ,
    AppPermissionApplyOutputSLZ,
    AppPermissionExportInputSLZ,
    AppPermissionIDsSLZ,
    AppPermissionInputSLZ,
    AppPermissionRecordOutputSLZ,
    AppResourcePermissionOutputSLZ,
)

logger = logging.getLogger(__name__)


class AppResourcePermissionQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()

        # 仅展示资源存在的权限
        resource_ids = Resource.objects.filter(api=self.request.gateway).values_list("id", flat=True)
        return queryset.filter(api=self.request.gateway, resource_id__in=resource_ids)


class AppResourcePermissionListCreateApi(AppResourcePermissionQuerySetMixin, generics.ListCreateAPIView):
    queryset = AppResourcePermission.objects.order_by("-id")
    filterset_class = AppResourcePermissionFilter

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: AppResourcePermissionOutputSLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """
        权限列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = AppResourcePermissionOutputSLZ(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=AppPermissionInputSLZ,
        tags=["Permission"],
    )
    def create(self, request, *args, **kwargs):
        """
        主动授权
        """
        slz = AppPermissionInputSLZ(data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppResourcePermission.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=data["resource_ids"],
            bk_app_code=data["bk_app_code"],
            expire_days=data["expire_days"],
            grant_type=GrantTypeEnum.INITIALIZE.value,
        )

        return V1OKJsonResponse("OK")


class AppResourcePermissionExportApi(AppResourcePermissionQuerySetMixin, generics.CreateAPIView):
    queryset = AppResourcePermission.objects.order_by("-id")

    @swagger_auto_schema(
        request_body=AppPermissionExportInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Permission"],
    )
    def create(self, request, *args, **kwargs):
        """
        权限导出
        """
        slz = AppPermissionExportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        if data["export_type"] == ExportTypeEnum.ALL.value:
            queryset = self.get_queryset()
        elif data["export_type"] == ExportTypeEnum.FILTERED.value:
            queryset = AppResourcePermissionFilter(data=data, queryset=self.get_queryset(), request=request).qs
        elif data["export_type"] == ExportTypeEnum.SELECTED.value:
            queryset = self.get_queryset().filter(id__in=data["permission_ids"])

        slz = AppResourcePermissionOutputSLZ(queryset, many=True)
        content = self._get_csv_content(slz.data)

        response = DownloadableResponse(content, filename=f"{self.request.gateway.name}-permissions.csv")
        # FIXME: change to export excel directly, while the exported csv file copy from mac to windows is not ok now!
        # use utf-8-sig for windows
        response.charset = "utf-8-sig" if "windows" in request.headers.get("User-Agent", "").lower() else "utf-8"

        return response

    def _get_csv_content(self, data: List[Any]) -> str:
        """
        将筛选出的权限数据，整理为 csv 格式内容
        """
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


class AppResourcePermissionAppCodeListApi(generics.ListAPIView):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """获取有权限的应用列表"""

        app_codes = list(
            AppResourcePermission.objects.filter(api=request.gateway)
            .order_by("bk_app_code")
            .distinct()
            .values_list("bk_app_code", flat=True)
        )
        return V1OKJsonResponse("OK", data=app_codes)


class AppResourcePermissionRenewApi(generics.CreateAPIView):
    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=AppPermissionIDsSLZ, tags=["Permission"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        权限续期
        """
        slz = AppPermissionIDsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppResourcePermission.objects.renew_by_ids(
            gateway=request.gateway,
            ids=data["ids"],
        )

        return V1OKJsonResponse("OK")


class AppResourcePermissionDeleteApi(AppResourcePermissionQuerySetMixin, generics.CreateAPIView):
    queryset = AppResourcePermission.objects.order_by("-id")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=AppPermissionIDsSLZ, tags=["Permission"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = AppPermissionIDsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        self.get_queryset().filter(id__in=data["ids"]).delete()
        return V1OKJsonResponse("OK")


class AppGatewayPermissionQuerySetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(api=self.request.gateway)


class AppGatewayPermissionListCreateApi(AppGatewayPermissionQuerySetMixin, generics.ListCreateAPIView):
    queryset = AppAPIPermission.objects.order_by("-id")
    filterset_class = AppGatewayPermissionFilter

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: AppGatewayPermissionOutputSLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """
        权限列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = AppGatewayPermissionOutputSLZ(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=AppPermissionInputSLZ,
        tags=["Permission"],
    )
    def create(self, request, *args, **kwargs):
        """
        主动授权
        """
        slz = AppPermissionInputSLZ(data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppAPIPermission.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=data["resource_ids"],
            bk_app_code=data["bk_app_code"],
            expire_days=data["expire_days"],
            grant_type=GrantTypeEnum.INITIALIZE.value,
        )

        return V1OKJsonResponse("OK")


class AppGatewayPermissionExportApi(AppGatewayPermissionQuerySetMixin, generics.CreateAPIView):
    queryset = AppAPIPermission.objects.order_by("-id")

    @swagger_auto_schema(
        request_body=AppPermissionExportInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Permission"],
    )
    def create(self, request, *args, **kwargs):
        """
        权限导出
        """
        slz = AppPermissionExportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        if data["export_type"] == ExportTypeEnum.ALL.value:
            queryset = self.get_queryset()
        elif data["export_type"] == ExportTypeEnum.FILTERED.value:
            queryset = AppGatewayPermissionFilter(data=data, queryset=self.get_queryset(), request=request).qs
        elif data["export_type"] == ExportTypeEnum.SELECTED.value:
            queryset = self.get_queryset().filter(id__in=data["permission_ids"])

        slz = AppGatewayPermissionOutputSLZ(queryset, many=True)
        content = self._get_csv_content(slz.data)

        response = DownloadableResponse(content, filename=f"{self.request.gateway.name}-permissions.csv")
        # FIXME: change to export excel directly, while the exported csv file copy from mac to windows is not ok now!
        # use utf-8-sig for windows
        response.charset = "utf-8-sig" if "windows" in request.headers.get("User-Agent", "").lower() else "utf-8"

        return response

    def _get_csv_content(self, data: List[Any]) -> str:
        """
        将筛选出的权限数据，整理为 csv 格式内容
        """
        data = sorted(data, key=lambda x: x["bk_app_code"])
        headers = ["bk_app_code", "expires", "grant_type"]
        header_row = {
            "bk_app_code": _("蓝鲸应用ID"),
            "expires": _("过期时间"),
            "grant_type": _("授权类型"),
        }

        content = StringIO()
        io_csv = csv.DictWriter(content, fieldnames=headers, extrasaction="ignore")
        io_csv.writerow(header_row)
        io_csv.writerows(data)

        return content.getvalue()


class AppGatewayPermissionAppCodeListApi(generics.ListAPIView):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """获取有权限的应用列表"""

        app_codes = list(
            AppAPIPermission.objects.filter(api=request.gateway)
            .order_by("bk_app_code")
            .distinct()
            .values_list("bk_app_code", flat=True)
        )
        return V1OKJsonResponse("OK", data=app_codes)


class AppGatewayPermissionRenewApi(generics.CreateAPIView):
    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=AppPermissionIDsSLZ, tags=["Permission"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        权限续期
        """
        slz = AppPermissionIDsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppAPIPermission.objects.renew_by_ids(
            gateway=request.gateway,
            ids=data["ids"],
        )

        return V1OKJsonResponse("OK")


class AppGatewayPermissionDeleteApi(AppGatewayPermissionQuerySetMixin, generics.CreateAPIView):
    queryset = AppAPIPermission.objects.order_by("-id")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=AppPermissionIDsSLZ, tags=["Permission"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = AppPermissionIDsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        self.get_queryset().filter(id__in=data["ids"]).delete()
        return V1OKJsonResponse("OK")


class AppPermissionApplyQuerySetMixin:
    def get_queryset(self):
        return AppPermissionApply.objects.filter(api=self.request.gateway).order_by("-id")


class AppPermissionApplyListApi(AppPermissionApplyQuerySetMixin, generics.ListAPIView):
    filterset_class = AppPermissionApplyFilter

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: AppPermissionApplyOutputSLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        """
        获取权限申请单列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        page = self.paginate_queryset(queryset)

        serializer = AppPermissionApplyOutputSLZ(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))


class AppPermissionApplyRetrieveApi(AppPermissionApplyQuerySetMixin, generics.RetrieveAPIView):
    lookup_field = "id"

    @swagger_auto_schema(tags=["Permission"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = AppPermissionApplyOutputSLZ(instance)
        return V1OKJsonResponse("OK", data=slz.data)


class AppPermissionRecordListApi(generics.ListAPIView):
    filterset_class = AppPermissionRecordFilter

    def get_queryset(self):
        return (
            AppPermissionRecord.objects.filter(api=self.request.gateway)
            .exclude(status=ApplyStatusEnum.PENDING.value)
            .order_by("-handled_time")
        )

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: AppPermissionRecordOutputSLZ(many=True)},
        tags=["Permission"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = AppPermissionRecordOutputSLZ(
            page,
            many=True,
            context={
                "resource_id_map": Resource.objects.filter_id_object_map(request.gateway.id),
            },
        )
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))


class AppPermissionRecordRetrieveApi(generics.RetrieveAPIView):
    lookup_field = "id"

    def get_queryset(self):
        return AppPermissionRecord.objects.filter(api=self.request.gateway).order_by("-handled_time")

    @swagger_auto_schema(tags=["Permission"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = AppPermissionRecordOutputSLZ(
            instance,
            context={
                "resource_id_map": Resource.objects.filter_id_object_map(request.gateway.id),
            },
        )
        return V1OKJsonResponse("OK", data=slz.data)


class AppPermissionApplyApprovalApi(AppPermissionApplyQuerySetMixin, generics.CreateAPIView):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=AppPermissionApplyApprovalInputSLZ, tags=["Permission"]
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        审批操作
        """
        slz = AppPermissionApplyApprovalInputSLZ(data=request.data)
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

        return V1OKJsonResponse("OK")
