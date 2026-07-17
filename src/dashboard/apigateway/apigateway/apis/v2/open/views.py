# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import logging
import operator
import time
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.permissions import OpenAPIV2GatewayNamePermission, OpenAPIV2Permission
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerCategory,
)
from apigateway.apps.permission.constants import PermissionApplyExpireDaysEnum
from apigateway.apps.permission.tasks import send_mail_for_perm_apply
from apigateway.biz.access_log import LogHandler
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.mcp_server import MCPServerHandler, MCPServerPermissionHandler
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.released_resource_doc import DocGenerator, ReleasedResourceDocHandler
from apigateway.biz.resource_doc import ResourceDocHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.django.translation import get_current_language_code
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id
from apigateway.components.bkauth import get_app_tenant_info
from apigateway.core.constants import (
    GatewayKindNameEnum,
    GatewayStatusEnum,
    StageStatusEnum,
    convert_gateway_kind_name_to_value,
)
from apigateway.core.models import Gateway, Release, ReleasedResource, Resource, Stage
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper
from apigateway.service.contexts import ResourceAuthContext
from apigateway.service.resource import get_resource_id_to_labels, get_resource_url_tmpl
from apigateway.service.resource_version import get_resource_schema
from apigateway.utils.paginator import LimitOffsetPaginator
from apigateway.utils.responses import OKJsonResponse

