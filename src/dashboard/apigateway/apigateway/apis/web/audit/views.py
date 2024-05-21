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
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.models import AuditEventLog
from apigateway.iam.constants import ActionEnum

from .serializers import AuditEventLogOutputSLZ, AuditEventLogQueryInputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=AuditEventLogQueryInputSLZ,
        responses={status.HTTP_200_OK: AuditEventLogOutputSLZ(many=True)},
        operation_description="操作审计列表",
        tags=["WebAPI.Audit"],
    ),
)
class AuditEventLogListApi(generics.ListAPIView):
    method_permission = {
        "get": ActionEnum.VIEW_AUDIT.value,
    }

    serializer_class = AuditEventLogOutputSLZ
    lookup_field = "id"

    def get_queryset(self):
        # 过滤网关数据
        return AuditEventLog.objects.filter(op_object_group=str(self.request.gateway.id)).order_by("-id")

    def list(self, request, gateway_id, *args, **kwargs):
        slz = AuditEventLogQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        time_start = data.get("time_start")
        time_end = data.get("time_end")
        keyword = data.get("keyword")
        op_object_type = data.get("op_object_type")
        op_type = data.get("op_type")
        op_object = data.get("op_object")
        username = data.get("username")

        queryset = self.get_queryset()
        if time_start:
            queryset = queryset.filter(op_time__gte=time_start)
        if time_end:
            queryset = queryset.filter(op_time__lte=time_end)

        # fuzzy search by keyword
        if keyword:
            queryset = queryset.filter(Q(username__icontains=keyword) | Q(op_object__icontains=keyword))

        # filter by other fields
        if op_object_type:
            queryset = queryset.filter(op_object_type=op_object_type)
        if op_type:
            queryset = queryset.filter(op_type=op_type)
        if op_object:
            queryset = queryset.filter(op_object__icontains=op_object)
        if username:
            queryset = queryset.filter(username=username)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
