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
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_app_binding import GatewayAppBindingHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.common.error_codes import error_codes
from apigateway.common.release.publish import trigger_gateway_publish
from apigateway.core.constants import GatewayStatusEnum, PublishSourceEnum
from apigateway.core.models import Gateway
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    GatewayCreateInputSLZ,
    GatewayFeatureFlagsOutputSLZ,
    GatewayListInputSLZ,
    GatewayListOutputSLZ,
    GatewayRetrieveOutputSLZ,
    GatewayUpdateInputSLZ,
    GatewayUpdateStatusInputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表",
        responses={status.HTTP_200_OK: GatewayListOutputSLZ(many=True)},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建网关",
        request_body=GatewayCreateInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayListCreateApi(generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        # 获取用户有权限的网关列表，后续切换到 IAM
        gateways = GatewayHandler.list_gateways_by_user(request.user.username)
        gateway_ids = [gateway.id for gateway in gateways]

        slz = GatewayListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = self._filter_list_queryset(
            gateway_ids,
            slz.validated_data.get("query"),
            slz.validated_data["order_by"],
        )
        page = self.paginate_queryset(queryset)
        gateway_ids = [gateway.id for gateway in page]

        output_slz = GatewayListOutputSLZ(
            page,
            many=True,
            context={
                "resource_count": GatewayHandler.get_resource_count(gateway_ids),
                "stages": GatewayHandler.get_stages_with_release_status(gateway_ids),
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids),
            },
        )

        return self.get_paginated_response(output_slz.data)

    def _filter_list_queryset(self, gateway_ids: List[int], query: Optional[str], order_by: str):
        queryset = Gateway.objects.filter(id__in=gateway_ids)

        if query:
            queryset = queryset.filter(name__icontains=query)

        return queryset.order_by(order_by)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = GatewayCreateInputSLZ(data=request.data, context={"created_by": request.user.username})
        slz.is_valid(raise_exception=True)

        bk_app_codes = slz.validated_data.pop("bk_app_codes")

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
            app_codes_to_binding=bk_app_codes,
        )

        # 3. record audit log
        GatewayHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=slz.instance.id,
            op_type=OpTypeEnum.CREATE,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED, data={"id": slz.instance.id})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定网关的信息",
        responses={status.HTTP_200_OK: GatewayRetrieveOutputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新网关",
        request_body=GatewayUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="更新网关部分信息",
        request_body=GatewayUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除网关",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayRetrieveOutputSLZ
    lookup_url_kwarg = "gateway_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = GatewayRetrieveOutputSLZ(
            instance,
            context={
                "auth_config": GatewayAuthContext().get_auth_config(instance.pk),
                "bk_app_codes": GatewayAppBindingHandler.get_bound_app_codes(instance),
            },
        )
        return OKJsonResponse(data=slz.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        slz = GatewayUpdateInputSLZ(instance=instance, data=request.data, partial=partial)
        slz.is_valid(raise_exception=True)

        bk_app_codes = slz.validated_data.pop("bk_app_codes")

        slz.save(updated_by=request.user.username)

        GatewayAppBindingHandler.update_gateway_app_bindings(instance, bk_app_codes)

        GatewayHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=instance.id,
            op_type=OpTypeEnum.MODIFY,
            instance_id=instance.id,
            instance_name=instance.name,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        # 网关为“停用”状态，才可以删除
        if instance.is_active:
            raise error_codes.FAILED_PRECONDITION.format(_("请先停用网关，然后再删除。"), replace=True)

        GatewayHandler.delete_gateway(instance_id)

        GatewayHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=instance_id,
            op_type=OpTypeEnum.DELETE,
            instance_id=instance_id,
            instance_name=instance.name,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新网关状态，如启用、停用",
        request_body=GatewayUpdateStatusInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayUpdateStatusApi(generics.UpdateAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayUpdateStatusInputSLZ
    lookup_url_kwarg = "gateway_id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance=instance, data=request.data)
        slz.is_valid(raise_exception=True)

        is_need_publish = slz.validated_data["status"] is not instance.status

        slz.save(updated_by=request.user.username)

        # 触发网关发布
        if is_need_publish:
            source = PublishSourceEnum.GATEWAY_ENABLE if instance.is_active else PublishSourceEnum.GATEWAY_DISABLE
            trigger_gateway_publish(source, request.user.username, instance.id)

        GatewayHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=instance.id,
            op_type=OpTypeEnum.MODIFY,
            instance_id=instance.id,
            instance_name=instance.name,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关特性开关",
        responses={status.HTTP_200_OK: GatewayFeatureFlagsOutputSLZ()},
        tags=["WebAPI.Gateway"],
    ),
)
class GatewayFeatureFlagsApi(generics.ListAPIView):
    queryset = Gateway.objects.all()
    serializer_class = GatewayFeatureFlagsOutputSLZ
    lookup_url_kwarg = "gateway_id"

    def list(self, request, *args, **kwargs):
        instance = self.get_object()

        feature_flags = GatewayHandler.get_feature_flags(instance.pk)
        slz = self.get_serializer({"feature_flags": feature_flags})

        return OKJsonResponse(data=slz.data)
