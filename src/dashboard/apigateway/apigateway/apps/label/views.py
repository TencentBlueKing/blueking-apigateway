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
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.label import serializers
from apigateway.apps.label.models import APILabel
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema
from apigateway.utils.time import now_datetime


class APILabelViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.APILabelSLZ
    lookup_field = "id"

    def get_queryset(self):
        return APILabel.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.APILabelQuerySLZ,
        responses={status.HTTP_200_OK: serializers.APILabelSLZ(many=True)},
        tags=["APILabels"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.APILabelQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        if data.get("name"):
            queryset = queryset.filter(name__contains=data["name"])

        # order
        queryset = queryset.order_by(data.get("order_by") or "-id")

        page = self.paginate_queryset(queryset)

        serializer = serializers.APILabelSLZ(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.APILabelSLZ()}, tags=["APILabels"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.APILabelSLZ, tags=["APILabels"])
    def create(self, request, gateway_id):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
            created_time=now_datetime(),
            updated_time=now_datetime(),
        )

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.API_LABEL.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment=_("创建网关标签"),
        )

        return OKJsonResponse("OK", data={"id": slz.instance.id})

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.APILabelSLZ, tags=["APILabels"])
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
            updated_time=now_datetime(),
        )

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.API_LABEL.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment=_("更新网关标签"),
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["APILabels"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        instance.delete()

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.API_LABEL.value,
            op_object_id=instance_id,
            op_object=instance.name,
            comment=_("删除网关标签"),
        )

        return OKJsonResponse("OK")
