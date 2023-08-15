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
from typing import List

from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.gateway import GatewayHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.constants import GatewayStatusEnum, UserAuthTypeEnum
from apigateway.core.models import Gateway, Resource
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

from .serializers import (
    GatewayCreateInputSLZ,
    GatewayListOutputSLZ,
    GatewayRetrieveOutputSLZ,
    GatewayUpdateInputSLZ,
    GatewayUpdateStatusInputSLZ,
)


class GatewayListCreateApi(generics.ListCreateAPIView):
    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GatewayListOutputSLZ(many=True)},
        tags=["Gateway"],
    )
    def list(self, request, *args, **kwargs):
        gateways = self._filter_list_gateways(self.request.user.username)
        gateway_ids = [gateway.id for gateway in gateways]

        slz = GatewayListOutputSLZ(
            gateways,
            many=True,
            context={
                "resource_count": Resource.objects.get_resource_count(gateway_ids),
                "stages": GatewayHandler.get_stages_with_release_status(gateway_ids),
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids),
            },
        )

        return OKJsonResponse(data=slz.data)

    def _filter_list_gateways(self, username: str) -> List[Gateway]:
        """过滤出当前用户有权限的网关列表"""
        # 使用 _maintainers 过滤的数据并不准确，需要根据其中人员列表二次过滤
        queryset = Gateway.objects.filter(_maintainers__contains=username)
        return [gateway for gateway in queryset if gateway.has_permission(username)]

    @swagger_auto_schema(responses={status.HTTP_201_CREATED: ""}, tags=["Gateway"])
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = GatewayCreateInputSLZ(data=request.data, context={"username": request.user.username})
        slz.is_valid(raise_exception=True)

        # 1. save gateway
        slz.save(
            status=GatewayStatusEnum.ACTIVE.value,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 2. save related data
        GatewayHandler.save_related_data(
            gateway=slz.instance,
            user_auth_type=UserAuthTypeEnum(settings.DEFAULT_USER_AUTH_TYPE).value,
            username=request.user.username,
        )

        # 3. record audit log
        GatewayHandler.record_audit_log_success(request.user.username, slz.instance, op_type=OpTypeEnum.CREATE)

        return OKJsonResponse(status=status.HTTP_201_CREATED, data={"id": slz.instance.id})


class GatewayRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayRetrieveOutputSLZ
    lookup_url_kwarg = "gateway_id"

    @swagger_auto_schema(responses={status.HTTP_200_OK: GatewayRetrieveOutputSLZ()}, tags=["Gateway"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = GatewayRetrieveOutputSLZ(
            instance,
            context={
                "auth_config": GatewayAuthContext().get_auth_config(instance.pk),
                "feature_flags": GatewayHandler.get_feature_flag(instance.pk),
            },
        )
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        request_body=GatewayUpdateInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Gateway"],
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        slz = GatewayUpdateInputSLZ(instance=instance, data=request.data, partial=partial)
        slz.is_valid(raise_exception=True)

        slz.save(updated_by=request.user.username)

        GatewayHandler.record_audit_log_success(request.user.username, instance, op_type=OpTypeEnum.MODIFY)

        return OKJsonResponse()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["Gateway"],
    )
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 网关为“停用”状态，才可以删除
        if instance.is_active:
            return FailJsonResponse(
                status=status.HTTP_400_BAD_REQUEST,
                code="GATEWAY_IS_ACTIVE",
                message=_("请先停用网关，然后再删除。"),
            )

        GatewayHandler.delete_gateway(instance.pk)

        GatewayHandler.record_audit_log_success(request.user.username, instance, OpTypeEnum.DELETE)

        return OKJsonResponse()


class GatewayUpdateStatusApi(generics.UpdateAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayUpdateStatusInputSLZ
    lookup_url_kwarg = "gateway_id"

    @swagger_auto_schema(
        request_body=GatewayUpdateStatusInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Gateway"],
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = GatewayUpdateStatusInputSLZ(instance=instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(updated_by=request.user.username)

        # FIXME: 添加触发发布微网关的逻辑

        GatewayHandler.record_audit_log_success(request.user.username, instance, op_type=OpTypeEnum.MODIFY)

        return OKJsonResponse()
