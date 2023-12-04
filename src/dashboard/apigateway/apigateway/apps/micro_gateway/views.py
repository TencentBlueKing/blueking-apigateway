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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.micro_gateway import serializers
from apigateway.apps.micro_gateway.constants import MicroGatewayCreateWayEnum
from apigateway.apps.micro_gateway.handlers import MicroGatewayHandlerFactory
from apigateway.biz.audit import Auditor
from apigateway.core.models import MicroGateway, Stage
from apigateway.utils.bk_ticket import get_user_bk_ticket_from_request
from apigateway.utils.django import get_model_dict
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
            slz.instance.id, get_user_bk_ticket_from_request(request), request.user.username
        )

        Auditor.record_micro_gateway_op_success(
            op_type=OpTypeEnum.CREATE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
            data_before={},
            data_after=get_model_dict(slz.instance),
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
        data_before = get_model_dict(instance)

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
                slz.instance.id, get_user_bk_ticket_from_request(request), request.user.username
            )

        Auditor.record_micro_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
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
        data_before = get_model_dict(instance)
        instance_id = instance.id

        instance.delete()

        Auditor.record_micro_gateway_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance_id,
            instance_name=instance.name,
            data_before=data_before,
            data_after={},
        )

        return OKJsonResponse()
