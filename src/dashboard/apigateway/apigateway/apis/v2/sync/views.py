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

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.permissions import OpenAPIV2GatewayRelatedAppPermission
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.tasks import sync_mcp_server_after_release
from apigateway.apps.permission.constants import FormattedGrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppResourcePermission,
)
from apigateway.biz.audit import Auditor
from apigateway.biz.data_plane import DataPlaneHandler
from apigateway.biz.gateway import GatewayHandler, GatewayRelatedAppHandler
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.resource.importer import sync_openapi_resources_from_content
from apigateway.biz.resource_doc import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.biz.resource_doc.importer import ArchiveParser, DocImporter
from apigateway.biz.resource_version import ResourceVersionArtifactHandler, ResourceVersionHandler
from apigateway.biz.sdk.orchestrator import create_or_resume_generation
from apigateway.biz.sdk.tasks import enqueue_generation_items
from apigateway.common.constants import CallSourceTypeEnum
from apigateway.common.error_codes import error_codes
from apigateway.components.bkauth import get_app_tenant_info
from apigateway.core.constants import ReleaseHistoryStatusEnum, ReleaseStatusEnum
from apigateway.core.models import JWT, Gateway, Release, Resource, ResourceVersion, Stage
from apigateway.utils.django import get_model_dict, get_object_or_None
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

from . import serializers
from .serializers import (
    DocImportByArchiveInputSLZ,
    GatewayPublicKeyRetrieveOutputSLZ,
    GatewayResourceVersionLatestRetrieveOutputSLZ,
    GatewaySyncOutputSLZ,
    ReleaseInputSLZ,
    ReleaseOutputSLZ,
    ResourceImportInputSLZ,
    ResourceSyncOutputSLZ,
    ResourceVersionCreateInputSLZ,
    ResourceVersionCreateOutputSLZ,
    ResourceVersionListInputSLZ,
    ResourceVersionListOutputSLZ,
    SDKGenerateInputSLZ,
    SDKGenerateOutputSLZ,
    StageMcpServersSyncInputSLZ,
    StageMcpServersSyncOutputSLZ,
    StageSyncInputSLZ,
    StageSyncOutputSLZ,
)