from . import serializers
from .serializers import (
    GatewayAppPermissionApplyOutputSLZ,
    GatewayBatchQueryInputSLZ,
    GatewayBatchQueryOutputSLZ,
    GatewayResourceDetailInputSLZ,
    GatewayResourceDetailOutputSLZ,
    GatewayResourceListInputSLZ,
    GatewayResourceListOutputSLZ,
    GatewayResourceRetrieveByNameOutputSLZ,
    GetCurrentUnixTimestampOutputSLZ,
    GetDatetimeInputSLZ,
    GetDatetimeOutputSLZ,
    LogSearchByRequestIdInputSLZ,
    LogSearchByRequestIdOutputSLZ,
    MCPServerAppPermissionApplyRecordListOutputSLZ,
    MCPServerAppPermissionListInputSLZ,
    MCPServerAppPermissionListOutputSLZ,
    MCPServerAppPermissionRecordListInputSLZ,
    MCPServerBatchQueryInputSLZ,
    MCPServerBatchQueryOutputSLZ,
    MCPServerCategoryListOutputSLZ,
    MCPServerListInputSLZ,
    MCPServerListOutputSLZ,
    MCPServerPermissionListOutputSLZ,
    MCPServerRetrieveOutputSLZ,
    OAuthProtectedResourceInputSLZ,
    ParseDatetimeStrToTimestampInputSLZ,
    ParseDatetimeStrToTimestampOutputSLZ,
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
        - 4. 满足 name / keyword / kind 过滤条件
        """
        slz = serializers.GatewayListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        name = slz.validated_data.get("name")
        fuzzy = slz.validated_data.get("fuzzy")
        keyword = slz.validated_data.get("keyword")
        kind = slz.validated_data.get("kind")

        queryset = GatewayHandler.list_public_released_gateways()

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

        if keyword:
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(description__icontains=keyword))

        if kind:
            kind_query = Q(kind=convert_gateway_kind_name_to_value(kind))
            if kind == GatewayKindNameEnum.NORMAL.value:
                kind_query |= Q(kind__isnull=True)
            queryset = queryset.filter(kind_query)

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

        resource_ids = data.get("resource_ids") or []

        manager = PermissionDimensionManager.get_manager(data["grant_dimension"])
        record = manager.create_apply_record(
            app_code,
            request.gateway,
            resource_ids,
            data["grant_dimension"],
            data["reason"],
            data.get("expire_days", PermissionApplyExpireDaysEnum.FOREVER.value),
            data["applicant"],
        )

        # ITSM 单据创建成功后，不再发送邮件通知
        if not record.itsm_ticket_id:
            try:
                apply_async_on_commit(send_mail_for_perm_apply, args=[record.id])
            except Exception:  # pylint: disable=broad-except
                logger.exception("send mail to gateway manager fail. apply_record_id=%s", record.id)

        output_slz = GatewayAppPermissionApplyOutputSLZ(
            {
                "record_id": record.id,
                "itsm_ticket_id": record.itsm_ticket_id or "",
                "itsm_ticket_url": ItsmPermissionApplyHelper.build_ticket_url(record.itsm_ticket_id),
            }
        )

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

        queryset = MCPServerHandler.build_list_queryset(
            keyword=slz.validated_data.get("keyword"),
            category=slz.validated_data.get("category"),
            is_public=True,
            order_by="-updated_time",
        )

        page = self.paginate_queryset(queryset)
        context = MCPServerHandler.build_list_context(page)

        # Add categories map
        context["categories"] = MCPServerHandler.build_categories_map([mcp_server.id for mcp_server in page])

        output_slz = MCPServerListOutputSLZ(page, many=True, context=context)
        return self.get_paginated_response(output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 MCPServer 分类列表",
        responses={status.HTTP_200_OK: MCPServerCategoryListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerCategoryListApi(generics.ListAPIView):
    """获取所有已激活的 MCPServer 分类"""

    permission_classes = [OpenAPIV2Permission]
    serializer_class = MCPServerCategoryListOutputSLZ

    def list(self, request, *args, **kwargs):
        queryset = MCPServerCategory.objects.filter(is_active=True).order_by("name")
        output_slz = self.get_serializer(queryset, many=True)
        return OKJsonResponse(data=output_slz.data)


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

        # Build categories map
        categories_map = MCPServerHandler.build_categories_map([perm.mcp_server_id for perm in page])

        output_slz = MCPServerAppPermissionListOutputSLZ(page, many=True, context={"categories": categories_map})

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

        # Build categories map
        categories_map = MCPServerHandler.build_categories_map([instance.id])

        output_slz = MCPServerPermissionListOutputSLZ(page, many=True, context={"categories": categories_map})

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

        if queryset.count() == 0:
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

        if data.get("record_id"):
            queryset = queryset.filter(id=data["record_id"])

        output_data = {}
        for obj in queryset.order_by("-applied_time"):
            if obj.mcp_server.id not in output_data:
                output_data[obj.mcp_server.id] = obj

        # Build categories map
        categories_map = MCPServerHandler.build_categories_map(list(output_data.keys()))

        output_slz = MCPServerAppPermissionApplyRecordListOutputSLZ(
            output_data.values(), many=True, context={"categories": categories_map}
        )
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
                | Q(title__icontains=slz.validated_data["keyword"])
                | Q(description__icontains=slz.validated_data["keyword"])
            )

        # optimize query by using select_related
        queryset = queryset.select_related("gateway", "stage")

        # note: the stage offline will update related mcp server status to inactive,
        # the stage publish will update the mcp server resource_names,
        # so we don't need to care about is the mcp server stage is correctly published here

        page = self.paginate_queryset(queryset)

        gateway_ids = list({mcp_server.gateway.id for mcp_server in page})
        gateways = {
            gateway.id: {
                "id": gateway.id,
                "name": gateway.name,
                "maintainers": gateway.maintainers,
                "is_official": gateway.is_official,
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

        least_privileges = MCPServerHandler.get_least_privileges(page)

        # Add categories map
        categories_map = MCPServerHandler.build_categories_map([mcp_server.id for mcp_server in page])

        output_slz = UserMCPServerListOutputSLZ(
            page,
            many=True,
            context={
                "gateways": gateways,
                "stages": stages,
                "least_privileges": least_privileges,
                "categories": categories_map,
            },
        )

        return self.get_paginated_response(output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关下的所有资源列表",
        query_serializer=GatewayResourceListInputSLZ,
        responses={status.HTTP_200_OK: GatewayResourceListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayResourceListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = GatewayResourceListOutputSLZ

    def get_queryset(self):
        return Resource.objects.all()

    def list(self, request, *args, **kwargs):
        """
        获取网关下的所有资源列表
        - 只返回公开的资源
        - 支持 fields 参数指定返回字段，如 fields=id,name
        - 支持 keyword 模糊搜索 name、description 和标签名称
        """
        slz = GatewayResourceListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        queryset = Resource.objects.filter(
            gateway=request.gateway,
            is_public=True,
        ).order_by("-updated_time")

        if slz.validated_data.get("keyword"):
            queryset = queryset.filter(
                Q(name__icontains=slz.validated_data["keyword"])
                | Q(description__icontains=slz.validated_data["keyword"])
                | Q(resourcelabel__api_label__name__icontains=slz.validated_data["keyword"])
            ).distinct()

        resources = list(queryset)
        fields_str = slz.validated_data.get("fields")

        resource_ids = [resource.id for resource in resources]
        output_slz = self.get_serializer(
            resources,
            many=True,
            context={
                "labels": get_resource_id_to_labels(resource_ids),
                "auth_configs": ResourceAuthContext().get_resource_id_to_auth_config(resource_ids),
            },
        )

        data = output_slz.data
        allowed_fields = {"id", "name"}
        if fields_str:
            allowed_fields = {f.strip() for f in fields_str.split(",") if f.strip()}
        data = [{k: v for k, v in item.items() if k in allowed_fields} for item in data]

        return OKJsonResponse(data=data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关资源的详细信息，包含文档和 Schema",
        query_serializer=GatewayResourceDetailInputSLZ(),
        responses={status.HTTP_200_OK: GatewayResourceDetailOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayResourceDetailApi(generics.RetrieveAPIView):
    """获取网关资源详情接口"""

    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = GatewayResourceDetailOutputSLZ

    def get_queryset(self):
        return Resource.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """
        获取网关资源的详细信息
        - 包含资源基本信息
        - 包含资源文档（Markdown格式）
        - 包含资源 OpenAPI Schema 定义
        - 包含认证配置
        """
        # 验证查询参数
        slz = GatewayResourceDetailInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        stage_name = slz.validated_data["stage_name"]
        resource_name = self.kwargs.get("resource_name")

        # 获取该环境下已发布的资源版本 ID
        resource_version_id = Release.objects.get_released_resource_version_id(request.gateway.id, stage_name)
        if not resource_version_id:
            raise error_codes.NOT_FOUND.format(_("该环境下未找到已发布的资源版本"), replace=True)

        # 获取资源数据和文档数据
        resource_data, doc_data = ReleasedResourceDocHandler.get_released_resource_doc_data(
            gateway_id=request.gateway.id,
            stage_name=stage_name,
            resource_name=resource_name,
            language=ResourceDocHandler.get_doc_language(get_current_language_code()),
        )

        # 检查资源是否存在
        if not resource_data:
            raise error_codes.NOT_FOUND.format(
                _("资源【{resource_name}】不存在").format(resource_name=resource_name), replace=True
            )

        # 只返回公开的资源
        if not resource_data.is_public:
            raise error_codes.NOT_FOUND.format(
                _("资源【{resource_name}】不存在").format(resource_name=resource_name), replace=True
            )

        # 获取资源 OpenAPI Schema
        resource_schema = get_resource_schema(resource_version_id, resource_data.id)

        # 生成文档信息
        doc_info = self._generate_doc_info(request.gateway, stage_name, resource_data, doc_data)

        # 组装返回数据
        result = {
            "id": resource_data.id,
            "name": resource_data.name,
            "kind": resource_data.kind,
            "description": resource_data.description,
            "description_en": resource_data.description_en,
            "method": resource_data.method,
            "path": resource_data.path,
            "match_subpath": resource_data.match_subpath,
            "enable_websocket": resource_data.enable_websocket,
            "is_public": resource_data.is_public,
            "schema": resource_schema or {},
            "doc": doc_info,
            "auth_config": {
                "user_verified_required": resource_data.verified_user_required,
                "app_verified_required": resource_data.verified_app_required,
                "resource_perm_required": resource_data.resource_perm_required,
            },
        }

        output_slz = self.get_serializer(result)
        return OKJsonResponse(data=output_slz.data)

    def _generate_doc_info(self, gateway, stage_name, resource_data, doc_data):
        """生成文档信息"""
        if not doc_data:
            return None
        try:
            generator = DocGenerator(
                gateway=gateway,
                stage_name=stage_name,
                resource_data=resource_data,
                doc_data=doc_data,
                language=ResourceDocHandler.get_doc_language(get_current_language_code()),
            )
            doc = generator.get_doc()
            return {
                "type": doc.get("type"),
                "content": doc.get("content"),
                "updated_time": doc.get("updated_time"),
            }
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "generate doc failed, gateway_id=%s, stage_name=%s, resource_name=%s",
                gateway.id,
                stage_name,
                resource_data.name,
            )
            return None


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="查询指定环境下已发布资源列表",
        responses={status.HTTP_200_OK: serializers.GatewayReleasedResourceListItemOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayReleasedResourceListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]

    def list(self, request, gateway_name, stage_name, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resources = ResourceVersionHandler.get_released_public_resources(request.gateway.id, stage_name=stage_name)
        paginator = LimitOffsetPaginator(count=len(resources), offset=0, limit=len(resources))
        output_slz = serializers.GatewayReleasedResourceListItemOutputSLZ(
            resources,
            many=True,
            context={
                "resource_url_tmpl": get_resource_url_tmpl(),
                "gateway_name": request.gateway.name,
                "stage_name": stage_name,
            },
        )
        return OKJsonResponse(data=paginator.get_paginated_data(output_slz.data))


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="查询指定环境下已发布资源详情",
        responses={status.HTTP_200_OK: serializers.GatewayReleasedResourceOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayReleasedResourceRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = serializers.GatewayReleasedResourceOutputSLZ

    def get_object(self):
        if not self.request.gateway.is_active_and_public:
            raise Http404

        stage_name = self.kwargs["stage_name"]
        resource_name = self.kwargs["resource_name"]

        resource_version_id = Release.objects.get_released_resource_version_id(self.request.gateway.id, stage_name)
        if not resource_version_id:
            raise Http404

        resource = ReleasedResource.objects.get_released_resource(
            self.request.gateway.id, resource_version_id, resource_name
        )
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"]:
            raise Http404

        resource["schema"] = get_resource_schema(resource_version_id, resource["id"])
        return resource

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return OKJsonResponse(data=serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取单个 MCPServer 的详细信息（用户态接口）",
        responses={status.HTTP_200_OK: MCPServerRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerRetrieveApi(generics.RetrieveAPIView):
    """
    获取单个 MCPServer 的详细信息
    - 用户态接口，需要用户认证权限验证
    - 返回内容涵盖 MCP 市场详情页所需信息
    """

    permission_classes = [OpenAPIV2Permission]
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerRetrieveOutputSLZ
    lookup_url_kwarg = "mcp_server_id"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        context = MCPServerHandler.build_retrieve_context(
            instance,
            check_public=True,
            username=request.user.username,
        )

        serializer = self.get_serializer(instance, context=context)
        return OKJsonResponse(data=serializer.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取当前时间",
        query_serializer=GetDatetimeInputSLZ,
        responses={status.HTTP_200_OK: GetDatetimeOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GetDatetimeApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        # get tz_name from request.params
        slz = GetDatetimeInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        tz_name = slz.validated_data.get("tz_name")
        # default tz_name is Asia/Shanghai
        if not tz_name:
            tz_name = settings.TIME_ZONE

        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            raise error_codes.INVALID_ARGUMENT.format(
                _("时区【{tz_name}】不存在").format(tz_name=tz_name), replace=True
            )

        current_time = datetime.now(tz)
        slz = GetDatetimeOutputSLZ({"datetime": current_time.strftime("%Y-%m-%d %H:%M:%S")})
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取当前时间",
        responses={status.HTTP_200_OK: GetCurrentUnixTimestampOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GetCurrentUnixTimestampApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        slz = GetCurrentUnixTimestampOutputSLZ({"unix_timestamp": int(time.time())})
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="将时间字符串转换为时间戳",
        request_body=ParseDatetimeStrToTimestampInputSLZ,
        responses={status.HTTP_200_OK: ParseDatetimeStrToTimestampOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class ParseDatetimeStrToTimestampApi(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        slz = ParseDatetimeStrToTimestampInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        datetime_str = slz.validated_data.get("datetime")
        datetime_format = slz.validated_data.get("datetime_format", "%Y-%m-%d %H:%M:%S")

        try:
            datetime_obj = datetime.strptime(datetime_str, datetime_format)
        except ValueError:
            raise error_codes.INVALID_ARGUMENT.format(
                _("时间字符串格式错误").format(datetime_str=datetime_str), replace=True
            )

        timestamp = int(time.mktime(datetime_obj.timetuple()))

        slz = ParseDatetimeStrToTimestampOutputSLZ({"timestamp": timestamp})
        return OKJsonResponse(data=slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="根据 request_id 查询日志",
        query_serializer=LogSearchByRequestIdInputSLZ,
        responses={status.HTTP_200_OK: LogSearchByRequestIdOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class LogSearchByRequestIdApi(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        slz = LogSearchByRequestIdInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        request_id = slz.validated_data.get("request_id")

        total_count, logs = LogHandler.search_logs_by_request_id(request_id)

        output_slz = LogSearchByRequestIdOutputSLZ(logs, many=True)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="批量根据网关名称查询网关展示名称和描述",
        request_body=GatewayBatchQueryInputSLZ,
        responses={status.HTTP_200_OK: GatewayBatchQueryOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayBatchQueryApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2Permission]

    def create(self, request, *args, **kwargs):
        slz = GatewayBatchQueryInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        queryset = Gateway.objects.filter(
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
        )

        if slz.validated_data.get("ids"):
            queryset = queryset.filter(id__in=slz.validated_data["ids"])
        if slz.validated_data.get("names"):
            queryset = queryset.filter(name__in=slz.validated_data["names"])

        output_slz = GatewayBatchQueryOutputSLZ(queryset, many=True)
        data = output_slz.data

        allowed_fields = {"id", "name"}
        fields_str = slz.validated_data.get("fields")
        if fields_str:
            allowed_fields = {f.strip() for f in fields_str.split(",") if f.strip()}
        data = [{k: v for k, v in item.items() if k in allowed_fields} for item in data]

        return OKJsonResponse(data=data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="根据资源名称获取网关下单个资源的基本信息",
        responses={status.HTTP_200_OK: GatewayResourceRetrieveByNameOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class GatewayResourceRetrieveByNameApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayNamePermission]
    serializer_class = GatewayResourceRetrieveByNameOutputSLZ
    lookup_url_kwarg = "resource_name"
    lookup_field = "name"

    def get_queryset(self):
        return Resource.objects.all()

    def retrieve(self, request, *args, **kwargs):
        resource_name = self.kwargs.get("resource_name")
        resource = Resource.objects.filter(
            gateway=request.gateway,
            name=resource_name,
        ).first()

        if not resource:
            raise error_codes.NOT_FOUND.format(
                _("资源【{resource_name}】不存在").format(resource_name=resource_name), replace=True
            )

        output_slz = self.get_serializer(resource)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="批量根据 MCPServer 名称查询 MCPServer 展示名称、描述和分类",
        request_body=MCPServerBatchQueryInputSLZ,
        responses={status.HTTP_200_OK: MCPServerBatchQueryOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Open"],
    ),
)
class MCPServerBatchQueryApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2Permission]

    def create(self, request, *args, **kwargs):
        slz = MCPServerBatchQueryInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        queryset = MCPServer.objects.filter(
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        if slz.validated_data.get("ids"):
            queryset = queryset.filter(id__in=slz.validated_data["ids"])
        if slz.validated_data.get("names"):
            queryset = queryset.filter(name__in=slz.validated_data["names"])

        queryset = queryset.prefetch_related("categories")

        categories_map = {
            mcp_server.id: [
                {"name": cat.name, "display_name": cat.display_name}
                for cat in mcp_server.categories.filter(is_active=True)
            ]
            for mcp_server in queryset
        }

        output_slz = MCPServerBatchQueryOutputSLZ(
            queryset,
            many=True,
            context={"categories": categories_map},
        )
        data = output_slz.data

        allowed_fields = {"id", "name"}
        fields_str = slz.validated_data.get("fields")
        if fields_str:
            allowed_fields = {f.strip() for f in fields_str.split(",") if f.strip()}
        data = [{k: v for k, v in item.items() if k in allowed_fields} for item in data]

        return OKJsonResponse(data=data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取 OAuth 保护资源元数据",
        query_serializer=OAuthProtectedResourceInputSLZ,
        responses={status.HTTP_200_OK: "OAuth Protected Resource Metadata"},
        tags=["OpenAPI.V2.Open"],
    ),
)
class OAuthProtectedResourceApi(generics.RetrieveAPIView):
    """OAuth Protected Resource Metadata endpoint (RFC 9728)"""

    permission_classes = []  # type: ignore  # No permission check required

    def retrieve(self, request, *args, **kwargs):
        slz = OAuthProtectedResourceInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        resource = slz.validated_data["resource"]

        return JsonResponse(
            {
                "resource": resource,
                "authorization_servers": [settings.BK_AUTH_SERVER_URL],
                "bearer_methods_supported": ["header"],
            }
        )
