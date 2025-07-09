# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.v2.permissions import OpenAPIV2Permission
from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord, ComponentSystem, ESBChannel
from apigateway.biz.esb.permissions import ComponentPermissionManager
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway
from apigateway.utils.responses import OKJsonResponse

from . import serializers_esb as serializers
from .serializers import GatewayAppPermissionApplyCreateOutputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.EsbSystemListInputSLZ,
        responses={status.HTTP_200_OK: serializers.EsbSystemListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbSystemListApi(generics.ListAPIView):
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

    def list(self, request, *args, **kwargs):
        slz = serializers.EsbSystemListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = self._filter_active_and_public_systems(boards=slz.validated_data["boards"])

        slz = serializers.EsbSystemListOutputSLZ(queryset.order_by("board", "name"), many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.EsbPermissionComponentListInputSLZ,
        responses={status.HTTP_200_OK: serializers.EsbPermissionComponentListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbPermissionComponentListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.EsbPermissionComponentListOutputSLZ

    def list(self, request, *args, **kwargs):
        system_id = self.kwargs["system_id"]

        slz = serializers.EsbPermissionComponentListInputSLZ(data=request.query_params)
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


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建申请资源权限的申请单据",
        request_body=serializers.EsbAppPermissionApplyCreateInputSLZ,
        responses={status.HTTP_201_CREATED: GatewayAppPermissionApplyCreateOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbAppPermissionApplyCreateApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.EsbAppPermissionApplyCreateInputSLZ

    @transaction.atomic
    def create(self, request, system_id: int, *args, **kwargs):
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

        return OKJsonResponse(
            status=status.HTTP_201_CREATED,
            data={
                "record_id": record.id,
            },
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="权限续期",
        request_body=serializers.EsbAppPermissionRenewInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbAppPermissionRenewPutApi(generics.CreateAPIView):
    """
    权限续期
    """

    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.EsbAppPermissionRenewInputSLZ

    def post(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ComponentPermissionManager.get_manager()
        manager.renew_permission(
            data["target_app_code"],
            data["component_ids"],
            data["expire_days"],
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.EsbAppPermissionListInputSLZ,
        responses={status.HTTP_200_OK: serializers.EsbAppPermissionOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbAppPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        """已申请权限列表"""
        slz = serializers.EsbAppPermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ComponentPermissionManager.get_manager()
        component_permissions = manager.list_applied_permissions(
            data["target_app_code"],
            data.get("expire_days_range"),
        )

        slz = serializers.EsbAppPermissionOutputSLZ(component_permissions, many=True)
        output_data = sorted(slz.data, key=operator.itemgetter("system_name", "name"))
        return OKJsonResponse(data=output_data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.EsbAppPermissionApplyRecordListInputSLZ,
        responses={status.HTTP_200_OK: serializers.EsbAppPermissionApplyRecordListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbAppPermissionApplyRecordListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.EsbAppPermissionApplyRecordListInputSLZ

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

        slz = serializers.EsbAppPermissionApplyRecordListOutputSLZ(page, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.EsbAppPermissionApplyRecordRetrieveInputSLZ,
        responses={status.HTTP_200_OK: serializers.EsbAppPermissionApplyRecordRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class EsbAppPermissionApplyRecordRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.EsbAppPermissionApplyRecordRetrieveInputSLZ

    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    def get_object(self):
        record_id = self.kwargs["record_id"]

        slz = serializers.EsbAppPermissionApplyRecordRetrieveInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        try:
            return AppPermissionApplyRecord.objects.get(bk_app_code=data["target_app_code"], id=record_id)
        except AppPermissionApplyRecord.DoesNotExist:
            raise error_codes.NOT_FOUND

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        manager = ComponentPermissionManager.get_manager()
        manager.patch_permission_apply_records([instance])

        slz = serializers.EsbAppPermissionApplyRecordRetrieveOutputSLZ(instance)
        return OKJsonResponse(data=slz.data)
