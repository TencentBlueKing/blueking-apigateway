# -*- coding: utf-8 -*-
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
import logging
import operator

from bkapi_client_generator import ExpandSwaggerError, GenerateMarkdownError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.apis.open.support import serializers
from apigateway.apps.support.api_sdk import exceptions
from apigateway.apps.support.api_sdk.helper import SDKHelper
from apigateway.apps.support.api_sdk.models import SDKFactory
from apigateway.apps.support.constants import DocLanguageEnum, ProgrammingLanguageEnum
from apigateway.apps.support.models import APISDK, ReleasedResourceDoc, ResourceDoc
from apigateway.apps.support.resource_doc.exceptions import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.apps.support.resource_doc.import_doc.managers import ArchiveImportDocManager, SwaggerImportDocManager
from apigateway.apps.support.resource_doc.serializers import ResourceDocSLZ
from apigateway.apps.support.utils import get_doc_language
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.common.contexts import APIAuthContext
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import SchemaValidationError
from apigateway.common.funcs import get_resource_version_display
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion
from apigateway.core.utils import get_path_display, get_resource_url
from apigateway.utils.responses import OKJsonResponse

logger = logging.getLogger(__name__)


class ResourceDocViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceDocSLZ
    lookup_field = "resource_id"
    api_permission_exempt = True

    def get_queryset(self):
        return ResourceDoc.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ResourceDocSLZ()},
        tags=["OpenAPI.Support"],
    )
    def retrieve(self, request, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            return OKJsonResponse("OK", data={})

        api_id = request.gateway.id
        resource_id = kwargs["resource_id"]

        resource = ReleasedResource.objects.get_latest_released_resource(api_id, resource_id)
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"]:
            return OKJsonResponse("OK", data={})

        doc = ReleasedResourceDoc.objects.get_latest_released_resource_doc(api_id, resource_id)
        stages = Release.objects.get_released_stage_names(api_id)
        latest_sdk = APISDK.objects.filter_recommended_sdks(
            language=ProgrammingLanguageEnum.PYTHON.value,
            gateway_id=api_id,
        ).first()

        return OKJsonResponse(
            "OK",
            data={
                "resource": resource,
                "stages": stages,
                "doc": doc,
                "sdk": self._get_python_sdk_info(latest_sdk),
            },
        )

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ResourceDocSLZ()},
        tags=["OpenAPI.Support"],
    )
    def get_doc(self, request, stage_name: str, resource_name: str, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            raise Http404

        resource_version_id = Release.objects.get_released_resource_version_id(request.gateway.id, stage_name)
        if not resource_version_id:
            raise Http404

        resource = ReleasedResource.objects.get_released_resource(
            request.gateway.id, resource_version_id, resource_name
        )
        # 资源在已发布版本中不存在，或者资源未公开
        if not resource or not resource["is_public"] or stage_name in resource["disabled_stages"]:
            raise Http404

        doc = ReleasedResourceDoc.objects.get_released_resource_doc(
            request.gateway.id,
            resource_version_id,
            resource["id"],
            language=get_doc_language(get_current_language_code()),
        )

        return OKJsonResponse(
            "OK",
            data={
                "resource": resource,
                "doc": doc,
                "resource_url": get_resource_url(
                    resource_url_tmpl=ResourceURLHandler.get_resource_url_tmpl(request.gateway.name, stage_name),
                    gateway_name=request.gateway.name,
                    stage_name=stage_name,
                    resource_path=get_path_display(resource["path"], resource["match_subpath"]),
                ),
            },
        )

    def _get_python_sdk_info(self, sdk):
        if not sdk:
            return {}

        is_uploaded_to_pypi = sdk.config.get(ProgrammingLanguageEnum.PYTHON.value, {}).get(
            "is_uploaded_to_pypi", False
        )
        if not is_uploaded_to_pypi:
            return {}

        return {
            "version_number": sdk.version_number,
            "filename": sdk.filename,
            "download_url": sdk.download_url,
        }


class APISDKV1ViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.APISDKV1SLZ
    lookup_field = "id"
    api_permission_exempt = True

    def get_queryset(self):
        return APISDK.objects.all()

    def list_latest_sdks(self, request, *args, **kwargs):
        slz = serializers.APISDKQueryV1SLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        queryset = APISDK.objects.filter_recommended_sdks(
            data["language"],
            gateway_id=data.get("api_id"),
        )

        resource_version_ids = list(set(queryset.values_list("resource_version_id", flat=True)))

        slz = serializers.APISDKV1SLZ(
            [SDKFactory.create(i) for i in queryset],
            many=True,
            context={
                "api_id_map": Gateway.objects.filter_id_object_map(),
                "api_id_config_map": APIAuthContext().filter_scope_id_config_map(),
                "released_stages": Release.objects.get_released_stages(resource_version_ids=resource_version_ids),
                "resource_versions": ResourceVersion.objects.get_id_to_fields_map(
                    resource_version_ids=resource_version_ids,
                ),
            },
        )
        return OKJsonResponse("OK", data=slz.data)

    def list_stage_sdks(self, request, *args, **kwargs):
        if not request.gateway.is_active_and_public:
            return OKJsonResponse("OK", data=[])

        released_resource_version_ids = Release.objects.get_released_resource_version_ids(request.gateway.id)
        public_latest_sdks = {
            k: SDKFactory.create(v)
            for k, v in APISDK.objects.filter_resource_version_public_latest_sdk(
                gateway_id=request.gateway.id,
                resource_version_ids=released_resource_version_ids,
            ).items()
        }

        releases = Release.objects.filter(api_id=request.gateway.id).values(
            "stage__id",
            "stage__name",
            "stage__is_public",
            "resource_version__id",
            "resource_version__name",
            "resource_version__title",
            "resource_version__version",
        )
        stage_sdks = []
        for release in releases:
            if not release["stage__is_public"]:
                continue

            sdk = public_latest_sdks.get(release["resource_version__id"])
            stage_sdks.append(
                {
                    "stage_id": release["stage__id"],
                    "stage_name": release["stage__name"],
                    "resource_version_id": release["resource_version__id"],
                    "resource_version_name": release["resource_version__name"],
                    "resource_version_title": release["resource_version__title"],
                    "resource_version_display": get_resource_version_display(
                        {
                            "version": release["resource_version__version"],
                            "name": release["resource_version__name"],
                            "title": release["resource_version__title"],
                        }
                    ),
                    "language": sdk.language.value if sdk else "",
                    "sdk_version_number": sdk.version if sdk else "",
                    "sdk_download_url": sdk.url if sdk else "",
                    "sdk_name": sdk.name if sdk else "",
                    "sdk_install_command": sdk.install_command if sdk else "",
                }
            )

        return OKJsonResponse("OK", data=sorted(stage_sdks, key=operator.itemgetter("stage_name")))


class ResourceDocImportViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @transaction.atomic
    @swagger_auto_schema(
        tags=["OpenAPI.Support"],
    )
    def import_by_archive(self, request, gateway_name: str, *args, **kwargs):
        """根据 tgz/zip 归档文件，导入资源文档"""
        slz = serializers.ImportResourceDocsByArchiveV1SLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ArchiveImportDocManager()
        try:
            manager.import_docs(
                gateway_id=request.gateway.id,
                selected_resource_docs=None,
                archive_file=data["file"],
            )
        except NoResourceDocError:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(
                _("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"), replace=True
            )
        except ResourceDocJinja2TemplateError as err:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(_("导入资源文档失败，{err}。").format(err=err), replace=True)
        return OKJsonResponse("OK")

    @transaction.atomic
    @swagger_auto_schema(
        tags=["OpenAPI.Support"],
    )
    def import_by_swagger(self, request, gateway_name: str, *args, **kwargs):
        """根据 swagger 描述文件，导入资源文档"""
        slz = serializers.ImportResourceDocsBySwaggerV1SLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = SwaggerImportDocManager()
        try:
            manager.import_docs(
                gateway_id=request.gateway.id,
                selected_language=DocLanguageEnum(data["language"]),
                selected_resource_docs=None,
                swagger=data["swagger"],
            )
        except (ExpandSwaggerError, SchemaValidationError):
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(_("swagger 描述内容不符合规范。"))
        except GenerateMarkdownError:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(_("根据 swagger 描述生成 markdown 格式文档出现错误。"))

        return OKJsonResponse("OK")


class SDKGenerateViewSet(viewsets.ViewSet):
    permission_classes = [GatewayRelatedAppPermission]

    @transaction.atomic
    @swagger_auto_schema(
        tags=["OpenAPI.Support"],
    )
    def generate(self, request, gateway_name: str, *args, **kwargs):
        """创建资源版本对应的 SDK"""

        slz = serializers.SDKGenerateV1SLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        resource_version = get_object_or_404(
            ResourceVersion, api=request.gateway, version=slz.data["resource_version"]
        )
        results = []
        with SDKHelper(resource_version=resource_version) as helper:
            for language in slz.data["languages"]:
                try:
                    info = helper.create(
                        language=language,
                        include_private_resources=slz.data["include_private_resources"],
                        version=slz.data["version"] or resource_version.version,
                        is_public=True,
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
                    raise error_codes.SDK_ERROR.format(_("网关下无资源，无法生成 SDK。"), replace=True)
                except exceptions.GenerateError:
                    raise error_codes.SDK_ERROR.format(_("网关 SDK 生成失败，请联系管理员。"), replace=True)
                except exceptions.PackError:
                    raise error_codes.SDK_ERROR.format(_("网关 SDK 打包失败，请联系管理员。"), replace=True)
                except exceptions.DistributeError:
                    raise error_codes.SDK_ERROR.format(_("网关 SDK 发布失败，请联系管理员。"), replace=True)
                except exceptions.TooManySDKVersion as err:
                    raise error_codes.SDK_ERROR.format(
                        _("同一资源版本，最多只能生成 {count} 个 SDK。").format(count=err.max_count), replace=True
                    )
                except Exception:
                    logger.exception(
                        "create sdk failed for gateway %s, release %s", gateway_name, resource_version.version
                    )
                    raise error_codes.SDK_ERROR.format(_("网关 SDK 创建失败, 请联系管理员。"), replace=True)

        return OKJsonResponse("OK", data=results)
