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

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.permissions import OpenAPIV2GatewayNamePermission, OpenAPIV2Permission
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import PermissionApplyExpireDaysEnum
from apigateway.apps.permission.tasks import send_mail_for_perm_apply
from apigateway.biz.gateway import GatewayHandler, GatewayTypeHandler
from apigateway.biz.mcp_server import MCPServerPermissionHandler
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.release import ReleaseHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id
from apigateway.components.bkauth import get_app_tenant_info
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Stage
from apigateway.service.contexts import GatewayAuthContext
from apigateway.utils.responses import OKJsonResponse

from . import serializers
from .serializers import (
    GatewayAppPermissionApplyOutputSLZ,
    MCPServerAppPermissionApplyRecordListOutputSLZ,
    MCPServerAppPermissionListInputSLZ,
    MCPServerAppPermissionListOutputSLZ,
    MCPServerAppPermissionRecordListInputSLZ,
    MCPServerListInputSLZ,
    MCPServerListOutputSLZ,
    MCPServerPermissionListOutputSLZ,
    UserMCPServerListInputSLZ,
    UserMCPServerListOutputSLZ,
)

# 注意：请使用 OpenAPIV2Permission / OpenAPIV2GatewayNamePermission, 有特殊情况请在类注释中说明

logger = logging.getLogger(__name__)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关列表，网关需公开且已发布",
        query_serializer=serializers.GatewayListInputSLZ,
        responses={status.HTTP_200_OK: serializers.GatewayListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
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
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayRetrieveApi(generics.RetrieveAPIView):
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


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建申请资源权限的申请单据",
        request_body=serializers.GatewayAppPermissionApplyInputSLZ,
        responses={status.HTTP_200_OK: GatewayAppPermissionApplyOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayAppPermissionApplyAPI(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.GatewayAppPermissionApplyInputSLZ

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        创建申请资源权限的申请单据
        """
        slz = self.get_serializer_class()(
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

        output_slz = GatewayAppPermissionApplyOutputSLZ({"record_id": record.id})

        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取公开的 MCPServer 列表",
        query_serializer=MCPServerListInputSLZ,
        responses={status.HTTP_200_OK: MCPServerListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        slz = MCPServerListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        # mcp server should be public and active
        queryset = MCPServer.objects.filter(is_public=True, status=MCPServerStatusEnum.ACTIVE.value)
        # gateway should be active
        queryset = queryset.filter(gateway__status=GatewayStatusEnum.ACTIVE.value)
        # the stage should be active and online
        queryset = queryset.filter(stage__status=StageStatusEnum.ACTIVE.value)

        if slz.validated_data.get("keyword"):
            queryset = queryset.filter(
                Q(name__icontains=slz.validated_data["keyword"])
                | Q(description__icontains=slz.validated_data["keyword"])
            )

        # optimize query by using select_related
        queryset = queryset.select_related("gateway", "stage")

        # note: the stage offline will update related mcp server status to inactive,
        # the stage publish will update the mcp server resource_names,
        # so we don't need to care about is the mcp server stage is correctly published here

        page = self.paginate_queryset(queryset)

        gateway_ids = list({mcp_server.gateway.id for mcp_server in page})
        gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids)
        gateways = {
            gateway.id: {
                "id": gateway.id,
                "name": gateway.name,
                "maintainers": gateway.maintainers,
                "is_official": GatewayTypeHandler.is_official(gateway_auth_configs[gateway.id].gateway_type),
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

        output_slz = MCPServerListOutputSLZ(
            page,
            many=True,
            context={
                "gateways": gateways,
                "stages": stages,
            },
        )

        return self.get_paginated_response(output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 app_code 的权限列表",
        query_serializer=MCPServerAppPermissionListInputSLZ,
        responses={status.HTTP_200_OK: MCPServerAppPermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerAppPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = MCPServerAppPermission.objects.filter(bk_app_code=slz.validated_data["bk_app_code"])
        page = self.paginate_queryset(queryset)
        output_slz = MCPServerAppPermissionListOutputSLZ(page, many=True)

        return self.get_paginated_response(output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 的权限列表",
        responses={status.HTTP_200_OK: MCPServerPermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]
    queryset = MCPServer.objects.all()
    lookup_url_kwarg = "mcp_server_id"

    def list(self, request, *args, **kwargs):
        instance = self.get_object()

        queryset = MCPServerAppPermission.objects.filter(mcp_server=instance)
        page = self.paginate_queryset(queryset)
        output_slz = MCPServerPermissionListOutputSLZ(page, many=True)

        return self.get_paginated_response(output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="指定应用发起 MCPServer 权限申请",
        request_body=serializers.MCPServerAppPermissionApplyCreateInputSLZ,
        responses={status.HTTP_200_OK: serializers.MCPServerAppPermissionApplyCreateOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
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
            data["bk_app_code"],
            data["mcp_server_ids"],
            data["reason"],
            data["applied_by"],
        )

        if len(queryset) == 0:
            raise error_codes.NOT_FOUND.format(
                "请检查对应 mcp server /环境/网关是否都已启用。",
                replace=True,
            )

        output_slz = serializers.MCPServerAppPermissionApplyCreateOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取指定应用的 MCPServer 权限申请记录列表",
        query_serializer=MCPServerAppPermissionRecordListInputSLZ,
        responses={status.HTTP_200_OK: MCPServerAppPermissionApplyRecordListOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerAppPermissionRecordListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        slz = MCPServerAppPermissionRecordListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = MCPServerAppPermissionApply.objects.filter(
            bk_app_code=data["bk_app_code"],
        )

        if data.get("mcp_server_id"):
            queryset = queryset.filter(mcp_server_id=data["mcp_server_id"])

        output_data = {}
        for obj in queryset.order_by("-applied_time"):
            if obj.mcp_server.id not in output_data:
                output_data[obj.mcp_server.id] = obj

        output_slz = MCPServerAppPermissionApplyRecordListOutputSLZ(output_data.values(), many=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 列表",
        query_serializer=UserMCPServerListInputSLZ,
        responses={status.HTTP_200_OK: UserMCPServerListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class UserMCPServerListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2Permission]

    def list(self, request, *args, **kwargs):
        slz = UserMCPServerListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = MCPServer.objects.filter(
            status=MCPServerStatusEnum.ACTIVE.value,
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
        )

        is_public = slz.validated_data.get("is_public", None)
        if is_public is None:
            # 查询全部
            queryset = queryset.filter(
                Q(is_public=True)
                | Q(
                    is_public=False,
                    gateway_id__in=[
                        gateway.id for gateway in GatewayHandler.list_gateways_by_user(request.user.username)
                    ],
                )
            )
        elif not is_public:
            queryset = queryset.filter(
                is_public=False,
                gateway_id__in=[gateway.id for gateway in GatewayHandler.list_gateways_by_user(request.user.username)],
            )
        else:
            queryset = queryset.filter(is_public=True)

        if slz.validated_data.get("keyword"):
            queryset = queryset.filter(
                Q(name__icontains=slz.validated_data["keyword"])
                | Q(description__icontains=slz.validated_data["keyword"])
            )

        # optimize query by using select_related
        queryset = queryset.select_related("gateway", "stage")

        # note: the stage offline will update related mcp server status to inactive,
        # the stage publish will update the mcp server resource_names,
        # so we don't need to care about is the mcp server stage is correctly published here

        page = self.paginate_queryset(queryset)

        gateway_ids = list({mcp_server.gateway.id for mcp_server in page})
        gateway_auth_configs = GatewayAuthContext().get_gateway_id_to_auth_config(gateway_ids)
        gateways = {
            gateway.id: {
                "id": gateway.id,
                "name": gateway.name,
                "maintainers": gateway.maintainers,
                "is_official": GatewayTypeHandler.is_official(gateway_auth_configs[gateway.id].gateway_type),
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

        output_slz = UserMCPServerListOutputSLZ(
            page,
            many=True,
            context={
                "gateways": gateways,
                "stages": stages,
            },
        )

        return self.get_paginated_response(output_slz.data)
