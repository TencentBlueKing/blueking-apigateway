#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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


import csv
from io import StringIO

from django.db import transaction
from django.db.models import Case, DateTimeField, F, OuterRef, Q, Subquery, When
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.constants import (
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerAppPermissionApplyProcessedStateEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerExtendTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerCategory,
    MCPServerExtend,
)
from apigateway.biz.audit import Auditor
from apigateway.biz.mcp_server import MCPServerHandler, MCPServerPromptHandler
from apigateway.common.constants import CallSourceTypeEnum
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.common.tenant.user_credentials import get_user_credentials_from_request
from apigateway.core.models import Stage
from apigateway.service.resource_version import get_standard_resource_names_set
from apigateway.utils.django import get_model_dict
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse
from apigateway.utils.time import now_datetime

from .serializers import (
    GatewayMCPServerAppPermissionExportInputSLZ,
    GatewayMCPServerAppPermissionListInputSLZ,
    GatewayMCPServerAppPermissionListOutputSLZ,
    MCPServerAppPermissionAppCodeListInputSLZ,
    MCPServerAppPermissionAppCodeListOutputSLZ,
    MCPServerAppPermissionApplyApplicantListInputSLZ,
    MCPServerAppPermissionApplyListInputSLZ,
    MCPServerAppPermissionApplyListOutputSLZ,
    MCPServerAppPermissionApplyUpdateInputSLZ,
    MCPServerAppPermissionCreateInputSLZ,
    MCPServerAppPermissionListInputSLZ,
    MCPServerAppPermissionListOutputSLZ,
    MCPServerBatchConfigInputSLZ,
    MCPServerBatchConfigOutputSLZ,
    MCPServerCategoryOutputSLZ,
    MCPServerConfigListOutputSLZ,
    MCPServerCreateInputSLZ,
    MCPServerFilterOptionsOutputSLZ,
    MCPServerGuidelineOutputSLZ,
    MCPServerListInputSLZ,
    MCPServerListOutputSLZ,
    MCPServerRemotePromptsBatchInputSLZ,
    MCPServerRemotePromptsBatchOutputSLZ,
    MCPServerRemotePromptsOutputSLZ,
    MCPServerRemotePromptsQueryInputSLZ,
    MCPServerRetrieveOutputSLZ,
    MCPServerStageReleaseCheckInputSLZ,
    MCPServerStageReleaseCheckOutputSLZ,
    MCPServerToolDocOutputSLZ,
    MCPServerToolOutputSLZ,
    MCPServerUpdateInputSLZ,
    MCPServerUpdateStatusInputSLZ,
    MCPServerUserCustomDocInputSLZ,
    MCPServerUserCustomDocOutputSLZ,
)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关的 MCPServer 列表",
        query_serializer=MCPServerListInputSLZ,
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
        slz = MCPServerListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = (
            MCPServer.objects.filter(gateway=self.request.gateway)
            .select_related("stage")
            .prefetch_related("categories")
        )

        # 关键词搜索
        keyword = slz.validated_data.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(_labels__icontains=keyword)
            )

        # 状态筛选
        filter_status = slz.validated_data.get("status")
        if filter_status is not None:
            queryset = queryset.filter(status=filter_status)

        # 环境筛选
        stage_id = slz.validated_data.get("stage_id")
        if stage_id is not None:
            queryset = queryset.filter(stage_id=stage_id)

        # 标签筛选
        label = slz.validated_data.get("label")
        if label:
            queryset = queryset.filter(_labels__icontains=label)

        # 分类筛选 —— 使用 biz 层的通用方法
        categories = slz.validated_data.get("categories")
        if categories:
            queryset = MCPServerHandler.apply_category_filter(queryset, categories)

        # 排序（支持多字段排序，如 "-status,-updated_time"）
        order_by = slz.validated_data.get("order_by", "-status,-updated_time")
        order_fields = [field.strip() for field in order_by.split(",") if field.strip()]
        queryset = queryset.order_by(*order_fields) if order_fields else queryset.order_by("-status", "-updated_time")

        page = self.paginate_queryset(queryset)

        stages = {
            stage.id: {
                "id": stage.id,
                "name": stage.name,
            }
            for stage in Stage.objects.filter(gateway=self.request.gateway)
        }

        # 获取 prompts_count
        mcp_server_ids = [mcp_server.id for mcp_server in page]
        prompts_count_map = MCPServerHandler.get_prompts_count_map(mcp_server_ids)

        # 预查询 Release 记录，供后续方法共享避免重复查询
        releases = MCPServerHandler._get_releases_for_mcp_servers(page)

        # 获取应用态权限安全风险信息
        app_permission_risks = MCPServerHandler.get_app_permission_risks(page, releases=releases)

        # 计算最低权限级别，用于判断是否展示应用态 URL
        least_privileges = MCPServerHandler.get_least_privileges(page, releases=releases)

        slz = MCPServerListOutputSLZ(
            page,
            many=True,
            context={
                "stages": stages,
                "prompts_count_map": prompts_count_map,
                "app_permission_risks": app_permission_risks,
                "least_privileges": least_privileges,
            },
        )

        return self.get_paginated_response(slz.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        valid_resource_names = MCPServerHandler().get_valid_resource_names(
            gateway_id=self.request.gateway.id, stage_id=request.data["stage_id"]
        )
        ctx = {
            "gateway": self.request.gateway,
            "created_by": request.user.username,
            "status": MCPServerStatusEnum.ACTIVE.value,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": valid_resource_names,
        }
        slz = MCPServerCreateInputSLZ(data=request.data, context=ctx)
        slz.is_valid(raise_exception=True)

        slz.save()

        # sync permissions (includes oauth2 public app permission based on oauth2_public_client_enabled)
        MCPServerHandler.sync_permissions(slz.instance.id)

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


class MCPServerQuerySetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(gateway=self.request.gateway)


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
class MCPServerRetrieveUpdateDestroyApi(MCPServerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = MCPServer.objects.select_related("stage").prefetch_related("categories")
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

        prompts = MCPServerHandler.get_prompts(instance.id)

        releases = MCPServerHandler._get_releases_for_mcp_servers([instance])
        app_permission_risks = MCPServerHandler.get_app_permission_risks([instance], releases=releases)
        least_privileges = MCPServerHandler.get_least_privileges([instance], releases=releases)

        serializer = self.get_serializer(
            instance,
            context={
                "stages": stages,
                "prompts": prompts,
                "app_permission_risks": app_permission_risks,
                "least_privileges": least_privileges,
            },
        )
        return OKJsonResponse(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        data_before = get_model_dict(instance)

        valid_resource_names = MCPServerHandler().get_valid_resource_names(
            gateway_id=self.request.gateway.id, stage_id=instance.stage.id
        )

        slz = MCPServerUpdateInputSLZ(
            instance,
            data=request.data,
            partial=partial,
            context={"valid_resource_names": valid_resource_names, "username": request.user.username},
        )
        slz.is_valid(raise_exception=True)
        slz.save(updated_by=request.user.username)

        # sync permissions (includes oauth2 public app permission based on oauth2_public_client_enabled)
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

        # 删除 prompts
        MCPServerHandler.delete_prompts(instance.id)

        # Delete resource permission records created by sync_permissions
        MCPServerHandler.cleanup_all_resource_permissions(
            gateway_id=self.request.gateway.id,
            mcp_server_id=instance.id,
        )

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
class MCPServerUpdateStatusApi(MCPServerQuerySetMixin, generics.UpdateAPIView):
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
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 工具列表",
        responses={status.HTTP_200_OK: MCPServerToolOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerToolsListApi(MCPServerQuerySetMixin, generics.ListAPIView):
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
            context={"labels": labels, "tool_name_map": instance.gen_tool_name_map()},
        )

        return OKJsonResponse(status=status.HTTP_200_OK, data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 官方使用指南",
        responses={status.HTTP_200_OK: MCPServerGuidelineOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerGuidelineRetrieveApi(MCPServerQuerySetMixin, generics.RetrieveAPIView):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerGuidelineOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        least_privileges = MCPServerHandler.get_least_privileges([instance])
        least_privilege = least_privileges.get((instance.gateway.id, instance.stage.id), "")

        user_tenant_id = get_user_tenant_id(request)

        # 使用 biz 层的通用方法生成 guideline
        content = MCPServerHandler.build_guideline(
            instance,
            user_tenant_id=user_tenant_id,
            least_privilege=least_privilege,
        )

        slz = self.get_serializer({"content": content})

        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 配置列表（支持 Cursor、CodeBuddy、Claude、VSCode 等工具的配置）",
        responses={status.HTTP_200_OK: MCPServerConfigListOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerConfigListApi(MCPServerQuerySetMixin, generics.RetrieveAPIView):
    """获取 MCPServer 配置列表，支持多种 AI 工具的配置"""

    queryset = MCPServer.objects.all()
    serializer_class = MCPServerConfigListOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        least_privileges = MCPServerHandler.get_least_privileges([instance])
        least_privilege = least_privileges.get((instance.gateway.id, instance.stage.id), "")

        user_tenant_id = get_user_tenant_id(request)
        configs = MCPServerHandler.build_agent_client_configs(instance, least_privilege, user_tenant_id=user_tenant_id)
        return OKJsonResponse(data={"configs": configs})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 某个工具的文档",
        responses={status.HTTP_200_OK: MCPServerToolDocOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerToolDocRetrieveApi(MCPServerQuerySetMixin, generics.RetrieveAPIView):
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


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 用户自定义文档",
        responses={status.HTTP_200_OK: MCPServerUserCustomDocOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建 MCPServer 用户自定义文档",
        request_body=MCPServerUserCustomDocInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新 MCPServer 用户自定义文档",
        request_body=MCPServerUserCustomDocInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除 MCPServer 用户自定义文档",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerUserCustomDocApi(MCPServerQuerySetMixin, generics.RetrieveUpdateDestroyAPIView, generics.CreateAPIView):
    queryset = MCPServer.objects.all()
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        extend = MCPServerExtend.objects.filter(
            mcp_server=instance, type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value
        ).first()

        content = extend.content if extend else ""
        slz = MCPServerUserCustomDocOutputSLZ({"content": content})

        return OKJsonResponse(data=slz.data)

    def create(self, request, *args, **kwargs):
        instance = self.get_object()

        # 检查是否已存在
        if MCPServerExtend.objects.filter(
            mcp_server=instance, type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value
        ).exists():
            raise error_codes.FAILED_PRECONDITION.format(_("用户自定义文档已存在，请使用更新接口。"), replace=True)

        slz = MCPServerUserCustomDocInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        extend = MCPServerExtend.objects.create(
            mcp_server=instance,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
            content=slz.validated_data["content"],
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        # 用户自定义文档属于 MCPServer 扩展配置，审计统一记录为更新 MCPServer。
        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before={},
            data_after=get_model_dict(extend),
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        extend = MCPServerExtend.objects.filter(
            mcp_server=instance, type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value
        ).first()

        if not extend:
            raise error_codes.NOT_FOUND.format(_("用户自定义文档不存在，请先创建。"), replace=True)

        data_before = get_model_dict(extend)
        slz = MCPServerUserCustomDocInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        extend.content = slz.validated_data["content"]
        extend.updated_by = request.user.username
        extend.save(update_fields=["content", "updated_by", "updated_time"])

        # 用户自定义文档属于 MCPServer 扩展配置，审计统一记录为更新 MCPServer。
        Auditor.record_mcp_server_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance.id,
            instance_name=instance.name,
            data_before=data_before,
            data_after=get_model_dict(extend),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        extend = MCPServerExtend.objects.filter(
            mcp_server=instance, type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value
        ).first()
        if extend:
            data_before = get_model_dict(extend)
            extend.delete()

            # 用户自定义文档属于 MCPServer 扩展配置，审计统一记录为更新 MCPServer。
            Auditor.record_mcp_server_op_success(
                op_type=OpTypeEnum.MODIFY,
                username=request.user.username,
                gateway_id=request.gateway.id,
                instance_id=instance.id,
                instance_name=instance.name,
                data_before=data_before,
                data_after={},
            )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="环境发布前检查对应环境 MCP Server 是否存在资源变更",
        query_serializer=MCPServerStageReleaseCheckInputSLZ,
        responses={status.HTTP_200_OK: MCPServerStageReleaseCheckOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerStageReleaseCheckApi(generics.RetrieveAPIView):
    serializer_class = MCPServerStageReleaseCheckOutputSLZ

    def retrieve(self, request, *args, **kwargs):
        slz = MCPServerStageReleaseCheckInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        stage_id = slz.validated_data["stage_id"]
        resource_version_id = slz.validated_data["resource_version_id"]

        mcp_servers = MCPServer.objects.filter(
            gateway=request.gateway,
            stage_id=stage_id,
        ).all()

        data = {}
        if not mcp_servers:
            data["has_related_changes"] = False
            return OKJsonResponse(data=data)

        changed_mcp_servers = []
        valid_resource_names = get_standard_resource_names_set(resource_version_id, raise_exception=True)
        for mcp_server in mcp_servers:
            mcp_server_resource_names = set(mcp_server.resource_names)
            changed_resource_names = mcp_server_resource_names - valid_resource_names
            if changed_resource_names:
                changed_mcp_servers.append((mcp_server, changed_resource_names))

        # expand the changed_resources to the resource_names
        changed_resources = []
        unique_resource_names = set()
        for mcp_server, changed_resource_names in changed_mcp_servers:
            for resource_name in changed_resource_names:
                unique_resource_names.add(resource_name)

                changed_resources.append(
                    {
                        "resource_name": resource_name,
                        "mcp_server": {
                            "id": mcp_server.id,
                            "name": mcp_server.name,
                        },
                    }
                )

        data["has_related_changes"] = len(changed_resources) > 0
        data["deleted_resource_count"] = len(unique_resource_names)
        data["details"] = changed_resources

        output_slz = self.get_serializer(data)
        return OKJsonResponse(data=output_slz.data)


class MCPServerAppPermissionQuerySetMixin:
    def get_queryset(self):
        return MCPServerAppPermission.objects.filter(
            mcp_server_id=self.kwargs["mcp_server_id"],
            mcp_server__gateway=self.request.gateway,
        )


class MCPServerAppPermissionApplyQuerySetMixin:
    def get_queryset(self):
        queryset = MCPServerAppPermissionApply.objects.filter(
            mcp_server__gateway=self.request.gateway,
        )
        mcp_server_id = self.kwargs.get("mcp_server_id")
        if mcp_server_id is not None:
            queryset = queryset.filter(mcp_server_id=mcp_server_id)
        return queryset


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
        mcp_server = get_object_or_404(MCPServer, id=kwargs["mcp_server_id"], gateway=request.gateway)
        permission_before = MCPServerAppPermission.objects.filter(
            mcp_server_id=mcp_server.id,
            bk_app_code=data["bk_app_code"],
        ).first()
        data_before = get_model_dict(permission_before) if permission_before else {}

        MCPServerAppPermission.objects.save_permission(
            mcp_server_id=mcp_server.id,
            bk_app_code=data["bk_app_code"],
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
            expire_days=None,
            operator=request.user.username,
        )

        MCPServerHandler.sync_permissions(mcp_server.id)
        permission_after = MCPServerAppPermission.objects.get(
            mcp_server_id=mcp_server.id,
            bk_app_code=data["bk_app_code"],
        )

        Auditor.record_mcp_server_permission_op_success(
            op_type=OpTypeEnum.CREATE if not permission_before else OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=permission_after.id,
            instance_name=permission_after.bk_app_code,
            data_before=data_before,
            data_after=get_model_dict(permission_after),
        )

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
        data_before = get_model_dict(instance)
        instance_id = instance.id
        bk_app_code = instance.bk_app_code
        mcp_server = instance.mcp_server
        instance.delete()

        # 将 bk_app_code 对应已通过审批的 mcp server 记录设置为已删除状态
        MCPServerAppPermissionApply.objects.filter(
            bk_app_code=bk_app_code,
            mcp_server=mcp_server,
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=False,
        ).update(is_deleted=True)

        MCPServerHandler.sync_permissions(kwargs["mcp_server_id"])

        Auditor.record_mcp_server_permission_op_success(
            op_type=OpTypeEnum.DELETE,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=instance_id,
            instance_name=bk_app_code,
            data_before=data_before,
            data_after={},
        )

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
class MCPServerAppPermissionApplyListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionApplyListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        state = data.get("state")
        status_list = MCPServerAppPermissionApplyProcessedStateEnum.get_status_list(state)

        # 根据 mcp_server_id 查询参数过滤，不传则查询当前网关下所有
        queryset = MCPServerAppPermissionApply.objects.filter(mcp_server__gateway=request.gateway)
        mcp_server_id = data.get("mcp_server_id")
        if mcp_server_id:
            queryset = queryset.filter(mcp_server_id=mcp_server_id)

        queryset = MCPServerAppPermissionApply.objects.filter_app_permission_apply(
            queryset,
            status_list,
            data.get("bk_app_code"),
            data.get("applied_by"),
        )
        queryset = queryset.order_by("-handled_time", "-applied_time", "-id")

        page = self.paginate_queryset(queryset)

        context = {
            "gateway_tenant_mode": request.gateway.tenant_mode,
            "gateway_tenant_id": request.gateway.tenant_id,
        }
        slz = MCPServerAppPermissionApplyListOutputSLZ(page, many=True, context=context)
        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取授权审批申请人列表",
        query_serializer=MCPServerAppPermissionApplyApplicantListInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionApplyApplicantListApi(MCPServerAppPermissionApplyQuerySetMixin, generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionApplyApplicantListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        queryset = self.get_queryset()

        state = data.get("state")
        status_list = MCPServerAppPermissionApplyProcessedStateEnum.get_status_list(state)
        queryset = queryset.filter(status__in=status_list)

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
        data_before = get_model_dict(instance)

        slz = MCPServerAppPermissionApplyUpdateInputSLZ(instance, data=request.data)
        slz.is_valid(raise_exception=True)
        slz.save(handled_by=request.user.username, handled_time=now_datetime())

        if slz.instance.status == MCPServerAppPermissionApplyStatusEnum.APPROVED.value:
            MCPServerAppPermission.objects.save_permission(
                mcp_server_id=slz.instance.mcp_server.id,
                bk_app_code=slz.instance.bk_app_code,
                grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
                expire_days=None,
                operator=request.user.username,
            )

            MCPServerHandler.sync_permissions(kwargs["mcp_server_id"])

        Auditor.record_mcp_server_permission_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=request.user.username,
            gateway_id=request.gateway.id,
            instance_id=slz.instance.id,
            instance_name=slz.instance.bk_app_code,
            data_before=data_before,
            data_after=get_model_dict(slz.instance),
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


# ========== Prompts 相关 API ==========


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="从第三方平台获取 Prompts 列表",
        query_serializer=MCPServerRemotePromptsQueryInputSLZ,
        responses={status.HTTP_200_OK: MCPServerRemotePromptsOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerRemotePromptsListApi(generics.ListAPIView):
    """从第三方平台获取 Prompts 列表"""

    def list(self, request, *args, **kwargs):
        slz = MCPServerRemotePromptsQueryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        # 调用第三方平台获取 prompts 列表
        user_credentials = get_user_credentials_from_request(request)
        prompts = MCPServerHandler.fetch_remote_prompts(user_credentials=user_credentials)

        output_slz = MCPServerRemotePromptsOutputSLZ({"prompts": prompts})
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="根据 ID 列表批量获取第三方平台 Prompts 内容",
        request_body=MCPServerRemotePromptsBatchInputSLZ,
        responses={status.HTTP_200_OK: MCPServerRemotePromptsBatchOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerRemotePromptsBatchApi(generics.CreateAPIView):
    """根据 ID 列表批量获取第三方平台 Prompts 内容"""

    def create(self, request, *args, **kwargs):
        slz = MCPServerRemotePromptsBatchInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        prompt_ids = slz.validated_data["ids"]

        # 调用第三方平台批量获取 prompts 内容
        prompts = MCPServerPromptHandler.fetch_remote_prompts_by_ids(prompt_ids)

        output_slz = MCPServerRemotePromptsBatchOutputSLZ({"prompts": prompts})
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取可用的 MCPServer 分类列表（排除官方和精选）",
        responses={status.HTTP_200_OK: MCPServerCategoryOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerCategoriesListApi(generics.ListAPIView):
    """获取可用的 MCPServer 分类列表，排除官方和精选分类"""

    def list(self, request, *args, **kwargs):
        # 排除官方和精选分类，只返回用户可选择的分类
        excluded_names = [
            OFFICIAL_MCP_CATEGORY_NAME,
            FEATURED_MCP_CATEGORY_NAME,
        ]

        queryset = (
            MCPServerCategory.objects.filter(is_active=True)
            .exclude(name__in=excluded_names)
            .order_by("sort_order", "id")
        )

        slz = MCPServerCategoryOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 搜索过滤选项（环境、标签、分类），用于前端下拉列表",
        responses={status.HTTP_200_OK: MCPServerFilterOptionsOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerFilterOptionsApi(generics.ListAPIView):
    """获取 MCPServer 搜索过滤选项，用于前端下拉列表"""

    serializer_class = MCPServerFilterOptionsOutputSLZ

    def list(self, request, *args, **kwargs):
        gateway = self.request.gateway

        # 获取环境列表
        stages = [
            {"id": stage.id, "name": stage.name} for stage in Stage.objects.filter(gateway=gateway).order_by("id")
        ]

        # 获取所有标签（从该网关的 MCPServer 中提取所有唯一标签）
        mcp_servers = MCPServer.objects.filter(gateway=gateway)
        labels_set = set()
        for mcp_server in mcp_servers:
            if mcp_server.labels:
                labels_set.update(mcp_server.labels)
        labels = sorted(labels_set)

        categories = [
            {"id": cat.id, "name": cat.name, "display_name": cat.display_name}
            for cat in MCPServerCategory.objects.filter(is_active=True).order_by("sort_order", "id")
        ]

        return OKJsonResponse(
            data={
                "stages": stages,
                "labels": labels,
                "categories": categories,
            }
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取有 MCPServer 调用权限的 bk_app_code 列表（网关级别），用于前端下拉列表",
        query_serializer=MCPServerAppPermissionAppCodeListInputSLZ,
        responses={status.HTTP_200_OK: MCPServerAppPermissionAppCodeListOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerAppPermissionAppCodeListApi(generics.ListAPIView):
    """获取有 MCPServer 调用权限的 bk_app_code 列表（网关级别）"""

    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionAppCodeListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        mcp_server_id = slz.validated_data.get("mcp_server_id")

        # 构建查询条件
        queryset = MCPServerAppPermission.objects.filter(mcp_server__gateway=request.gateway)

        # 如果传入了 mcp_server_id，则只查询该 MCPServer 的授权应用
        if mcp_server_id:
            queryset = queryset.filter(mcp_server_id=mcp_server_id)

        # 获取唯一的 bk_app_code 列表
        bk_app_codes = queryset.values_list("bk_app_code", flat=True).distinct().order_by("bk_app_code")

        output_slz = MCPServerAppPermissionAppCodeListOutputSLZ(data={"bk_app_codes": list(bk_app_codes)})
        output_slz.is_valid(raise_exception=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="批量获取 MCPServer 配置（支持指定客户端类型：cursor, codebuddy, claude, vscode 等）",
        request_body=MCPServerBatchConfigInputSLZ,
        responses={status.HTTP_200_OK: MCPServerBatchConfigOutputSLZ()},
        tags=["WebAPI.MCPServer"],
    ),
)
class MCPServerBatchConfigApi(generics.CreateAPIView):
    """批量获取 MCPServer 配置，支持指定客户端类型"""

    def create(self, request, *args, **kwargs):
        slz = MCPServerBatchConfigInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        mcp_server_ids = slz.validated_data["mcp_server_ids"]
        client_type = slz.validated_data["client_type"]

        # 查询 MCPServer 列表
        instances = list(
            MCPServer.objects.filter(
                id__in=mcp_server_ids,
                gateway=request.gateway,
                status=MCPServerStatusEnum.ACTIVE.value,
            ).select_related("gateway", "stage")
        )

        if not instances:
            raise error_codes.NOT_FOUND.format(_("未找到有效的 MCPServer"), replace=True)

        # 获取最低权限信息（按 mcp_server.id 为 key）
        least_privileges = MCPServerHandler.get_least_privileges_by_server(instances)

        # 获取用户租户 ID
        user_tenant_id = get_user_tenant_id(request)

        # 构建批量配置
        config = MCPServerHandler.build_batch_agent_client_config(
            instances, client_type, least_privileges, user_tenant_id=user_tenant_id
        )

        # 查找客户端显示名称
        display_name = MCPServerHandler.get_client_display_name(client_type)

        result = {
            "client_type": client_type,
            "display_name": display_name,
            "config": config,
        }

        output_slz = MCPServerBatchConfigOutputSLZ(result)
        return OKJsonResponse(data=output_slz.data)


def _filter_gateway_app_permissions(queryset, data):
    """根据筛选条件过滤网关级 MCPServer 应用权限"""
    mcp_server_id = data.get("mcp_server_id")
    bk_app_code = data.get("bk_app_code")
    grant_type = data.get("grant_type")

    if mcp_server_id:
        queryset = queryset.filter(mcp_server_id=mcp_server_id)
    if bk_app_code:
        queryset = queryset.filter(bk_app_code__icontains=bk_app_code)
    if grant_type:
        queryset = queryset.filter(grant_type=grant_type)

    return queryset


def _order_gateway_app_permissions(queryset, order_by):
    """网关级 MCPServer 应用权限排序"""
    if order_by not in ["effective_time", "-effective_time"]:
        return queryset.order_by("mcp_server__name", "bk_app_code")

    approved_apply_handled_time = MCPServerAppPermissionApply.objects.filter(
        mcp_server_id=OuterRef("mcp_server_id"),
        bk_app_code=OuterRef("bk_app_code"),
        status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
        is_deleted=False,
    ).order_by("-handled_time", "-id")

    queryset = queryset.annotate(
        _effective_time=Case(
            When(
                grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
                then=Coalesce(
                    Subquery(approved_apply_handled_time.values("handled_time")[:1]),
                    F("created_time"),
                ),
            ),
            default=F("created_time"),
            output_field=DateTimeField(),
        )
    )
    order_field = "_effective_time" if order_by == "effective_time" else "-_effective_time"
    return queryset.order_by(order_field, "mcp_server__name", "bk_app_code")


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关下 MCPServer 应用权限列表",
        query_serializer=GatewayMCPServerAppPermissionListInputSLZ,
        responses={status.HTTP_200_OK: GatewayMCPServerAppPermissionListOutputSLZ(many=True)},
        tags=["WebAPI.MCPServer"],
    ),
)
class GatewayMCPServerAppPermissionListApi(generics.ListAPIView):
    def list(self, request, *args, **kwargs):
        slz = GatewayMCPServerAppPermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = MCPServerAppPermission.objects.filter(mcp_server__gateway=self.request.gateway).select_related(
            "mcp_server"
        )

        queryset = _filter_gateway_app_permissions(queryset, slz.validated_data)
        queryset = _order_gateway_app_permissions(queryset, slz.validated_data.get("order_by"))
        page = self.paginate_queryset(queryset)

        slz = GatewayMCPServerAppPermissionListOutputSLZ(
            page,
            many=True,
            context={
                "gateway_tenant_mode": self.request.gateway.tenant_mode,
                "gateway_tenant_id": self.request.gateway.tenant_id,
                "apply_record_map": MCPServerHandler.get_app_permission_apply_record_map(page),
            },
        )
        return self.get_paginated_response(slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="导出网关下 MCPServer 应用权限列表",
        request_body=GatewayMCPServerAppPermissionExportInputSLZ,
        responses={status.HTTP_200_OK: "file/csv"},
        tags=["WebAPI.MCPServer"],
    ),
)
class GatewayMCPServerAppPermissionExportApi(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        queryset = MCPServerAppPermission.objects.filter(mcp_server__gateway=self.request.gateway).select_related(
            "mcp_server"
        )

        if data["export_type"] == ExportTypeEnum.FILTERED.value:
            queryset = _filter_gateway_app_permissions(queryset, data)
        elif data["export_type"] == ExportTypeEnum.SELECTED.value:
            queryset = queryset.filter(id__in=data["selected_ids"])

        permissions = list(queryset.order_by("mcp_server__name", "bk_app_code"))
        slz = GatewayMCPServerAppPermissionListOutputSLZ(
            permissions,
            many=True,
            context={
                "gateway_tenant_mode": self.request.gateway.tenant_mode,
                "gateway_tenant_id": self.request.gateway.tenant_id,
                "apply_record_map": MCPServerHandler.get_app_permission_apply_record_map(permissions),
            },
        )

        content = self._get_csv_content(slz.data)
        filename = f"{self.request.gateway.name}-mcp_server_app_permissions.csv"

        response = DownloadableResponse(content, filename=filename)
        response.charset = "utf-8-sig" if "windows" in request.headers.get("User-Agent", "").lower() else "utf-8"
        return response

    def _get_csv_content(self, data):
        headers = [
            "mcp_server_name",
            "bk_app_code",
            "applied_by",
            "effective_time",
            "handled_by",
            "grant_type_display",
        ]
        header_row = {
            "mcp_server_name": _("MCPServer名称"),
            "bk_app_code": _("蓝鲸应用ID"),
            "applied_by": _("申请人"),
            "effective_time": _("生效时间"),
            "handled_by": _("审批人/授权人"),
            "grant_type_display": _("授权类型"),
        }

        rows = [
            {
                "mcp_server_name": item["mcp_server"]["name"],
                "bk_app_code": item["bk_app_code"],
                "applied_by": item["applied_by"],
                "effective_time": item["effective_time"],
                "handled_by": item["handled_by"],
                "grant_type_display": item["grant_type_display"],
            }
            for item in data
        ]

        content = StringIO()
        io_csv = csv.DictWriter(content, fieldnames=headers, extrasaction="ignore")
        io_csv.writerow(header_row)
        io_csv.writerows(rows)

        return content.getvalue()
