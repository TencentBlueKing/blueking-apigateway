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

from apigateway.apps.access_strategy.access_strategy import serializers
from apigateway.apps.access_strategy.models import AccessStrategy
from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.core.signals import reversion_update_signal
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema


class AccessStrategyViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.AccessStrategySLZ
    lookup_field = "id"

    def get_queryset(self):
        return AccessStrategy.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.AccessStrategySLZ, tags=["AccessStrategy"]
    )
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.AccessStrategyQuerySLZ,
        responses={status.HTTP_200_OK: serializers.AccessStrategyListSLZ(many=True)},
        tags=["AccessStrategy"],
    )
    def list(self, request, gateway_id, *args, **kwargs):
        slz = serializers.AccessStrategyQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AccessStrategy.objects.filter_strategy(
            api=self.request.gateway,
            _type=data.get("type"),
            query=data.get("query"),
            order_by=data.get("order_by") or "-id",
            fuzzy=True,
        )

        page = self.paginate_queryset(queryset)
        serializer = serializers.AccessStrategyListSLZ(page, many=True)
        return OKJsonResponse("OK", data=self.paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["AccessStrategy"])
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(tags=["AccessStrategy"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OKJsonResponse("OK", data=serializer.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["AccessStrategy"])
    def destroy(self, request, gateway_id, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        # 删除关联数据
        AccessStrategy.objects.delete_strategies([instance.id])

        # send signal
        reversion_update_signal.send(sender=AccessStrategy, instance_id=instance_id, action="destroy")

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.ACCESS_STRATEGY.value,
            op_object_id=instance_id,
            op_object=instance.name,
            comment="删除访问策略",
        )

        return OKJsonResponse("OK")
