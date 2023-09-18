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
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.biz.backend import BackendHandler
from apigateway.common.audit.shortcuts import record_audit_log
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Backend, BackendConfig, Proxy
from apigateway.utils.responses import OKJsonResponse

from .filters import BackendFilter
from .serializers import BackendInputSLZ, BackendListOutputSLZ, BackendRetrieveOutputSLZ


class BackendQuerySetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(gateway=self.request.gateway)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: BackendListOutputSLZ(many=True)},
        tags=["WebAPI.Backend"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""},
        request_body=BackendInputSLZ,
        tags=["WebAPI.Backend"],
    ),
)
class BackendListCreateApi(BackendQuerySetMixin, generics.ListCreateAPIView):
    queryset = Backend.objects.order_by("id")
    serializer_class = BackendListOutputSLZ
    filterset_class = BackendFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            backend_ids = [backend.id for backend in page]
            serializer = BackendListOutputSLZ(
                page, many=True, context={"resource_count": Proxy.objects.get_backend_resource_count(backend_ids)}
            )
            return self.get_paginated_response(serializer.data)

        backend_ids = [backend.id for backend in queryset]
        serializer = BackendListOutputSLZ(
            page, many=True, context={"resource_count": Proxy.objects.get_backend_resource_count(backend_ids)}
        )
        return OKJsonResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建后端服务
        """
        slz = BackendInputSLZ(data=request.data, context={"gateway": request.gateway})
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


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: BackendRetrieveOutputSLZ()},
        tags=["WebAPI.Backend"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        request_body=BackendInputSLZ,
        tags=["WebAPI.Backend"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Backend"],
    ),
)
class BackendRetrieveUpdateDestroyApi(BackendQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    serializer_class = BackendInputSLZ
    queryset = Backend.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BackendRetrieveOutputSLZ(instance)
        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance=instance, data=request.data, context={"gateway": request.gateway})
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

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 通过stage/resource关联数据校验是否能删除
        if not BackendHandler.deletable(instance):
            raise error_codes.FAILED_PRECONDITION.format(_("请先下线后端服务，然后再删除。"))

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
