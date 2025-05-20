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
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.biz.audit import Auditor
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Stage
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import OKJsonResponse

from .serializers import (
    MCPServerCreateInputSLZ,
    MCPServerListOutputSLZ,
    MCPServerRetrieveOutputSLZ,
    MCPServerUpdateInputSLZ,
    MCPServerUpdateLabelsInputSLZ,
    MCPServerUpdateStatusInputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关的 MCPServer 列表",
        responses={status.HTTP_200_OK: MCPServerListOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建 MCPServer",
        request_body=MCPServerCreateInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerListCreateApi(generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        queryset = MCPServer.objects.filter(gateway=self.request.gateway)

        page = self.paginate_queryset(queryset)

        stages = {
            stage.id: {
                "id": stage.id,
                "name": stage.name,
            }
            for stage in Stage.objects.filter(gateway=self.request.gateway)
        }
        slz = MCPServerListOutputSLZ(
            page,
            many=True,
            context={"stages": stages},
        )

        return self.get_paginated_response(slz.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ctx = {
            "gateway_id": self.request.gateway.id,
            "created_by": request.user.username,
            "status": MCPServerStatusEnum.ACTIVE.value,
        }
        slz = MCPServerCreateInputSLZ(data=request.data, context=ctx)
        slz.is_valid(raise_exception=True)

        slz.save()
        # FIXME: trigger the mcp server permission refresh

        # record audit log
        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.CREATE,
            username=request.user.username,
            gateway_id=self.request.gateway.id,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
            data_before={},
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED, data={"id": slz.instance.id})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定网关的信息",
        responses={status.HTTP_200_OK: MCPServerRetrieveOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新 MCPServer",
        request_body=MCPServerUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="更新 MCPServer 部分信息",
        request_body=MCPServerUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除 MCPServer",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerRetrieveOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        stages = {
            instance.stage.id: {
                "id": instance.stage.id,
                "name": instance.stage.name,
            }
        }
        serializer = self.get_serializer(instance, context={"stages": stages})
        # FIXME: return the tools details and usage page
        # 返回工具列表页面需要的信息

        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = MCPServerUpdateInputSLZ(instance, data=request.data, partial=partial)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        # FIXME: trigger the mcp server permission refresh if update the resource_ids

        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=self.request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        if instance.is_active:
            raise error_codes.FAILED_PRECONDITION.format(_("请先停用 MCPServer，然后再删除。"), replace=True)

        instance.delete()

        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=self.request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after={},
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="更新 MCPServer 状态，如启用、停用",
        request_body=MCPServerUpdateStatusInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerUpdateStatusApi(generics.UpdateAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerUpdateStatusInputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=self.request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="更新 MCPServer 标签",
        request_body=MCPServerUpdateLabelsInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerUpdateLabelsApi(generics.UpdateAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerUpdateLabelsInputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data_before = get_model_dict(instance)

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=self.request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
