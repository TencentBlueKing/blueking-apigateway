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
from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppPermissionRecord,
    AppResourcePermission,
)
from apigateway.apps.permission.tasks import send_mail_for_perm_handle
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.resource import ResourceHandler
from apigateway.core.models import Resource
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse

from .filters import (
    AppGatewayPermissionFilter,
    AppPermissionApplyFilter,
    AppPermissionRecordFilter,
    AppResourcePermissionFilter,
)
from .serializers import (
    AppPermissionApplyApprovalInputSLZ,
    AppPermissionApplyOutputSLZ,
    AppPermissionExportInputSLZ,
    AppPermissionExportOutputSLZ,
    AppPermissionIDsSLZ,
    AppPermissionInputSLZ,
    AppPermissionOutputSLZ,
    AppPermissionQueryInputSLZ,
    AppPermissionRecordOutputSLZ,
    AppPermissionRenewInputSLZ,
)

logger = logging.getLogger(__name__)


class AppGatewayPermissionQuerySetMixin:
    def get_queryset(self):
        return AppGatewayPermission.objects.filter(gateway=self.request.gateway).order_by("-id")


class AppResourcePermissionQuerySetMixin:
    def get_queryset(self):
        # 仅展示资源存在的权限
        resource_ids = Resource.objects.filter(gateway=self.request.gateway).values_list("id", flat=True)
        return (
            AppResourcePermission.objects.filter(gateway=self.request.gateway, resource_id__in=resource_ids)
            .exclude(bk_app_code=settings.DEFAULT_TEST_APP["bk_app_code"])
            .order_by("-id")
        )


