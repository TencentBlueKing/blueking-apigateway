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


from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.core.models import Stage
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
        queryset = MCPServer.objects.filter(is_public=True, status=MCPServerStatusEnum.ACTIVE.value)

        page = self.paginate_queryset(queryset)

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
            context={"stages": stages},
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
        serializer = self.get_serializer(instance)
        # FIXME: return the tools details and usage page
        # 返回工具列表页面需要的信息
        return OKJsonResponse(data=serializer.data)
