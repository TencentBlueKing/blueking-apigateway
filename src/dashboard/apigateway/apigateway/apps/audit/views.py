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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.audit import serializers
from apigateway.apps.audit.models import AuditEventLog
from apigateway.utils.responses import V1OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class AuditEventLogViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AuditEventLogSLZ
    lookup_field = "id"

    def get_queryset(self):
        # 过滤网关数据
        return AuditEventLog.objects.filter(op_object_group=str(self.request.gateway.id)).order_by("-id")

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AuditEventLogQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AuditEventLogSLZ(many=True)},
        tags=["Audit"],
    )
    def list(self, request, gateway_id, *args, **kwargs):
        slz = serializers.AuditEventLogQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        queryset = AuditEventLog.objects.filter_log(
            queryset,
            time_start=data.get("time_start"),
            time_end=data.get("time_end"),
            op_object_type=data.get("op_object_type"),
            op_type=data.get("op_type"),
            username=data.get("username"),
        )

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return V1OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))
