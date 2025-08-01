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
import json
import logging

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from pydantic import TypeAdapter
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError

from apigateway.apis.v2.permissions import OpenAPIV2GatewayRelatedAppPermission
from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.apps.openapi.models import OpenAPIFileResourceSchemaVersion
from apigateway.apps.permission.constants import FormattedGrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppResourcePermission,
)
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc, ResourceDocVersion
from apigateway.biz.audit import Auditor
from apigateway.biz.gateway import GatewayData, GatewayRelatedAppHandler, GatewaySaver, ReleaseError, release
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.resource.importer import ResourcesImporter
from apigateway.biz.resource.importer.openapi import OpenAPIExportManager, OpenAPIImportManager
from apigateway.biz.resource_doc.exceptions import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.biz.resource_doc.importer import DocImporter
from apigateway.biz.resource_doc.importer.parsers import ArchiveParser, OpenAPIParser
from apigateway.biz.resource_version import ResourceDocVersionHandler, ResourceVersionHandler
from apigateway.biz.sdk import exceptions
from apigateway.biz.sdk.helper import SDKHelper
from apigateway.common.constants import CallSourceTypeEnum
from apigateway.common.error_codes import error_codes
from apigateway.components.bkauth import get_app_tenant_info
from apigateway.core.models import Gateway, Release, Resource, ResourceVersion, Stage
from apigateway.utils.django import get_model_dict, get_object_or_None
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