class AppPermissionQuerySetMixin(AppGatewayPermissionQuerySetMixin, AppResourcePermissionQuerySetMixin):
    def get_gateway_queryset(self):
        return AppGatewayPermissionQuerySetMixin.get_queryset(self)

    def get_resource_queryset(self):
        return AppResourcePermissionQuerySetMixin.get_queryset(self)

    def get_app_permissions(self, gateway_queryset, resource_queryset):
        gateway_permissions = [
            {
                "bk_app_code": perm.bk_app_code,
                "expires": perm.expires,
                "grant_dimension": GrantDimensionEnum.API.value,
            }
            for perm in gateway_queryset
        ]
        resource_permission = [
            {
                "bk_app_code": perm.bk_app_code,
                "grant_type": perm.grant_type,
                "resource_id": perm.resource_id,
                "expires": perm.expires,
                "grant_dimension": GrantDimensionEnum.RESOURCE.value,
            }
            for perm in resource_queryset
        ]
        return gateway_permissions + resource_permission


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取应用权限列表",
        query_serializer=AppPermissionQueryInputSLZ(),
        responses={status.HTTP_200_OK: AppPermissionOutputSLZ(many=True)},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionListApi(AppPermissionQuerySetMixin, generics.ListAPIView):
    def get_queryset(self):
        query_params = self.request.query_params
        app_gateway_permissions = AppGatewayPermissionFilter(self.request.GET, queryset=self.get_gateway_queryset()).qs
        # 如果查询维度为资源 或者 授权类型不为 INITIALIZE(网关维度都为INITIALIZE)或者 查询某个资源 都要忽略掉网关维度的
        if (
            query_params.get("grant_dimension") == GrantDimensionEnum.RESOURCE.value
            or (query_params.get("grant_type") and query_params.get("grant_type") != GrantTypeEnum.INITIALIZE.value)
            or query_params.get("resource_id")
        ):
            app_gateway_permissions = []

        app_resource_permissions = AppResourcePermissionFilter(
            self.request.GET, queryset=self.get_resource_queryset()
        ).qs
        if query_params.get("grant_dimension") == GrantDimensionEnum.API.value:
            app_resource_permissions = []

        return self.get_app_permissions(app_gateway_permissions, app_resource_permissions)

    def get(self, request, *args, **kwargs):
        """
        权限列表(gateway+resource)
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        resource_ids = [perm["resource_id"] for perm in page if perm.get("resource_id")]
        resources = Resource.objects.filter(id__in=resource_ids)
        serializer = AppPermissionOutputSLZ(
            page, many=True, context={"resource_map": {resource.id: resource for resource in resources}}
        )
        return self.get_paginated_response(serializer.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="批量续期",
        responses={status.HTTP_201_CREATED: ""},
        request_body=AppPermissionRenewInputSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionRenewApi(generics.CreateAPIView):
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        批量续期
        """
        slz = AppPermissionRenewInputSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        if data["resource_dimension_ids"]:
            AppResourcePermission.objects.renew_by_ids(
                gateway=request.gateway, ids=data["resource_dimension_ids"], expires=data["expire_days"]
            )

        if data["gateway_dimension_ids"]:
            AppGatewayPermission.objects.renew_by_ids(
                gateway=request.gateway, ids=data["gateway_dimension_ids"], expires=data["expire_days"]
            )
        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取有权限的应用列表",
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionAppCodeListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        """获取有权限的应用列表"""

        app_gateway_codes = (
            AppGatewayPermission.objects.filter(gateway=request.gateway)
            .order_by("bk_app_code")
            .values_list("bk_app_code", flat=True)
        )

        app_resource_codes = (
            AppResourcePermission.objects.filter(gateway=request.gateway)
            .order_by("bk_app_code")
            .values_list("bk_app_code", flat=True)
        )

        # 去重
        app_codes = sorted(set(app_gateway_codes) | set(app_resource_codes))
        return OKJsonResponse(data=list(app_codes))


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="网关权限导出",
        request_body=AppPermissionExportInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionExportApi(AppPermissionQuerySetMixin, generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        """
        权限导出
        """
        slz = AppPermissionExportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        gateway_queryset = []
        resource_queryset = []
        if data["export_type"] == ExportTypeEnum.ALL.value:
            gateway_queryset = self.get_gateway_queryset()
            resource_queryset = self.get_resource_queryset()
        elif data["export_type"] == ExportTypeEnum.FILTERED.value:
            resource_queryset = AppResourcePermissionFilter(
                data=data, queryset=self.get_queryset(), request=request
            ).qs
        elif data["export_type"] == ExportTypeEnum.SELECTED.value:
            if data["resource_permission_ids"]:
                resource_queryset = self.get_resource_queryset().filter(id__in=data["resource_permission_ids"])
            if data["gateway_permission_ids"]:
                gateway_queryset = self.get_gateway_queryset().filter(id__in=data["gateway_permission_ids"])

        app_permissions = self.get_app_permissions(gateway_queryset, resource_queryset)

        resource_ids = [perm["resource_id"] for perm in app_permissions if perm.get("resource_id")]
        resources = Resource.objects.filter(id__in=resource_ids)
        slz = AppPermissionExportOutputSLZ(
            app_permissions, many=True, context={"resource_map": {resource.id: resource for resource in resources}}
        )
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
        headers = [
            "bk_app_code",
            "resource_name",
            "resource_path",
            "resource_method",
            "expires",
            "grant_type",
            "grant_dimension",
        ]
        header_row = {
            "bk_app_code": _("蓝鲸应用ID"),
            "resource_name": _("资源名称"),
            "resource_path": _("请求路径"),
            "resource_method": _("请求方法"),
            "expires": _("过期时间"),
            "grant_type": _("授权类型"),
            "grant_dimension": _("授权维度"),
        }

        content = StringIO()
        io_csv = csv.DictWriter(content, fieldnames=headers, extrasaction="ignore")
        io_csv.writerow(header_row)
        io_csv.writerows(data)

        return content.getvalue()


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="资源权限主动授权",
        responses={status.HTTP_201_CREATED: ""},
        request_body=AppPermissionInputSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppResourcePermissionCreateApi(generics.CreateAPIView):
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        主动授权
        """
        slz = AppPermissionInputSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppResourcePermission.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=data["resource_ids"],
            bk_app_code=data["bk_app_code"],
            expire_days=data["expire_days"],
            grant_type=GrantTypeEnum.INITIALIZE.value,
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="资源权限续期",
        responses={status.HTTP_201_CREATED: ""},
        request_body=AppPermissionIDsSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppResourcePermissionRenewApi(generics.CreateAPIView):
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        权限续期
        """
        slz = AppPermissionIDsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppResourcePermission.objects.renew_by_ids(
            gateway=request.gateway, ids=data["ids"], expires=data["expire_days"]
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除资源权限",
        responses={status.HTTP_204_NO_CONTENT: ""},
        query_serializer=AppPermissionIDsSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppResourcePermissionDeleteApi(AppResourcePermissionQuerySetMixin, generics.DestroyAPIView):
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        slz = AppPermissionIDsSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        self.get_queryset().filter(id__in=data["ids"]).delete()
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="网关权限主动授权",
        responses={status.HTTP_201_CREATED: ""},
        request_body=AppPermissionInputSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppGatewayPermissionCreateApi(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        """
        主动授权
        """
        slz = AppPermissionInputSLZ(data=request.data, context={"gateway": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppGatewayPermission.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=data["resource_ids"],
            bk_app_code=data["bk_app_code"],
            expire_days=data["expire_days"],
            grant_type=GrantTypeEnum.INITIALIZE.value,
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="网关权限续期",
        responses={status.HTTP_201_CREATED: ""},
        request_body=AppPermissionIDsSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppGatewayPermissionRenewApi(generics.CreateAPIView):
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        权限续期
        """
        slz = AppPermissionIDsSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        AppGatewayPermission.objects.renew_by_ids(
            gateway=request.gateway, ids=data["ids"], expires=data["expire_days"]
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="网关权限删除",
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=AppPermissionIDsSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppGatewayPermissionDeleteApi(AppGatewayPermissionQuerySetMixin, generics.DestroyAPIView):
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        slz = AppPermissionIDsSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        self.get_queryset().filter(id__in=data["ids"]).delete()
        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


class AppPermissionApplyQuerySetMixin:
    def get_queryset(self):
        return AppPermissionApply.objects.filter(gateway=self.request.gateway).order_by("-id")


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取权限申请单列表",
        responses={status.HTTP_200_OK: AppPermissionApplyOutputSLZ(many=True)},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionApplyListApi(AppPermissionApplyQuerySetMixin, generics.ListAPIView):
    filterset_class = AppPermissionApplyFilter

    def list(self, request, *args, **kwargs):
        """
        获取权限申请单列表
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = AppPermissionApplyOutputSLZ(page, many=True)
        return self.get_paginated_response(serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取权限申请单详情",
        responses={status.HTTP_200_OK: AppPermissionApplyOutputSLZ()},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionApplyRetrieveApi(AppPermissionApplyQuerySetMixin, generics.RetrieveAPIView):
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = AppPermissionApplyOutputSLZ(instance)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取权限申请记录列表",
        responses={status.HTTP_200_OK: AppPermissionRecordOutputSLZ(many=True)},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionRecordListApi(generics.ListAPIView):
    filterset_class = AppPermissionRecordFilter

    def get_queryset(self):
        return (
            AppPermissionRecord.objects.filter(gateway=self.request.gateway)
            .exclude(status=ApplyStatusEnum.PENDING.value)
            .order_by("-handled_time")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        serializer = AppPermissionRecordOutputSLZ(
            page,
            many=True,
            context={
                "resource_id_map": ResourceHandler.get_id_to_resource(gateway_id=request.gateway.id),
            },
        )
        return self.get_paginated_response(serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取权限申请记录详情",
        responses={status.HTTP_200_OK: AppPermissionRecordOutputSLZ()},
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionRecordRetrieveApi(generics.RetrieveAPIView):
    lookup_field = "id"

    def get_queryset(self):
        return AppPermissionRecord.objects.filter(gateway=self.request.gateway).order_by("-handled_time")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = AppPermissionRecordOutputSLZ(
            instance,
            context={
                "resource_id_map": ResourceHandler.get_id_to_resource(gateway_id=request.gateway.id),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="审批操作",
        responses={status.HTTP_201_CREATED: ""},
        request_body=AppPermissionApplyApprovalInputSLZ,
        tags=["WebAPI.Permission"],
    ),
)
class AppPermissionApplyApprovalApi(AppPermissionApplyQuerySetMixin, generics.CreateAPIView):
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

        return OKJsonResponse(status=status.HTTP_201_CREATED)
