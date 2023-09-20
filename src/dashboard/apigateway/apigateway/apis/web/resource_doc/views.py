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
from tempfile import TemporaryDirectory
from typing import Any, Dict, List

from bkapi_client_generator import ExpandSwaggerError, GenerateMarkdownError
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource_doc.archive_factory import ArchiveFileFactory
from apigateway.biz.resource_doc.exceptions import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.biz.resource_doc.exporter.generators import DocArchiveGenerator
from apigateway.biz.resource_doc.importer import DocImporter
from apigateway.biz.resource_doc.importer.parsers import ArchiveParser, SwaggerParser
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import SchemaValidationError
from apigateway.core.models import Resource
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse

from .serializers import (
    DocArchiveParseInputSLZ,
    DocArchiveParseOutputSLZ,
    DocExportInputSLZ,
    DocImportByArchiveInputSLZ,
    DocImportBySwaggerInputSLZ,
)


class DocArchiveParseApi(generics.CreateAPIView):
    @swagger_auto_schema(
        request_body=DocArchiveParseInputSLZ,
        responses={status.HTTP_200_OK: DocArchiveParseOutputSLZ},
        tags=["WebAPI.ResourceDoc"],
    )
    def post(self, request, *args, **kwargs):
        slz = DocArchiveParseInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        parser = ArchiveParser(gateway_id=request.gateway.id)
        try:
            docs = parser.parse(slz.validated_data["file"])
        except NoResourceDocError:
            raise error_codes.INVALID_ARGUMENT.format(_("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"), replace=True)

        slz = DocArchiveParseOutputSLZ(docs, many=True)
        return OKJsonResponse(data=slz.data)


class DocImportByArchiveApi(generics.CreateAPIView):
    @swagger_auto_schema(
        request_body=DocImportByArchiveInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.ResourceDoc"],
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
            raise error_codes.INVALID_ARGUMENT.format(_("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"), replace=True)
        except ResourceDocJinja2TemplateError as err:
            raise error_codes.INTERNAL.format(_("导入资源文档失败，{err}。").format(err=err), replace=True)

        importer = DocImporter(
            gateway_id=request.gateway.id,
            selected_resource_docs=slz.validated_data["selected_resource_docs"],
        )
        importer.import_docs(docs=docs)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


class DocImportBySwaggerApi(generics.CreateAPIView):
    @swagger_auto_schema(
        request_body=DocImportBySwaggerInputSLZ,
        responses={status.HTTP_204_NO_CONTENT: ""},
        tags=["WebAPI.ResourceDoc"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """根据 swagger 描述文件，导入资源文档"""
        slz = DocImportBySwaggerInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        parser = SwaggerParser(gateway_id=request.gateway.id)
        try:
            docs = parser.parse(
                swagger=slz.validated_data["swagger"],
                language=DocLanguageEnum(slz.validated_data["language"]),
            )
        except (ExpandSwaggerError, SchemaValidationError):
            raise error_codes.INVALID_ARGUMENT.format(_("swagger 描述内容不符合规范。"))
        except GenerateMarkdownError:
            raise error_codes.INTERNAL.format(_("根据 swagger 描述生成 markdown 格式文档出现错误。"))

        importer = DocImporter(
            gateway_id=request.gateway.id,
            selected_resource_docs=slz.validated_data["selected_resource_docs"],
        )
        importer.import_docs(docs=docs)

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)


class DocExportApi(generics.CreateAPIView):
    @swagger_auto_schema(
        request_body=DocExportInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["WebAPI.ResourceDoc"],
    )
    def post(self, request, *args, **kwargs):
        """导出资源文档"""
        slz = DocExportInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        selected_resource_queryset = self._filter_selected_resources(
            export_type=slz.validated_data["export_type"],
            gateway_id=request.gateway.id,
            resource_filter_condition=slz.validated_data.get("resource_filter_condition", {}),
            resource_ids=slz.validated_data.get("resource_ids", []),
        )
        selected_resource_ids = list(selected_resource_queryset.values_list("id", flat=True))
        file_type = slz.validated_data["file_type"]

        with TemporaryDirectory() as output_dir:
            # 导出文件名规范：bk_产品名_功能名_文件名.后缀
            archive_name = f"bk_apigw_docs_{request.gateway.name}.{file_type}"

            archivefile = ArchiveFileFactory.from_file_type(file_type)

            try:
                files = DocArchiveGenerator().generate(output_dir, request.gateway.id, selected_resource_ids)
                archive_path = archivefile.archive(output_dir, archive_name, files)
            except NoResourceDocError:
                raise error_codes.INVALID_ARGUMENT.format(_("选中的资源未创建文档。"))

            return DownloadableResponse(open(archive_path, "rb"), filename=archive_name)

    def _filter_selected_resources(
        self,
        export_type: str,
        gateway_id: int,
        resource_filter_condition: Dict[str, Any],
        resource_ids: List[int],
    ):
        """获取待导出资源文档的资源"""

        if export_type == ExportTypeEnum.ALL.value:
            return Resource.objects.filter(gateway_id=gateway_id)

        if export_type == ExportTypeEnum.FILTERED.value:
            return ResourceHandler.filter_by_resource_filter_condition(gateway_id, resource_filter_condition or {})

        if export_type == ExportTypeEnum.SELECTED.value:
            return Resource.objects.filter(gateway_id=gateway_id, id__in=resource_ids)

        return Resource.objects.none()