# 注意：请使用 OpenAPIV2GatewayRelatedAppPermission, 有特殊情况请在类注释中说明
logger = logging.getLogger(__name__)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="同步网关",
        request_body=serializers.GatewaySyncInputSLZ,
        responses={status.HTTP_200_OK: GatewaySyncOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewaySyncApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    allow_gateway_not_exist = True
    serializer_class = serializers.GatewaySyncInputSLZ

    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        gateway = getattr(request, "gateway", None)

        data_before = get_model_dict(gateway) if gateway else {}

        request.data["name"] = gateway_name
        # gateway 为 None，则应为新建；非 None，则应为更新；
        # slz 中仅校验数据，不保存网关数据，利用 GatewaySaver 处理网关的保存；
        # 抽象出 GatewaySaver，是因 django command 中需要复用此 saver 中保存网关数据的逻辑
        slz = self.get_serializer(gateway, data=request.data)
        slz.is_valid(raise_exception=True)

        # assign the tenant_mode and tenant_id based on the calling app
        tenant_mode, tenant_id = get_app_tenant_info(request.app.app_code)
        slz.validated_data["tenant_mode"] = tenant_mode
        slz.validated_data["tenant_id"] = tenant_id

        # save gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR

        data_plane_ids = DataPlaneHandler.get_sync_data_plane_ids(
            gateway_name=gateway_name,
            data_plane_names=slz.validated_data.get("data_planes"),
        )

        gateway = GatewayHandler.sync_gateway(
            gateway,
            slz.validated_data,
            request.app.app_code,
            username,
            None,
            data_plane_ids,
        )

        # record audit log
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY if slz.instance else OpTypeEnum.CREATE,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before=data_before,
            data_after=get_model_dict(gateway),
        )

        output_slz = GatewaySyncOutputSLZ(instance=gateway)
        return OKJsonResponse(
            data=output_slz.data,
        )


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关公钥",
        responses={status.HTTP_200_OK: GatewayPublicKeyRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayPublicKeyRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    def get(self, request, gateway_name: str, *args, **kwargs):
        jwt = JWT.objects.get(gateway=request.gateway)
        output_slz = GatewayPublicKeyRetrieveOutputSLZ(
            {
                "issuer": getattr(settings, "JWT_ISSUER", ""),
                "public_key": jwt.public_key,
            }
        )
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="同步网关stage",
        request_body=StageSyncInputSLZ,
        responses={status.HTTP_200_OK: StageSyncOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayStageSyncViewSet(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    def post(self, request, *args, **kwargs):
        instance = get_object_or_None(Stage, gateway=request.gateway, name=request.data.get("name", ""))
        data_before = get_model_dict(instance) if instance else {}
        slz = StageSyncInputSLZ(
            instance,
            data=request.data,
            context={
                "request": request,
                "allow_var_not_exist": True,
            },
        )
        slz.is_valid(raise_exception=True)

        stage = slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        Auditor.record_stage_op_success(
            op_type=OpTypeEnum.MODIFY if instance else OpTypeEnum.CREATE,
            username=request.user.username or settings.GATEWAY_DEFAULT_CREATOR,
            gateway_id=request.gateway.id,
            instance_id=stage.id,
            instance_name=stage.name,
            data_before=data_before,
            data_after=get_model_dict(stage),
        )
        output_slz = StageSyncOutputSLZ(instance=stage)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="同步网关resources",
        request_body=serializers.ResourceImportInputSLZ,
        responses={status.HTTP_200_OK: ResourceSyncOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayResourceSyncApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    def get_queryset(self):
        return Resource.objects.filter(gateway=self.request.gateway)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        slz = ResourceImportInputSLZ(
            data=request.data,
            context={
                "gateway": request.gateway,
            },
        )
        slz.is_valid(raise_exception=True)

        ok, message, data = sync_openapi_resources_from_content(
            gateway=request.gateway,
            username=request.user.username,
            content=slz.validated_data["content"],
            delete_missing_resources=slz.validated_data["delete"],
            doc_language=slz.validated_data.get("doc_language", ""),
        )
        if not ok:
            raise ValidationError({"content": _("{err}").format(err=message)})

        slz = ResourceSyncOutputSLZ(data)
        return OKJsonResponse(data=slz.data)


class DocImportByArchiveApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    @swagger_auto_schema(
        operation_description="根据 tgz/zip 归档文件，导入资源文档",
        request_body=DocImportByArchiveInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.V2.Sync"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """根据 tgz/zip 归档文件，导入资源文档"""
        slz = DocImportByArchiveInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        parser = ArchiveParser(gateway_id=request.gateway.id)
        try:
            docs = parser.parse(slz.validated_data["file"])
        except NoResourceDocError:
            raise error_codes.INVALID_ARGUMENT.format(
                _("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"), replace=True
            )
        except ResourceDocJinja2TemplateError as err:
            raise error_codes.INTERNAL.format(_("导入资源文档失败，{err}。").format(err=err), replace=True)

        importer = DocImporter(gateway_id=request.gateway.id, selected_resource_docs=None)
        importer.import_docs(docs=docs)

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="添加网关关联的应用",
        request_body=serializers.GatewayRelatedAppsAddInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayRelatedAppAddApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayRelatedAppsAddInputSLZ

    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        input_app_codes = slz.validated_data["related_app_codes"]

        if settings.ENABLE_MULTI_TENANT_MODE:
            # check if all the target_app_codes are in the same tenant
            for app_code in input_app_codes:
                _, app_tenant_id = get_app_tenant_info(app_code)
                if app_tenant_id != request.gateway.tenant_id:
                    raise ValidationError(
                        {
                            "target_app_codes": f"app_code {app_code} not belong to the tenant {request.gateway.tenant_id}"
                        }
                    )

        related_app_codes_before, related_app_codes_after = GatewayRelatedAppHandler.sync_related_apps(
            gateway_id=request.gateway.id,
            bk_app_codes=input_app_codes,
        )

        # record audit log
        gateway = request.gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before={"related_app_codes": related_app_codes_before},
            data_after={"related_app_codes": related_app_codes_after},
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关权限列表",
        query_serializer=serializers.GatewayPermissionListInputSLZ(),
        responses={status.HTTP_200_OK: serializers.GatewayPermissionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayPermissionListApi(generics.ListAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayPermissionListInputSLZ

    def _get_queryset(self, gateway: Gateway, bk_app_code: str, grant_dimension: str):
        if grant_dimension == FormattedGrantDimensionEnum.GATEWAY.value:
            gateway_permissions_queryset = AppGatewayPermission.objects.filter(gateway=gateway)

            if bk_app_code:
                gateway_permissions_queryset = gateway_permissions_queryset.filter(bk_app_code=bk_app_code)

            return gateway_permissions_queryset.order_by("-id")

        resource_ids = Resource.objects.filter(gateway=gateway).values_list("id", flat=True)
        resource_permissions_queryset = AppResourcePermission.objects.filter(
            gateway=gateway, resource_id__in=resource_ids
        ).exclude(bk_app_code=settings.DEFAULT_TEST_APP["bk_app_code"])

        if bk_app_code:
            resource_permissions_queryset = resource_permissions_queryset.filter(bk_app_code=bk_app_code)

        return resource_permissions_queryset.order_by("-id")

    def get(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.query_params)
        slz.is_valid(raise_exception=True)

        bk_app_code = slz.validated_data.get("bk_app_code")
        grant_dimension = slz.validated_data.get("grant_dimension")

        queryset = self._get_queryset(request.gateway, bk_app_code, grant_dimension)

        paginated_data = self.paginate_queryset(queryset)
        data = []
        resource_ids = []
        for perm in paginated_data:
            if grant_dimension == FormattedGrantDimensionEnum.GATEWAY.value:
                data.append(
                    {
                        "bk_app_code": perm.bk_app_code,
                        "expires": perm.expires,
                        "grant_dimension": FormattedGrantDimensionEnum.GATEWAY.value,
                        "id": perm.id,
                    }
                )
            else:
                resource_ids.append(perm.resource_id)
                data.append(
                    {
                        "bk_app_code": perm.bk_app_code,
                        # "grant_type": perm.grant_type,
                        "resource_id": perm.resource_id,
                        "expires": perm.expires,
                        "grant_dimension": FormattedGrantDimensionEnum.RESOURCE.value,
                        "id": perm.id,
                    }
                )
        if resource_ids:
            resources = Resource.objects.filter(id__in=resource_ids)
            resource_map = {resource.id: resource for resource in resources}
            for item in data:
                if item.get("resource_id") and resource_map.get(item["resource_id"]):
                    item["resource_name"] = resource_map.get(item["resource_id"]).name

        return self.get_paginated_response(data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="网关关联应用，主动为应用授权访问网关 API 的权限",
        request_body=serializers.GatewayAppPermissionGrantInputSLZ,
        responses={status.HTTP_201_CREATED: ""},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayAppPermissionGrantApi(generics.CreateAPIView):
    """网关关联应用，主动为应用授权访问网关 API 的权限"""

    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = serializers.GatewayAppPermissionGrantInputSLZ

    def post(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        resource_ids = list(
            Resource.objects.filter(gateway=request.gateway, name__in=data.get("resource_names") or []).values_list(
                "id", flat=True
            )
        )
        permission_model = PermissionDimensionManager.get_permission_model(data["grant_dimension"])

        username = settings.GATEWAY_DEFAULT_CREATOR

        permission_model.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=resource_ids,
            bk_app_code=data["target_app_code"],
            expire_days=data.get("expire_days"),
            grant_type=GrantTypeEnum.INITIALIZE.value,
            handled_by=username,
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关资源版本列表",
        query_serializer=ResourceVersionListInputSLZ(),
        responses={status.HTTP_201_CREATED: ResourceVersionListOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Sync"],
    ),
)
@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="创建网关资源版本",
        request_body=ResourceVersionCreateInputSLZ(),
        responses={status.HTTP_200_OK: ResourceVersionCreateOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class ResourceVersionListCreateApi(generics.ListCreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = ResourceVersionListInputSLZ

    def list(self, request, *args, **kwargs):
        slz = ResourceVersionListInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        versions = ResourceVersion.objects.filter_objects_fields(
            gateway_id=self.request.gateway.id,
            version=slz.validated_data.get("version"),
        )
        page = self.paginate_queryset(versions)
        slz = ResourceVersionListOutputSLZ(page, many=True)
        return OKJsonResponse(data=slz.data)

    @transaction.atomic
    def create(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)
        data = slz.validated_data
        resource_version = ResourceVersionArtifactHandler.create_resource_version_with_artifacts(
            gateway=request.gateway,
            data=data,
            username=request.user.username,
        )
        output_slz = ResourceVersionCreateOutputSLZ(resource_version)
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关最新资源版本",
        responses={status.HTTP_200_OK: serializers.GatewayResourceVersionLatestRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class ResourceVersionLatestRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    def get(self, request, *args, **kwargs):
        resource_version = ResourceVersion.objects.get_latest_version(request.gateway.id)

        if not resource_version:
            return OKJsonResponse(data={})

        output_slz = GatewayResourceVersionLatestRetrieveOutputSLZ({"version": resource_version.version})
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="发布网关资源版本",
        request_body=ReleaseInputSLZ(),
        responses={status.HTTP_201_CREATED: ReleaseOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class ResourceVersionReleaseApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = ReleaseInputSLZ

    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        stage_ids = data["stage_ids"]
        resource_version = ResourceVersion.objects.get_object_fields(data["resource_version_id"])

        ok, message = ReleaseHandler.release_to_stages(
            gateway=request.gateway,
            resource_version_id=data["resource_version_id"],
            stage_ids=stage_ids,
            username=request.user.username,
            comment=data["comment"],
        )
        if not ok:
            return FailJsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UNKNOWN", message=message)
        output_slz = ReleaseOutputSLZ(
            {
                "version": resource_version["version"],
                "stage_names": list(Stage.objects.filter(id__in=stage_ids).values_list("name", flat=True)),
            }
        )
        return OKJsonResponse(data=output_slz.data)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="生成网关sdk",
        request_body=SDKGenerateInputSLZ(),
        responses={status.HTTP_202_ACCEPTED: SDKGenerateOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class SDKGenerateApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = SDKGenerateInputSLZ

    def post(self, request, gateway_name: str, *args, **kwargs):
        """创建资源版本对应的 SDK"""

        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        resource_version = get_object_or_404(
            ResourceVersion, gateway=request.gateway, version=data["resource_version"]
        )
        create_or_resume_generation(
            resource_version,
            data["languages"],
            getattr(request.user, "username", None),
            enqueue_generation_items,
        )

        return OKJsonResponse(status=status.HTTP_202_ACCEPTED, data={"message": "SDK generation started"})


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="同步网关 MCP Server",
        request_body=StageMcpServersSyncInputSLZ(),
        responses={status.HTTP_200_OK: StageMcpServersSyncOutputSLZ()},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class GatewayMcpServerSyncViewSet(generics.CreateAPIView):
    serializer_class = StageMcpServersSyncInputSLZ
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    def post(self, request, *args, **kwargs):
        stage_name = kwargs.get("stage_name")
        if not stage_name:
            raise error_codes.INTERNAL.format(_("stage_name is required"), replace=True)
        stage = get_object_or_None(Stage, gateway=request.gateway, name=stage_name)
        if not stage:
            raise error_codes.NOT_FOUND.format(
                _("stage: {stage_name} not found").format(stage_name=stage_name), replace=True
            )

        resource_version_id = Release.objects.get_released_resource_version_id(
            gateway_id=request.gateway.id, stage_name=stage_name
        )

        # 检查当前环境是否正在发布
        stage_release_status = ReleaseHandler.batch_get_stage_release_status([stage.id])
        stage_status_info = stage_release_status.get(stage.id)
        is_releasing = stage_status_info and stage_status_info.get("status") in (
            ReleaseHistoryStatusEnum.DOING.value,
            ReleaseStatusEnum.PENDING.value,
        )

        if is_releasing:
            validate_resource_version_id = stage_status_info["resource_version_id"]
        elif resource_version_id:
            validate_resource_version_id = resource_version_id
        else:
            raise error_codes.NOT_FOUND.format(
                _("该环境：{stage_name} 未发布资源版本").format(stage_name=stage_name), replace=True
            )
        resource_name_to_schema = ResourceVersionHandler().get_resource_name_to_schema_by_resource_version(
            validate_resource_version_id
        )

        context = {
            "gateway": request.gateway,
            "stage": stage,
            "source": CallSourceTypeEnum.OpenAPI,
            "resource_name_to_schema": resource_name_to_schema,
        }

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        mcp_servers_data = serializer.validated_data["mcp_servers"]
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        audit_comment = _("同步 MCPServer")

        if is_releasing:
            sync_mcp_server_after_release.delay(
                gateway_id=request.gateway.id,
                gateway_name=request.gateway.name,
                stage_id=stage.id,
                stage_name=stage.name,
                release_history_id=stage_status_info["publish_id"],
                mcp_servers_data=mcp_servers_data,
                username=username,
                comment=audit_comment,
            )

            results = [
                {
                    "name": MCPServerHandler.get_mcp_server_name(
                        gateway_name=request.gateway.name, stage_name=stage.name, name=mcp_data["name"]
                    ),
                    "action": "pending",
                    "id": 0,
                }
                for mcp_data in mcp_servers_data
            ]
        else:
            results = MCPServerHandler.save_mcp_servers(
                gateway_id=request.gateway.id,
                gateway_name=request.gateway.name,
                stage_id=stage.id,
                stage_name=stage.name,
                mcp_servers_data=mcp_servers_data,
                username=username,
                comment=audit_comment,
            )

        output_slz = StageMcpServersSyncOutputSLZ(results, many=True)
        return OKJsonResponse(data=output_slz.data)
