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
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.biz.backend import BackendHandler
from apigateway.core.models import Backend, BackendConfig
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema

from .filters import BackendFilter
from .serializers import BackendInputSLZ, BackendListOutputSLZ, BackendRetrieveOutputSLZ


class BackendQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(gateway=self.request.gateway)


class BackendListCreateApi(BackendQuerySetMixin, generics.ListCreateAPIView):
    queryset = Backend.objects.order_by("-id")
    serializer_class = BackendListOutputSLZ
    filterset_class = BackendFilter

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        responses={status.HTTP_200_OK: BackendListOutputSLZ(many=True)},
        tags=["Backend"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return OKJsonResponse(data=serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        request_body=BackendInputSLZ,
        tags=["Backend"],
    )
    def create(self, request, *args, **kwargs):
        """
        创建后端服务
        """
        slz = BackendInputSLZ(data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        backend = BackendHandler.create(data, request.user.username)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.BACKEND.value,
            op_object_id=backend.id,
            op_object=backend.name,
            comment=_("创建后端服务"),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


class BackendRetrieveUpdateDestroyApi(BackendQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    queryset = Backend.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: BackendRetrieveOutputSLZ()},
        tags=["Backend"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BackendRetrieveOutputSLZ(instance)
        return OKJsonResponse(data=serializer.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        request_body=BackendInputSLZ,
        tags=["Backend"],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = BackendInputSLZ(instance=instance, data=request.data, context={"api": request.gateway})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        backend = BackendHandler.update(instance, data, request.user.username)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.BACKEND.value,
            op_object_id=backend.id,
            op_object=backend.name,
            comment=_("更新后端服务"),
        )

        return OKJsonResponse()

    @swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["Backend"],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # TODO 通过stage/resource关联数据校验是否能删除

        BackendConfig.objects.filter(backend=instance).delete()
        instance.delete()

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.BACKEND.value,
            op_object_id=instance.id,
            op_object=instance.name,
            comment=_("删除后端服务"),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