from . import serializers
from .serializers import (
    DocImportByArchiveInputSLZ,
    GatewayResourceVersionLatestRetrieveOutputSLZ,
    GatewaySyncOutputSLZ,
    MCPServerSLZ,
    ReleaseInputSLZ,
    ReleaseOutputSLZ,
    ResourceImportInputSLZ,
    ResourceSyncOutputSLZ,
    ResourceVersionCreateInputSLZ,
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

        # save gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        saver = GatewaySaver(
            id=gateway and gateway.id,
            data=TypeAdapter(GatewayData).validate_python(slz.validated_data),
            bk_app_code=request.app.app_code,
            username=username,
        )
        gateway = saver.save()

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
        output_slz = StageSyncOutputSLZ(instance=instance)
        return OKJsonResponse(output_slz.data)


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

        try:
            openapi_manager = OpenAPIImportManager.load_from_content(
                request.gateway,
                slz.validated_data["content"],
                need_delete_unspecified_resources=slz.validated_data["delete"],
            )
        except Exception as err:  # pylint: disable=broad-except
            raise ValidationError({"content": _("导入内容为无效的 json/yaml 数据，{err}。").format(err=err)})

        validate_err_list = openapi_manager.validate()
        if len(validate_err_list) != 0:
            error_dicts = [error.to_dict() for error in validate_err_list]
            raise ValidationError(
                {
                    "content": _("validate err {err}。").format(
                        err=json.dumps(error_dicts, ensure_ascii=False, indent=4)
                    )
                }
            )

        importer = ResourcesImporter.from_resources(
            gateway=request.gateway,
            resources=openapi_manager.get_resource_list(),
            username=request.user.username,
            selected_resources=None,
            need_delete_unspecified_resources=slz.validated_data["delete"],
        )
        importer.import_resources()

        # 如果生成文档还要再生成文档
        if slz.validated_data.get("doc_language"):
            parser = OpenAPIParser(gateway_id=request.gateway.id)
            docs = parser.parse(
                swagger=slz.validated_data["content"],
                language=DocLanguageEnum(slz.validated_data["doc_language"]),
            )
            doc_importer = DocImporter(
                gateway_id=request.gateway.id,
            )
            doc_importer.import_docs(docs=docs)

        # 分析出已创建或更新的资源
        added = []
        updated = []
        for resource_data in importer.get_selected_resource_data_list():
            if resource_data.metadata.get("is_created"):
                added.append({"id": resource_data.resource.id})
            else:
                updated.append({"id": resource_data.resource.id})

        slz = ResourceSyncOutputSLZ(
            {
                "added": added,
                "updated": updated,
                "deleted": importer.get_deleted_resources(),
            }
        )
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

        exist_related_app_codes = GatewayRelatedAppHandler.get_related_app_codes(request.gateway.id)
        missing_app_codes = set(input_app_codes) - set(exist_related_app_codes)
        for bk_app_code in missing_app_codes:
            GatewayRelatedAppHandler.add_related_app(request.gateway.id, bk_app_code)

        data_after = GatewayRelatedAppHandler.get_related_app_codes(request.gateway.id)

        # record audit log
        gateway = request.gateway
        username = request.user.username or settings.GATEWAY_DEFAULT_CREATOR
        Auditor.record_gateway_op_success(
            op_type=OpTypeEnum.MODIFY,
            username=username,
            gateway_id=gateway.id,
            instance_id=gateway.id,
            instance_name=gateway.name,
            data_before={"related_app_codes": exist_related_app_codes},
            data_after={"related_app_codes": data_after},
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
        permission_model.objects.save_permissions(
            gateway=request.gateway,
            resource_ids=resource_ids,
            bk_app_code=data["target_app_code"],
            expire_days=data.get("expire_days"),
            grant_type=GrantTypeEnum.INITIALIZE.value,
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
        responses={status.HTTP_201_CREATED: ""},
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
        return OKJsonResponse(data=self.paginator.get_paginated_data(slz.data))

    @transaction.atomic
    def create(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)
        data = slz.validated_data
        instance = ResourceVersionHandler.create_resource_version(request.gateway, data, request.user.username)

        # 创建文档版本
        if ResourceDoc.objects.filter(gateway=request.gateway).exists():
            ResourceDocVersion.objects.create(
                gateway=request.gateway,
                resource_version=instance,
                data=ResourceDocVersionHandler().make_version(request.gateway.id),
            )
        exporter = OpenAPIExportManager(
            api_version=instance.version,
            title="the openapi of %s" % request.gateway.name,
        )
        # 创建openapi file版本
        OpenAPIFileResourceSchemaVersion.objects.create(
            gateway=request.gateway,
            resource_version=instance,
            schema=exporter.export_resource_version_openapi(instance),
        )
        return OKJsonResponse(status=status.HTTP_201_CREATED)


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        operation_description="获取网关最新资源版本",
        responses={status.HTTP_200_OK: serializers.GatewayResourceVersionLatestRetrieveOutputSLZ()},
        tags=["OpenAPI.V2.Open"],
    ),
)
class ResourceVersionLatestRetrieveApi(generics.RetrieveAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]

    @swagger_auto_schema(tags=["OpenAPI.V1"])
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

    @swagger_auto_schema(tags=["OpenAPI.V1"])
    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        slz = self.get_serializer(data=request.data, context={"request": request})
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        gateway_id = data["gateway"].id
        stage_ids = data["stage_ids"]
        resource_version = ResourceVersion.objects.get_object_fields(data["resource_version_id"])

        for stage_id in data["stage_ids"]:
            try:
                with Lock(
                    f"{gateway_id}_{stage_id}",
                    timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
                    try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
                ):
                    # do release, will record audit log
                    release(
                        gateway=request.gateway,
                        stage_id=stage_id,
                        resource_version_id=data["resource_version_id"],
                        comment=data["comment"],
                        username=request.user.username,
                    )
            except LockTimeout as err:
                return FailJsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UNKNOWN", message=str(err))
            except ReleaseError as err:
                return FailJsonResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR, code="UNKNOWN", message=str(err))
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
        request_body=ReleaseInputSLZ(),
        responses={status.HTTP_201_CREATED: SDKGenerateOutputSLZ(many=True)},
        tags=["OpenAPI.V2.Sync"],
    ),
)
class SDKGenerateApi(generics.CreateAPIView):
    permission_classes = [OpenAPIV2GatewayRelatedAppPermission]
    serializer_class = SDKGenerateInputSLZ

    @transaction.atomic
    def post(self, request, gateway_name: str, *args, **kwargs):
        """创建资源版本对应的 SDK"""

        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        resource_version = get_object_or_404(
            ResourceVersion, gateway=request.gateway, version=slz.data["resource_version"]
        )
        results = []
        with SDKHelper(resource_version=resource_version) as helper:
            for language in slz.data["languages"]:
                try:
                    info = helper.create(
                        language=language,
                        version=slz.data["version"] or resource_version.version,
                        operator=None,
                    )
                    results.append(
                        {
                            "name": info.sdk.name,
                            "version": info.sdk.version_number,
                            "url": info.sdk.url,
                        }
                    )
                except exceptions.ResourcesIsEmpty:
                    raise error_codes.INTERNAL.format(_("网关下无资源，无法生成 SDK。"), replace=True)
                except exceptions.GenerateError:
                    raise error_codes.INTERNAL.format(_("网关 SDK 生成失败，请联系管理员。"), replace=True)
                except exceptions.PackError:
                    raise error_codes.INTERNAL.format(_("网关 SDK 打包失败，请联系管理员。"), replace=True)
                except exceptions.DistributeError:
                    raise error_codes.INTERNAL.format(_("网关 SDK 发布失败，请联系管理员。"), replace=True)
                except exceptions.TooManySDKVersion as err:
                    raise error_codes.INTERNAL.format(
                        _("同一资源版本，最多只能生成 {count} 个 SDK。").format(count=err.max_count), replace=True
                    )
                except Exception:  # pylint: disable=broad-except
                    logger.exception(
                        "create sdk failed for gateway %s, release %s", gateway_name, resource_version.version
                    )
                    raise error_codes.INTERNAL.format(_("网关 SDK 创建失败，请联系管理员。"), replace=True)

        return OKJsonResponse(status=status.HTTP_201_CREATED, data={"results": results})


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
        # 验证输入数据
        stage_name = kwargs.get("stage_name")
        if not stage_name:
            raise error_codes.INTERNAL.format(_("stage_name is required"), replace=True)
        stage = Stage.objects.get(name=stage_name)
        if not stage:
            raise error_codes.NOT_FOUND.format(
                _("stage: {stage_name} not found").format(stage_name=stage_name), replace=True
            )
        # 查询stage发布的资源版本
        resource_version_id = Release.objects.get_released_resource_version_id(
            gateway_id=request.gateway.id, stage_name=stage_name
        )
        if not resource_version_id:
            raise error_codes.NOT_FOUND.format(
                _("该环境：{stage_name} 未发布资源版本").format(stage_name=stage_name), replace=True
            )

        # 查询资源 schema 数据
        resource_name_to_schema = ResourceVersionHandler().get_resource_name_to_schema_by_resource_version(
            resource_version_id
        )

        context = {
            "gateway": request.gateway,
            "stage": stage,
            "source": CallSourceTypeEnum.OpenAPI,
            "resource_name_to_schema": resource_name_to_schema,
        }

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        results = []
        for mcp_data in serializer.validated_data["mcp_servers"]:
            mcp_data["stage_id"] = stage.id
            name = mcp_data["name"]
            mcp_data["name"] = f"{request.gateway.name}-{stage.name}-{name}"
            # 查询是否存
            instance = MCPServer.objects.filter(
                name=mcp_data["name"], stage__name=stage.name, gateway_id=request.gateway.id
            ).first()
            action = "updated" if instance else "created"
            mcp_slz = MCPServerSLZ(instance=instance, data=mcp_data, context=context)
            mcp_slz.is_valid(raise_exception=True)
            instance = mcp_slz.save()
            results.append({"name": instance.name, "action": action, "id": instance.id})

        output_slz = StageMcpServersSyncOutputSLZ(results, many=True)
        return OKJsonResponse(data=output_slz.data)
