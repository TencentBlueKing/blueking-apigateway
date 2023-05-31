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

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.access_strategy.ip_group import serializers
from apigateway.apps.access_strategy.models import AccessStrategy, IPGroup
from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.common.error_codes import error_codes
from apigateway.core.signals import reversion_update_signal
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema
from apigateway.utils.time import now_datetime


class IPGroupViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.IPGroupSLZ
    lookup_field = "id"

    def get_queryset(self):
        return IPGroup.objects.filter(api=self.request.gateway).order_by("-updated_time")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.IPGroupSLZ, tags=["AccessStrategy"]
    )
    def create(self, request, *args, **kwargs):
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
            op_object_type=OpObjectTypeEnum.IP_GROUP.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment="创建IP分组",
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.IPGroupQuerySLZ,
        responses={status.HTTP_200_OK: serializers.IPGroupSLZ(many=True)},
        tags=["AccessStrategy"],
    )
    def list(self, request, gateway_id, *args, **kwargs):
        slz = serializers.IPGroupQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        if data.get("query"):
            queryset = queryset.filter(name__contains=data["query"])

        queryset = queryset.order_by(data.get("order_by") or "-id")

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["AccessStrategy"])
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
            updated_time=now_datetime(),
        )

        # send signal
        reversion_update_signal.send(sender=IPGroup, instance_id=slz.instance.id, action="update")

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.IP_GROUP.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment="更新IP分组",
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(tags=["AccessStrategy"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OKJsonResponse("OK", data=serializer.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["AccessStrategy"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        # 如果IP分组已经绑定了策略，不允许删除
        self._check_ipgroup_can_be_deleted(request.gateway, instance_id)

        instance.delete()

        # send signal
        reversion_update_signal.send(sender=IPGroup, instance_id=instance_id, action="destroy")

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.IP_GROUP.value,
            op_object_id=instance_id,
            op_object=instance.name,
            comment="删除IP分组",
        )

        return OKJsonResponse("OK")

    def _check_ipgroup_can_be_deleted(self, api, ip_group_id):
        strategy_queryset = AccessStrategy.objects.filter_strategy(
            api=api,
            _type=AccessStrategyTypeEnum.IP_ACCESS_CONTROL.value,
        )
        for strategy in strategy_queryset:
            if ip_group_id in strategy.config["ip_group_list"]:
                raise error_codes.FORBIDDEN.format(f'请先将IP分组从访问策略"{strategy.name}"中去除，再删除该IP分组', replace=True)
