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


from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.apps.mcp_server.utils import build_mcp_server_url
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Stage
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    MCPServerListOutputSLZ,
    MCPServerRetrieveOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关的 MCPServer 列表",
        responses={status.HTTP_200_OK: MCPServerListOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        # mcp server should be public and active
        queryset = MCPServer.objects.filter(is_public=True, status=MCPServerStatusEnum.ACTIVE.value)
        # gateway should be active
        queryset = queryset.filter(gateway__status=GatewayStatusEnum.ACTIVE.value)
        # the stage should be active and online
        queryset = queryset.filter(stage__status=StageStatusEnum.ACTIVE.value)
        # optimize query by using select_related
        queryset = queryset.select_related("gateway", "stage")

        # note: the stage offline will update related mcp server status to inactive,
        # the stage publish will update the mcp server resource_ids,
        # so we don't need to care about is the mcp server stage is correctly published here

        page = self.paginate_queryset(queryset)

        gateway_ids = [mcp_server.gateway.id for mcp_server in page]
        gateways = {
            gateway.id: {
                "id": gateway.id,
                "name": gateway.name,
            }
            for gateway in Gateway.objects.filter(id__in=gateway_ids)
        }
        stage_ids = [mcp_server.stage.id for mcp_server in page]
        stages = {
            stage.id: {
                "id": stage.id,
                "name": stage.name,
            }
            for stage in Stage.objects.filter(id__in=stage_ids)
        }

        slz = MCPServerListOutputSLZ(
            page,
            many=True,
            context={
                "gateways": gateways,
                "stages": stages,
            },
        )

        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定网关的信息",
        responses={status.HTTP_200_OK: MCPServerRetrieveOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPMarketplaceServerRetrieveApi(generics.RetrieveAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerRetrieveOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_public:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未公开，无法访问。"))
        if instance.status != MCPServerStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 未启用，无法访问。"))
        if instance.gateway.status != GatewayStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关未启用，无法访问。"))
        if instance.stage.status != StageStatusEnum.ACTIVE.value:
            raise error_codes.NOT_FOUND.format(_("当前 MCPServer 所属网关对应的环境未启用，无法访问。"))

        template_name = f"mcp_server/{get_current_language_code()}/guideline.md"
        guideline = render_to_string(
            template_name,
            context={
                "name": instance.name,
                "sse_url": build_mcp_server_url(instance.name),
            },
        )

        gateways = {
            instance.gateway.id: {
                "id": instance.gateway.id,
                "name": instance.gateway.name,
            }
        }
        stages = {
            instance.stage.id: {
                "id": instance.stage.id,
                "name": instance.stage.name,
            }
        }

        serializer = self.get_serializer(
            instance,
            context={
                "gateways": gateways,
                "stages": stages,
                "guideline": guideline,
            },
        )
        # FIXME: return the tools details and usage page
        # 返回工具列表页面需要的信息
        return OKJsonResponse(data=serializer.data)
