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
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.apps.mcp_server.utils import build_mcp_server_url
from apigateway.biz.audit import Auditor
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Stage
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.time import now_datetime

from .serializers import (
    MCPServerAppPermissionApplyListInputSLZ,
    MCPServerAppPermissionApplyListOutputSLZ,
    MCPServerAppPermissionApplyUpdateInputSLZ,
    MCPServerAppPermissionCreateInputSLZ,
    MCPServerAppPermissionListInputSLZ,
    MCPServerAppPermissionListOutputSLZ,
    MCPServerCreateInputSLZ,
    MCPServerGuidelineOutputSLZ,
    MCPServerListOutputSLZ,
    MCPServerRetrieveOutputSLZ,
    MCPServerToolDocOutputSLZ,
    MCPServerToolOutputSLZ,
    MCPServerUpdateInputSLZ,
    MCPServerUpdateLabelsInputSLZ,
    MCPServerUpdateStatusInputSLZ,
)
from .utils import get_valid_resource_names


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
            "gateway": self.request.gateway,
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
        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        data_before = get_model_dict(instance)

        valid_resource_names = get_valid_resource_names(gateway_id=self.request.gateway.id, stage_id=instance.stage.id)

        slz = MCPServerUpdateInputSLZ(
            instance, data=request.data, partial=partial, context={"valid_resource_names": valid_resource_names}
        )
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        # sync the permissions, if any changes in the resource_names
        MCPServerHandler.sync_permissions(instance.id)

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


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 工具列表",
        responses={status.HTTP_200_OK: MCPServerToolOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerToolsListApi(generics.ListAPIView):
    queryset = MCPServer.objects.all()
    lookup_url_kwarg = "mcp_server_id"

    def list(self, request, *args, **kwargs):
        instance = self.get_object()

        tool_resources, labels = MCPServerHandler.get_tools_resources_and_labels(
            gateway_id=request.gateway.id,
            stage_name=instance.stage.name,
            resource_names=instance.resource_names,
        )

        slz = MCPServerToolOutputSLZ(
            tool_resources,
            many=True,
            context={"labels": labels},
        )

        return OKJsonResponse(status=status.HTTP_200_OK, data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 使用指南",
        responses={status.HTTP_200_OK: MCPServerGuidelineOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerGuidelineRetrieveApi(generics.RetrieveAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerGuidelineOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        template_name = f"mcp_server/{get_current_language_code()}/guideline.md"
        content = render_to_string(
            template_name,
            context={
                "name": instance.name,
                "sse_url": build_mcp_server_url(instance.name),
            },
        )
        slz = self.get_serializer({"content": content})

        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 某个工具的文档",
        responses={status.HTTP_200_OK: MCPServerToolDocOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerToolDocRetrieveApi(generics.RetrieveAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerToolDocOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        resource_name = kwargs.get("tool_name")

        doc = MCPServerHandler.get_tool_doc(
            gateway_id=request.gateway.id,
            stage_name=instance.stage.name,
            tool_name=resource_name,
        )

        slz = MCPServerToolDocOutputSLZ(doc)
        return OKJsonResponse(data=slz.data)


class MCPServerAppPermissionQuerySetMixin:
    def get_queryset(self):
        return MCPServerAppPermission.objects.filter(
            mcp_server_id=self.kwargs["mcp_server_id"],
            mcp_server__gateway=self.request.gateway,
        )


class MCPServerAppPermissionApplyQuerySetMixin:
    def get_queryset(self):
        return MCPServerAppPermissionApply.objects.filter(
            mcp_server_id=self.kwargs["mcp_server_id"],
            mcp_server__gateway=self.request.gateway,
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=MCPServerAppPermissionListInputSLZ,
        operation_description="获取已授权应用列表",
        responses={status.HTTP_200_OK: MCPServerAppPermissionListOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="主动授权应用",
        request_body=MCPServerAppPermissionCreateInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionListCreateApi(MCPServerAppPermissionQuerySetMixin, generics.ListCreateAPIView):
    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        bk_app_code = slz.validated_data.get("bk_app_code")
        grant_type = slz.validated_data.get("grant_type")

        queryset = self.get_queryset()
        if bk_app_code:
            queryset = queryset.filter(bk_app_code__icontains=bk_app_code)

        if grant_type:
            queryset = queryset.filter(grant_type=grant_type)

        page = self.paginate_queryset(queryset)
        slz = MCPServerAppPermissionListOutputSLZ(page, many=True)

        return self.get_paginated_response(slz.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionCreateInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=kwargs["mcp_server_id"],
            bk_app_code=data["bk_app_code"],
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
            expire_days=None,
        )

        MCPServerHandler.sync_permissions(kwargs["mcp_server_id"])

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除授权应用",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionDestroyApi(MCPServerAppPermissionQuerySetMixin, generics.DestroyAPIView):
    lookup_url_kwarg = "id"

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=MCPServerAppPermissionApplyListInputSLZ,
        operation_description="获取授权审批列表",
        responses={status.HTTP_200_OK: MCPServerAppPermissionApplyListOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionApplyListApi(MCPServerAppPermissionApplyQuerySetMixin, generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionApplyListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = MCPServerAppPermissionApply.objects.filter_app_permission_apply(
            self.get_queryset(),
            data.get("state"),
            data.get("bk_app_code"),
            data.get("applied_by"),
        )

        page = self.paginate_queryset(queryset)

        slz = MCPServerAppPermissionApplyListOutputSLZ(page, many=True)
        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取授权审批申请人列表",
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionApplyApplicantListApi(MCPServerAppPermissionApplyQuerySetMixin, generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        applied_by_list = list(queryset.values_list("applied_by", flat=True).distinct().order_by("applied_by"))

        return OKJsonResponse(data={"applicants": applied_by_list})


@method_decorator(
    name="patch",
    decorator=swagger_auto_schema(
        operation_description="更新授权审批状态，通过/驳回",
        request_body=MCPServerAppPermissionApplyUpdateInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionApplyUpdateStatusApi(MCPServerAppPermissionApplyQuerySetMixin, generics.UpdateAPIView):
    serializer_class = MCPServerAppPermissionApplyUpdateInputSLZ
    lookup_url_kwarg = "id"

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = MCPServerAppPermissionApplyUpdateInputSLZ(instance, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(handled_by=request.user.username, handled_time=now_datetime())

        if slz.instance.status == MCPServerAppPermissionApplyStatusEnum.APPROVED.value:
            MCPServerAppPermission.objects.save_permission(
                mcp_server_id=slz.instance.mcp_server.id,
                bk_app_code=slz.instance.bk_app_code,
                grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
                expire_days=None,
            )

            MCPServerHandler.sync_permissions(kwargs["mcp_server_id"])

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
