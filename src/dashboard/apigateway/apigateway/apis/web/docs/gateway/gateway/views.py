# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.biz.sdk.gateway_sdk import GatewaySDKHandler
from apigateway.common.permissions import GatewayDisplayablePermission
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, Release
from apigateway.service.contexts import GatewayAuthContext
from apigateway.utils.responses import OKJsonResponse

from .serializers import GatewayOutputSLZ, GatewayQueryInputSLZ


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表，仅显示公开的、已发布的网关",
        query_serializer=GatewayQueryInputSLZ,
        responses={status.HTTP_200_OK: GatewayOutputSLZ(many=True)},
        tags=["WebAPI.Docs.Gateway"],
    ),
)
class GatewayListApi(generics.ListAPIView):
    serializer_class = GatewayQueryInputSLZ

    def list(self, request, *args, **kwargs):
        """获取网关列表"""
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        user_tenant_id = get_user_tenant_id(request)

        # 网关公开，启用中
        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        # 根据租户过滤 => app 开发者 可以看到本租户 + 全租户的网关列表及文档 => 所以这里以 user_tenant_id 当成 app_tenant_id 过滤
        queryset = gateway_filter_by_app_tenant_id(queryset, user_tenant_id)

        # 根据网关名称、描述过滤
        keyword = slz.validated_data.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(description__icontains=keyword))

        # 网关存在已发布的版本
        released_gateway_ids = Release.objects.all().values_list("gateway_id", flat=True).distinct()
        gateways = list(queryset.filter(id__in=released_gateway_ids))

        gateway_ids = [gateway.id for gateway in gateways]

        # FIXME: gateway maintainers to display_name, only ee edition
        output_slz = GatewayOutputSLZ(
            gateways,
            many=True,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids),
                "gateway_sdks": GatewaySDKHandler.get_sdks(gateway_ids),
            },
        )

        # NOTE: 需将官方 SDK 放在前面，但官方标记 is_official 不在 Gateway 表中，因此需要获取数据后，再排序分页
        # FIXME: 性能问题？
        page = self.paginate_queryset(sorted(output_slz.data, key=lambda x: (-x["is_official"], x["name"])))
        return self.get_paginated_response(page)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关详情，仅显示公开的、已发布的网关",
        responses={status.HTTP_200_OK: GatewayOutputSLZ},
        tags=["WebAPI.Docs.Gateway"],
    ),
)
class GatewayRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [GatewayDisplayablePermission]

    def retrieve(self, request, gateway_name: str, *args, **kwargs):
        """根据网关名称，获取网关详情"""
        slz = GatewayOutputSLZ(
            request.gateway,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config([request.gateway.id]),
                "gateway_sdks": GatewaySDKHandler.get_sdks([request.gateway.id]),
            },
        )
        return OKJsonResponse(data=slz.data)
