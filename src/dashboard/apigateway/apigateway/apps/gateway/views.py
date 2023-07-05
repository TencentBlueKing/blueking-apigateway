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
from blue_krill.async_utils.django_utils import delay_on_commit
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.apps.gateway import serializers
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.iam import IAMHandler
from apigateway.common.contexts import APIAuthContext
from apigateway.common.error_codes import error_codes
from apigateway.controller.tasks import revoke_release, rolling_update_release
from apigateway.core.models import Gateway, MicroGateway, Resource
from apigateway.core.signals import reversion_update_signal
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse
from apigateway.utils.swagger import PaginatedResponseSwaggerAutoSchema
from apigateway.utils.time import now_datetime


class BaseGatewayViewSet(viewsets.ModelViewSet):
    def get_object(self):
        obj = super().get_object()
        if not obj.has_permission(self.request.user.username):
            raise error_codes.FORBIDDEN.format(_("当前用户无访问网关权限。"), replace=True)
        return obj


class GatewayViewSet(BaseGatewayViewSet):
    queryset = Gateway.objects.all()
    serializer_class = serializers.GatewayCreateSLZ
    lookup_field = "id"

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Gateway"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        # 1. save api
        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 2. save related data
        GatewayHandler().save_related_data(
            gateway=slz.instance,
            user_auth_type=slz.validated_data["user_auth_type"],
            username=request.user.username,
        )

        # 3. 在权限中心注册分级管理员，创建用户组
        if settings.USE_BK_IAM_PERMISSION:
            IAMHandler.register_grade_manager_and_builtin_user_groups(slz.instance)

        # 4. record audit log
        GatewayHandler().add_create_audit_log(slz.instance, request.user.username)

        return OKJsonResponse("OK", data={"id": slz.instance.id})

    @swagger_auto_schema(
        auto_schema=PaginatedResponseSwaggerAutoSchema,
        query_serializer=serializers.GatewayQuerySLZ,
        responses={status.HTTP_200_OK: serializers.GatewayListSLZ(many=True)},
        tags=["API"],
    )
    def list(self, request, *args, **kwargs):
        slz = serializers.GatewayQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        gateways = Gateway.objects.search_gateways(
            request.user.username,
            slz.validated_data.get("name"),
            order_by="-updated_time",
        )

        # NOTE: 保留分页的接口协议，但是实际内容暂不分页
        paginator = LimitOffsetPaginator(count=len(gateways), offset=0, limit=len(gateways))

        gateway_ids = [gateway.id for gateway in gateways]
        serializer = serializers.GatewayListSLZ(
            gateways,
            many=True,
            context={
                "api_resource_count": Resource.objects.get_api_resource_count(gateway_ids),
                "api_stages": GatewayHandler().search_gateway_stages(gateway_ids),
                "api_auth_contexts": APIAuthContext().filter_scope_id_config_map(scope_ids=gateway_ids),
                "micro_gateway_count": MicroGateway.objects.get_count_by_gateway(gateway_ids),
            },
        )
        return OKJsonResponse("OK", data=paginator.get_paginated_data(serializer.data))

    @swagger_auto_schema(
        request_body=serializers.GatewayUpdateSLZ, responses={status.HTTP_200_OK: ""}, tags=["Gateway"]
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.GatewayUpdateSLZ(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
        )

        GatewayHandler().add_update_audit_log(slz.instance, request.user.username)

        return OKJsonResponse("OK")

    @swagger_auto_schema(responses={status.HTTP_200_OK: serializers.GatewayDetailSLZ()}, tags=["Gateway"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = serializers.GatewayDetailSLZ.from_instance(instance)
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Gateway"])
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        # 网关为"停用"状态，才可以删除
        if instance.is_active:
            return FailJsonResponse(_("请先停用网关，然后再删除。"))

        # 删除权限中心中网关的分级管理员和用户组
        IAMHandler.delete_grade_manager_and_builtin_user_groups(instance)

        GatewayHandler().delete_gateway(instance_id)

        # send signal
        reversion_update_signal.send(sender=Gateway, instance_id=instance_id, action="destroy")

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.DELETE.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=instance_id,
            op_object_type=OpObjectTypeEnum.API.value,
            op_object_id=instance_id,
            op_object=instance.name,
            comment=_("删除网关"),
        )

        return OKJsonResponse("OK")

    def _update_micro_gateway_release(self, instance: Gateway):
        if not instance.is_micro_gateway:
            return

        if instance.is_active:
            delay_on_commit(rolling_update_release, gateway_id=instance.pk)
        else:
            delay_on_commit(revoke_release, gateway_id=instance.pk)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, tags=["Gateway"])
    def update_status(self, request, *args, **kwargs):
        instance: Gateway = self.get_object()
        slz = serializers.GatewayUpdateStatusSLZ(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        # 1. save instance
        slz.save(updated_by=request.user.username, updated_time=now_datetime())

        # 2. send signal
        reversion_update_signal.send(sender=Gateway, instance_id=instance.pk, action="update status")

        # 3. revoke micro_gateway instance released resources
        self._update_micro_gateway_release(instance)

        record_audit_log(
            username=request.user.username,
            op_type=OpTypeEnum.MODIFY.value,
            op_status=OpStatusEnum.SUCCESS.value,
            op_object_group=instance.pk,
            op_object_type=OpObjectTypeEnum.API.value,
            op_object_id=instance.pk,
            op_object=instance.name,
            comment=_("更新网关状态"),
        )

        return OKJsonResponse("OK")
