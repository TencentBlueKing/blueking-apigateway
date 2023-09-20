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
from rest_framework import status, viewsets

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.micro_gateway import serializers
from apigateway.apps.micro_gateway.constants import MicroGatewayCreateWayEnum
from apigateway.apps.micro_gateway.handlers import MicroGatewayHandlerFactory
from apigateway.common.audit.shortcuts import record_audit_log
from apigateway.core.models import MicroGateway, Stage
from apigateway.utils.access_token import get_user_access_token_from_request
from apigateway.utils.responses import OKJsonResponse


class MicroGatewayViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.MicroGatewaySLZ
    lookup_field = "id"

    def get_queryset(self):
        return MicroGateway.objects.filter(gateway=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.MicroGatewaySLZ, tags=["MicroGateway"]
    )
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 部署微网关实例
        create_way = MicroGatewayCreateWayEnum(slz.validated_data["create_way"])
        MicroGatewayHandlerFactory.get_handler(create_way).deploy(
            slz.instance.id, get_user_access_token_from_request(request), request.user.username
        )

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.CREATE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.MICRO_GATEWAY.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment=_("创建微网关实例"),
        )

        return OKJsonResponse(data={"id": slz.instance.id})

    @swagger_auto_schema(
        query_serializer=serializers.QueryMicroGatewaySLZ,
        responses={status.HTTP_200_OK: serializers.ListMicroGatewaySLZ(many=True)},
        tags=["MicroGateway"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.QueryMicroGatewaySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = self.get_queryset()
        if data.get("name"):
            queryset = queryset.filter(name__contains=data["name"])

        queryset = queryset.order_by(data.get("order_by") or "-updated_time")

        page = self.paginate_queryset(queryset)
        slz = serializers.ListMicroGatewaySLZ(
            page,
            many=True,
            context={
                "micro_gateway_id_to_stage_fields": Stage.objects.get_micro_gateway_id_to_fields(
                    self.request.gateway.id
                )
            },
        )

        return self.get_paginated_response(slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""}, request_body=serializers.UpdateMicroGatewaySLZ(), tags=["MicroGateway"]
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = serializers.UpdateMicroGatewaySLZ(
            instance,
            data=request.data,
            context={"request": self.request},
        )
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        # 更新微网关实例
        if slz.validated_data["need_deploy"]:
            MicroGatewayHandlerFactory.get_handler(MicroGatewayCreateWayEnum.NEED_DEPLOY).deploy(
                slz.instance.id, get_user_access_token_from_request(request), request.user.username
            )

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.MICRO_GATEWAY.value,
            op_object_id=slz.instance.id,
            op_object=slz.instance.name,
            comment=_("更新微网关实例"),
        )

        return OKJsonResponse()

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.MicroGatewaySLZ()}, tags=["MicroGateway"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["MicroGateway"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        # TODO: 删除微网关实例前，需检查微网关实例中，已无注册的接口

        instance = self.get_object()
        instance_id = instance.id

        instance.delete()

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=request.gateway.id,
            op_object_type=OpObjectTypeEnum.MICRO_GATEWAY.value,
            op_object_id=instance_id,
            op_object=instance.name,
            comment=_("删除微网关实例"),
        )

        return OKJsonResponse()
