# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import logging
import operator
from typing import Dict

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.permissions import OpenAPIV2GatewayNamePermission, OpenAPIV2Permission
from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerPermissionActionEnum,
    MCPServerPermissionStatusEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import GrantDimensionEnum, GrantTypeEnum, PermissionApplyExpireDaysEnum
from apigateway.apps.permission.models import AppPermissionRecord, AppResourcePermission
from apigateway.apps.permission.tasks import send_mail_for_perm_apply
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.mcp_server import MCPServerHandler, MCPServerPermissionHandler
from apigateway.biz.permission import PermissionDimensionManager, ResourcePermissionHandler
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id
from apigateway.components.bkauth import get_app_tenant_info
from apigateway.controller.publisher.publish import trigger_gateway_publish
from apigateway.core.constants import GatewayStatusEnum, PublishSourceEnum
from apigateway.core.models import Gateway, Release
from apigateway.utils.responses import OKJsonResponse

from . import serializers
from .helpers import AppPermissionBuilder, ResourcePermissionBuilder

logger = logging.getLogger(__name__)


# 注意：请使用 OpenAPIV2Permission / OpenAPIV2GatewayNamePermission, 有特殊情况请在类注释中说明


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表，网关需公开且已发布",
        query_serializer=serializers.GatewayListInputSLZ,
        responses={status.HTTP_200_OK: serializers.GatewayListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayListApi(generics.ListAPIView):
    serializer_class = serializers.GatewayListOutputSLZ
    permission_classes = [OpenAPIV2Permission]

    def get_queryset(self):
        return Gateway.objects.all()

    def list(self, request, *args, **kwargs):
        """
        获取可用的网关列表
        - 1. 已启用
        - 2. 公开
        - 3. 已发布
        - 4. 满足 name 过滤条件
        """
        slz = serializers.GatewayListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        name = slz.validated_data.get("name")
        fuzzy = slz.validated_data.get("fuzzy")

        queryset = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        # 可以看到 全租户网关 + 本租户网关
        tenant_id = None
        if settings.ENABLE_MULTI_TENANT_MODE:
            if not request.tenant_id:
                raise ValidationError("tenant_id is required in multi-tenant mode")
            tenant_id = request.tenant_id
        if tenant_id:
            queryset = gateway_filter_by_app_tenant_id(queryset, tenant_id)

        if name:
            # 模糊匹配，查询名称中包含 name 的网关 or 精确匹配，查询名称为 name 的网关
            queryset = queryset.filter(name__contains=name) if fuzzy else queryset.filter(name=name)

        # 过滤出用户类型为指定类型的网关
        all_gateway_ids = list(queryset.values_list("id", flat=True))
        # 过滤出已发布的网关 ID
        released_gateway_ids = ReleaseHandler.filter_released_gateway_ids(all_gateway_ids)

        queryset = queryset.filter(id__in=released_gateway_ids)
        output_slz = self.get_serializer(queryset, many=True)
        output_data = sorted(output_slz.data, key=operator.itemgetter("name"))

        return OKJsonResponse(data=output_data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.GatewayRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
@method_decorator(
    name="delete",
    decorator=swagger_auto_schema(
        operation_description="删除网关，仅支持 bp- 开头的网关",
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayRetrieveDestroyApi(generics.RetrieveDestroyAPIView):
    """
    获取/删除网关
    - 删除：网关必须处于停用状态才能删除
    - 删除：仅支持 bp- 开头的网关，避免误操作
    """

    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.GatewayRetrieveOutputSLZ
    lookup_url_kwarg = "gateway_name"
    lookup_field = "name"

    def get_queryset(self):
        return Gateway.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance)
        return OKJsonResponse(data=slz.data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # 校验网关名称前缀
        _validate_gateway_name_prefix(instance.name)

        instance_id = instance.id

        # 网关为"停用"状态，才可以删除
        if instance.is_active:
            raise error_codes.FAILED_PRECONDITION.format(_("请先停用网关，然后再删除。"), replace=True)

        # 触发网关删除发布，只对已发布的 stage 进行下架
        # is_sync=True 因为需要先删除环境再删除数据库数据，否则异步任务会失败
        released_stage_ids = Release.objects.filter(gateway_id=instance_id).values_list("stage_id", flat=True)
        for stage_id in released_stage_ids:
            trigger_gateway_publish(
                PublishSourceEnum.GATEWAY_DELETE,
                request.user.username,
                instance_id,
                stage_id,
                is_sync=True,
                user_credentials=None,
            )

        # 删除网关及相关数据
        GatewayHandler.delete_gateway(instance_id)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.AppResourcePermissionListInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppResourcePermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayPermissionResourceListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]

    def list(self, request, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            return OKJsonResponse(data=[])

        slz = serializers.AppResourcePermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        resources = ResourceVersionHandler.get_released_public_resources(request.gateway.id)

        # 过滤掉不允许主动申请权限的资源
        resources = list(filter(lambda x: x["allow_apply_permission"], resources))

        resource_permissions = ResourcePermissionBuilder(
            self.request.gateway,
            slz.validated_data["target_app_code"],
        ).build(resources)

        slz = serializers.AppResourcePermissionListOutputSLZ(
            sorted(resource_permissions, key=operator.itemgetter("permission_level", "name")),
            many=True,
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.AppGatewayPermissionInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppGatewayPermissionOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayAppPermissionIsAllowedApplyCheckApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.AppGatewayPermissionInputSLZ

    def get(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        allow, reason = PermissionDimensionManager.get_manager(GrantDimensionEnum.API.value).allow_apply_permission(
            request.gateway.id, slz.validated_data["target_app_code"]
        )

        return OKJsonResponse(
            data={
                "allow_apply_by_gateway": allow,
                "reason": reason,
            }
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=serializers.GatewayAppPermissionApplyCreateInputSLZ,
        responses={status.HTTP_201_CREATED: serializers.GatewayAppPermissionApplyCreateOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayAppPermissionApplyCreateApi(generics.CreateAPIView):
    """
    PaaS 中应用申请访问网关 API 的权限
    - 提供给 paas3 开发者中心的接口
    """

    permission_classes = [OpenAPIV2GatewayNamePermission]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        创建申请资源权限的申请单据
        """
        slz = serializers.GatewayAppPermissionApplyCreateInputSLZ(
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        app_code = data["target_app_code"]
        # 全租户网关，谁都可以申请，单租户网关，只能本租户应用/全租户应用申请
        if settings.ENABLE_MULTI_TENANT_MODE and request.gateway.tenant_mode != TenantModeEnum.GLOBAL.value:
            gateway_tenant_id = request.gateway.tenant_id
            app_tenant_mode, app_tenant_id = get_app_tenant_info(app_code)
            if app_tenant_mode != TenantModeEnum.GLOBAL.value and app_tenant_id != gateway_tenant_id:
                raise error_codes.NO_PERMISSION.format(
                    f"app_code={app_code} is belongs to tenant {app_tenant_id}, should not apply the gateway of tenant {gateway_tenant_id}",
                    replace=True,
                )

        manager = PermissionDimensionManager.get_manager(data["grant_dimension"])
        record = manager.create_apply_record(
            app_code,
            request.gateway,
            data.get("resource_ids") or [],
            data["grant_dimension"],
            data["reason"],
            data.get("expire_days", PermissionApplyExpireDaysEnum.FOREVER.value),
            request.user.username,
        )

        try:
            apply_async_on_commit(send_mail_for_perm_apply, args=[record.id])
        except Exception:  # pylint: disable=broad-except
            logger.exception("send mail to gateway manager fail. apply_record_id=%s", record.id)

        return OKJsonResponse(
            status=status.HTTP_201_CREATED,
            data={
                "record_id": record.id,
            },
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="权限续期",
        request_body=serializers.AppPermissionRenewInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class AppPermissionRenewApi(generics.CreateAPIView):
    """
    权限续期
    """

    permission_classes = [OpenAPIV2Permission]

    def post(self, request, *args, **kwargs):
        slz = serializers.AppPermissionRenewInputSLZ(
            data=request.data,
            context={
                "request": request,
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        for gateway_id, resource_ids in ResourceHandler.group_by_gateway_id(data["resource_ids"]).items():
            gateway = Gateway.objects.get(id=gateway_id)
            # 如果应用 - 资源权限不存在，则将按网关的权限同步到应用 - 资源权限
            ResourcePermissionHandler.sync_from_gateway_permission(
                gateway=gateway,
                bk_app_code=data["target_app_code"],
                resource_ids=resource_ids,
            )
            AppResourcePermission.objects.renew_by_resource_ids(
                gateway=gateway,
                bk_app_code=data["target_app_code"],
                resource_ids=resource_ids,
                grant_type=GrantTypeEnum.RENEW.value,
                expire_days=data["expire_days"],
            )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.AppPermissionListInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppResourcePermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class AppPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        """已申请权限列表"""
        slz = serializers.AppPermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        permissions = AppPermissionBuilder(data["target_app_code"]).build()
        slz = serializers.AppResourcePermissionListOutputSLZ(permissions, many=True)
        output_data = sorted(slz.data, key=operator.itemgetter("gateway_name", "name"))
        return OKJsonResponse(data=output_data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.AppPermissionRecordListInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionRecordListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class AppPermissionRecordListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionRecordListInputSLZ

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = AppPermissionRecord.objects.all()
        queryset = AppPermissionRecord.objects.filter_record(
            queryset,
            bk_app_code=data["target_app_code"],
            applied_by=data.get("applied_by"),
            applied_time_start=data.get("applied_time_start"),
            applied_time_end=data.get("applied_time_end"),
            status=data.get("apply_status"),
            query=data.get("query"),
            order_by="-id",
        )

        page = self.paginate_queryset(queryset)
        slz = serializers.AppPermissionRecordListOutputSLZ(page, many=True)
        return self.get_paginated_response(slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        query_serializer=serializers.AppPermissionRecordRetrieveInputSLZ,
        responses={status.HTTP_200_OK: serializers.AppPermissionRecordOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class AppPermissionRecordRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.AppPermissionRecordRetrieveInputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return Gateway.objects.all()

    def get_object(self):
        record_id = self.kwargs["record_id"]

        slz = serializers.AppPermissionRecordRetrieveInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        try:
            return AppPermissionRecord.objects.get(bk_app_code=data["target_app_code"], id=record_id)
        except AppPermissionRecord.DoesNotExist:
            raise error_codes.NOT_FOUND

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        slz = serializers.AppPermissionRecordOutputSLZ(
            instance,
            context={
                "resource_id_map": ResourceHandler.get_id_to_resource(gateway_id=instance.gateway.id),
            },
        )
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="MCPServer 权限列表",
        query_serializer=serializers.MCPServerPermissionListInputSLZ,
        responses={status.HTTP_200_OK: serializers.MCPServerPermissionListOutputSLZ()},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class MCPServerPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        slz = serializers.MCPServerPermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = MCPServer.objects.filter(is_public=True, status=MCPServerStatusEnum.ACTIVE.value)

        keyword = data.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(description__icontains=keyword))

        mcp_server_permission_status: Dict[int, str] = {}
        mcp_server_permission_apply_status = (
            MCPServerAppPermissionApply.objects.filter(
                bk_app_code=data["target_app_code"],
                mcp_server_id__in=list(queryset.values_list("id", flat=True)),
                is_deleted=False,
            )
            .order_by("-applied_time")
            .values("mcp_server_id", "status", "handled_by")
        )

        mcp_server_permission_handled_by: Dict[int, str] = {}
        for obj in mcp_server_permission_apply_status:
            mcp_server_permission_handled_by[obj["mcp_server_id"]] = obj["handled_by"]
            if not mcp_server_permission_status.get(obj["mcp_server_id"]):
                mcp_server_permission_status[obj["mcp_server_id"]] = obj["status"]

        mcp_server_permissions = []
        for obj in queryset:
            permission_status = mcp_server_permission_status.get(
                obj.id, MCPServerPermissionStatusEnum.NEED_APPLY.value
            )
            handled_by = mcp_server_permission_handled_by.get(obj.id)

            if permission_status in [
                MCPServerPermissionStatusEnum.REJECTED.value,
                MCPServerPermissionStatusEnum.NEED_APPLY.value,
            ]:
                action = MCPServerPermissionActionEnum.APPLY.value
            else:
                action = ""

            mcp_server_permissions.append(
                {
                    "mcp_server": {
                        "id": obj.id,
                        "name": obj.name,
                        "title": obj.title or obj.name,
                        "description": obj.description,
                        "tools_count": obj.tools_count,
                        "tool_names": obj.resource_names,
                        "protocol_type": obj.protocol_type,
                    },
                    "permission": {
                        "status": permission_status,
                        "action": action,
                        "expires_in": None,
                        "handled_by": [handled_by] if handled_by else obj.gateway.maintainers,
                        "mcp_server_id": obj.id,
                        "gateway_id": obj.gateway_id,
                    },
                }
            )

        slz = serializers.MCPServerPermissionListOutputSLZ(mcp_server_permissions, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="MCPServer 申请权限/批量申请权限",
        request_body=serializers.MCPServerAppPermissionApplyCreateInputSLZ,
        responses={status.HTTP_200_OK: serializers.MCPServerAppPermissionApplyCreateOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class MCPServerAppPermissionApplyCreateApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.MCPServerAppPermissionApplyCreateInputSLZ

    def create(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = MCPServerPermissionHandler.create_apply(
            data["target_app_code"],
            data["mcp_server_ids"],
            data["reason"],
            data["applied_by"],
        )

        if queryset.count() == 0:
            raise error_codes.NOT_FOUND.format(
                "请检查对应 mcp server /环境/网关是否都已启用。",
                replace=True,
            )

        output_slz = serializers.MCPServerAppPermissionApplyCreateOutputSLZ(queryset, many=True)
        return OKJsonResponse(status=status.HTTP_200_OK, data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="MCPServer 已申请权限列表",
        query_serializer=serializers.MCPServerAppPermissionListInputSLZ,
        responses={status.HTTP_200_OK: serializers.MCPServerAppPermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class MCPServerAppPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.MCPServerAppPermissionListInputSLZ

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = MCPServerAppPermissionApply.objects.filter(
            bk_app_code=slz.validated_data["target_app_code"],
            status__in=[MCPServerAppPermissionApplyStatusEnum.APPROVED.value],
        ).order_by("-applied_time")

        mcp_server_permissions = [
            {
                "mcp_server": {
                    "id": obj.mcp_server_id,
                    "name": obj.mcp_server.name,
                    "title": obj.mcp_server.title or obj.mcp_server.name,
                    "description": obj.mcp_server.description,
                    "tools_count": obj.mcp_server.tools_count,
                    "tool_names": obj.mcp_server.resource_names,
                    "protocol_type": obj.mcp_server.protocol_type,
                },
                "permission": {
                    "status": MCPServerPermissionStatusEnum.OWNED.value,
                    "action": "",
                    "expires_in": None,
                    "handled_by": [obj.handled_by],
                    "mcp_server_id": obj.mcp_server_id,
                    "gateway_id": obj.mcp_server.gateway_id,
                },
            }
            for obj in queryset
        ]

        slz = serializers.MCPServerAppPermissionListOutputSLZ(mcp_server_permissions, many=True)
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="MCPServer 申请记录列表",
        query_serializer=serializers.MCPServerAppPermissionRecordListInputSLZ,
        responses={status.HTTP_200_OK: serializers.MCPServerAppPermissionRecordListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class MCPServerAppPermissionRecordListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]
    serializer_class = serializers.MCPServerAppPermissionRecordListInputSLZ

    def list(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = MCPServerPermissionHandler.filter_records(
            data["target_app_code"],
            data.get("applied_by"),
            data.get("apply_status"),
            data.get("query"),
            data.get("applied_time_start"),
            data.get("applied_time_end"),
        )

        mcp_server_permission_records = [
            {
                "mcp_server": {
                    "id": obj.mcp_server_id,
                    "name": obj.mcp_server.name,
                    "title": obj.mcp_server.title or obj.mcp_server.name,
                    "description": obj.mcp_server.description,
                    "tools_count": obj.mcp_server.tools_count,
                    "tool_names": obj.mcp_server.resource_names,
                    "protocol_type": obj.mcp_server.protocol_type,
                    "gateway_id": obj.mcp_server.gateway_id,  # 添加 gateway_id 用于构建审批 URL
                },
                "record": {
                    "id": obj.id,
                    "applied_by": obj.applied_by,
                    "applied_time": obj.applied_time,
                    "handled_by": [obj.handled_by] if obj.handled_by else obj.mcp_server.gateway.maintainers,
                    "handled_time": obj.handled_time,
                    "apply_status": obj.status,
                    "apply_status_display": MCPServerAppPermissionApplyStatusEnum.get_choice_label(obj.status),
                    "comment": obj.comment,
                    "reason": obj.reason,
                    "expire_days": obj.expire_days,
                    "mcp_server_id": obj.mcp_server_id,  # 添加 mcp_server_id 用于构建审批 URL
                    "gateway_id": obj.mcp_server.gateway_id,  # 在 record 中也添加 gateway_id
                },
            }
            for obj in queryset
        ]

        slz = serializers.MCPServerAppPermissionRecordListOutputSLZ(mcp_server_permission_records, many=True)

        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="MCPServer 申请记录详情",
        query_serializer=serializers.MCPServerAppPermissionRecordRetrieveInputSLZ,
        responses={status.HTTP_200_OK: serializers.MCPServerAppPermissionRecordRetrieveOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class MCPServerAppPermissionRecordRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2Permission]
    queryset = MCPServerAppPermissionApply.objects.all()
    serializer_class = serializers.MCPServerAppPermissionRecordRetrieveOutputSLZ
    lookup_field = "id"

    def get_object(self):
        record_id = self.kwargs["record_id"]

        slz = serializers.MCPServerAppPermissionRecordRetrieveInputSLZ(data=self.request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        try:
            return MCPServerAppPermissionApply.objects.get(bk_app_code=data["target_app_code"], id=record_id)
        except MCPServerAppPermissionApply.DoesNotExist:
            raise error_codes.NOT_FOUND

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        mcp_server_permission_record = {
            "mcp_server": {
                "id": instance.mcp_server_id,
                "name": instance.mcp_server.name,
                "title": instance.mcp_server.title or instance.mcp_server.name,
                "description": instance.mcp_server.description,
                "tools_count": instance.mcp_server.tools_count,
                "tool_names": instance.mcp_server.resource_names,
                "protocol_type": instance.mcp_server.protocol_type,
                "gateway_id": instance.mcp_server.gateway_id,  # 添加 gateway_id 用于构建审批 URL
            },
            "record": {
                "id": instance.id,
                "applied_by": instance.applied_by,
                "applied_time": instance.applied_time,
                "handled_by": [instance.handled_by]
                if instance.handled_by
                else instance.mcp_server.gateway.maintainers,
                "handled_time": instance.handled_time,
                "apply_status": instance.status,
                "apply_status_display": MCPServerAppPermissionApplyStatusEnum.get_choice_label(instance.status),
                "comment": instance.comment,
                "reason": instance.reason,
                "expire_days": instance.expire_days,
                "mcp_server_id": instance.mcp_server_id,  # 添加 mcp_server_id 用于构建审批 URL
                "gateway_id": instance.mcp_server.gateway_id,  # 在 record 中也添加 gateway_id
            },
        }

        slz = self.get_serializer(mcp_server_permission_record)
        return OKJsonResponse(data=slz.data)


# ===================== 网关状态变更/删除 API =====================

# 状态变更和删除操作限制只能操作 bp- 开头的网关，避免误操作
GATEWAY_STATUS_CHANGE_AND_DELETE_ALLOWED_PREFIX = "bp-"


def _validate_gateway_name_prefix(gateway_name: str) -> None:
    """校验网关名称前缀，状态变更和删除操作只允许操作 bp- 开头的网关"""
    if not gateway_name.startswith(GATEWAY_STATUS_CHANGE_AND_DELETE_ALLOWED_PREFIX):
        raise error_codes.INVALID_ARGUMENT.format(
            _("只允许操作以 '{prefix}' 开头的网关，当前网关名称：{name}").format(
                prefix=GATEWAY_STATUS_CHANGE_AND_DELETE_ALLOWED_PREFIX, name=gateway_name
            ),
            replace=True,
        )


@method_decorator(
    name="put",
    decorator=swagger_auto_schema(
        operation_description="更新网关状态（停用/启用），仅支持 bp- 开头的网关",
        request_body=serializers.GatewayUpdateStatusInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["OpenAPI.V2.Inner"],
    ),
)
class GatewayUpdateStatusApi(generics.UpdateAPIView):
    """
    更新网关状态
    - 停用网关：status=0
    - 启用网关：status=1
    - 仅支持 bp- 开头的网关，避免误操作
    """

    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.GatewayUpdateStatusInputSLZ
    lookup_url_kwarg = "gateway_name"
    lookup_field = "name"

    def get_queryset(self):
        return Gateway.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # 校验网关名称前缀
        _validate_gateway_name_prefix(instance.name)

        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        new_status = slz.validated_data["status"]
        is_need_publish = new_status != instance.status

        # 更新网关状态
        instance.status = new_status
        instance.save(update_fields=["status", "updated_time"])

        # 网关停用时，将网关下所有 MCPServer 设置为停用
        if new_status == GatewayStatusEnum.INACTIVE.value:
            MCPServerHandler.disable_servers(gateway_id=instance.id)

        # 触发网关发布
        if is_need_publish:
            source = PublishSourceEnum.GATEWAY_ENABLE if instance.is_active else PublishSourceEnum.GATEWAY_DISABLE
            trigger_gateway_publish(source, request.user.username, instance.id, user_credentials=None)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
