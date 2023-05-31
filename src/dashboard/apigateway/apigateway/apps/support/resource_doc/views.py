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
from tempfile import TemporaryDirectory

from bkapi_client_generator import ExpandSwaggerError, GenerateMarkdownError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from apigateway.apps.support.constants import DocLanguageEnum, DocSourceEnum, DocTypeEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.resource_doc import serializers
from apigateway.apps.support.resource_doc.exceptions import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.apps.support.resource_doc.export_doc.generators import DocArchiveGenerator
from apigateway.apps.support.resource_doc.import_doc.managers import ArchiveImportDocManager, SwaggerImportDocManager
from apigateway.apps.support.resource_doc.utils import get_resource_doc_link, get_resource_doc_tmpl
from apigateway.apps.support.utils import ArchiveFileFactory
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import SchemaValidationError
from apigateway.core.models import Resource
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse


class DeprecatedResourceDocViewSet(viewsets.ModelViewSet):
    """[Deprecated] 待支持多语言文档后，删除此类"""

    serializer_class = serializers.ResourceDocSLZ
    lookup_field = "resource_id"

    def get_queryset(self):
        return ResourceDoc.objects.all()

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ResourceDocSLZ()},
        tags=["Support"],
    )
    def retrieve(self, request, *args, **kwargs):
        instance = ResourceDoc.objects.filter(api_id=request.gateway.id, resource_id=kwargs["resource_id"]).first()
        if not instance:
            return OKJsonResponse(
                "OK",
                data={
                    "id": None,
                    "type": DocTypeEnum.MARKDOWN.value,
                    "content": get_resource_doc_tmpl(self.request.gateway.name, language=DocLanguageEnum.ZH.value),
                    "resource_doc_link": "",
                    "language": DocLanguageEnum.ZH.value,
                },
            )

        instance.resource_doc_link = get_resource_doc_link(request.gateway, kwargs["resource_id"])
        slz = self.get_serializer(instance)
        return OKJsonResponse("OK", data=slz.data)

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceDocSLZ, tags=["Support"])
    def update(self, request, gateway_id: int, resource_id: int, *args, **kwargs):
        """创建或更新文档"""
        instance = ResourceDoc.objects.filter(api_id=request.gateway.id, resource_id=resource_id).first()

        slz = serializers.ResourceDocSLZ(
            instance,
            data=request.data,
            context={
                "api_id": request.gateway.id,
                "resource_id": resource_id,
            },
        )
        slz.is_valid(raise_exception=True)

        # 临时过渡阶段，更新时 created_by 也改为当前用户，多语言上线，此代码将删除
        slz.save(
            api=request.gateway,
            resource_id=resource_id,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse("OK")


class ResourceDocViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ResourceDocSLZ
    lookup_field = "id"

    def get_queryset(self):
        return ResourceDoc.objects.all()

    def _check_resource_permission(self, resource_id: int, gateway_id: int):
        try:
            # 确保资源属于当前网关
            Resource.objects.get(id=resource_id, api_id=gateway_id)
        except Resource.DoesNotExist:
            raise Http404

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceDocSLZ, tags=["Support"])
    def create(self, request, gateway_id: int, resource_id: int, *args, **kwargs):
        """创建资源文档"""
        self._check_resource_permission(resource_id, request.gateway.id)

        slz = serializers.ResourceDocSLZ(
            data=request.data,
            context={
                "api_id": request.gateway.id,
                "resource_id": resource_id,
            },
        )
        slz.is_valid(raise_exception=True)

        slz.save(
            api=request.gateway,
            resource_id=resource_id,
            source=DocSourceEnum.CUSTOM.value,
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        return OKJsonResponse("OK", data={"id": slz.instance.id})

    @swagger_auto_schema(responses={status.HTTP_200_OK: ""}, request_body=serializers.ResourceDocSLZ, tags=["Support"])
    def update(self, request, gateway_id: int, resource_id: int, id: int, *args, **kwargs):
        """更新资源文档"""
        self._check_resource_permission(resource_id, request.gateway.id)

        try:
            instance = ResourceDoc.objects.get(
                api_id=request.gateway.id,
                resource_id=resource_id,
                id=id,
            )
        except ResourceDoc.DoesNotExist:
            raise Http404

        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            source=DocSourceEnum.CUSTOM.value,
            updated_by=request.user.username,
        )

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: ""},
        tags=["Support"],
    )
    def destroy(self, request, gateway_id: int, resource_id: int, id: int, *args, **kwargs):
        try:
            instance = ResourceDoc.objects.get(api_id=request.gateway.id, resource_id=resource_id, id=id)
        except ResourceDoc.DoesNotExist:
            raise Http404

        instance.delete()

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: serializers.ResourceDocSLZ(many=True)},
        tags=["Support"],
    )
    def list(self, request, gateway_id: int, resource_id: int, *args, **kwargs):
        """获取资源的文档列表，支持多语言文档"""
        self._check_resource_permission(resource_id, request.gateway.id)

        docs = ResourceDoc.objects.filter(api_id=request.gateway.id, resource_id=resource_id)
        language_to_doc = {doc.language: doc for doc in docs}

        for language in DocLanguageEnum.get_values():
            if language in language_to_doc:
                continue
            language_to_doc[language] = ResourceDoc(
                type=DocTypeEnum.MARKDOWN.value,
                language=language,
                content=get_resource_doc_tmpl(self.request.gateway.name, language),
            )

        slz = self.get_serializer(language_to_doc.values(), many=True)
        return OKJsonResponse("OK", data=slz.data)


class ArchiveDocParseViewSet(viewsets.ViewSet):
    """资源文档文件名解析"""

    @swagger_auto_schema(
        request_body=serializers.ArchiveDocParseSLZ,
        responses={status.HTTP_200_OK: serializers.ArchiveDocParseResultSLZ(many=True)},
        tags=["Support"],
    )
    def parse(self, request, gateway_id: int, *args, **kwargs):
        slz = serializers.ArchiveDocParseSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        manager = ArchiveImportDocManager()
        try:
            docs = manager.parse_doc_file(gateway_id, slz.validated_data["file"])
        except NoResourceDocError:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(
                _("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"),
                replace=True,
            )

        slz = serializers.ArchiveDocParseResultSLZ(
            docs,
            many=True,
            context={
                "resource_id_to_object": Resource.objects.filter_id_object_map(request.gateway.id),
            },
        )
        return OKJsonResponse("OK", data=slz.data)


class ResourceDocImportExportViewSet(viewsets.ViewSet):
    """资源文档导入、导出"""

    @swagger_auto_schema(
        request_body=serializers.ImportResourceDocsByArchiveSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Support"],
    )
    @transaction.atomic
    def import_by_archive(self, request, gateway_id: int, *args, **kwargs):
        """根据 tgz/zip 归档文件，导入资源文档"""
        slz = serializers.ImportResourceDocsByArchiveSLZ(
            data=request.data,
            context={
                "resource_name_to_id": Resource.objects.filter_resource_name_to_id(gateway_id),
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = ArchiveImportDocManager()
        try:
            manager.import_docs(
                gateway_id=request.gateway.id,
                selected_resource_docs=data["selected_resource_docs"],
                archive_file=data["file"],
            )
        except NoResourceDocError:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(
                _("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"), replace=True
            )
        except ResourceDocJinja2TemplateError as err:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(_("导入资源文档失败，{err}。").format(err=err), replace=True)
        return OKJsonResponse("OK")

    @swagger_auto_schema(
        request_body=serializers.ImportResourceDocsBySwaggerSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Support"],
    )
    @transaction.atomic
    def import_by_swagger(self, request, gateway_id: int, *args, **kwargs):
        """根据 swagger 描述文件，导入资源文档"""
        slz = serializers.ImportResourceDocsBySwaggerSLZ(
            data=request.data,
            context={
                "resource_name_to_id": Resource.objects.filter_resource_name_to_id(gateway_id),
            },
        )
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        manager = SwaggerImportDocManager()
        try:
            manager.import_docs(
                gateway_id=request.gateway.id,
                selected_language=DocLanguageEnum(data["language"]),
                selected_resource_docs=data["selected_resource_docs"],
                swagger=data["swagger"],
            )
        except (ExpandSwaggerError, SchemaValidationError):
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(_("swagger 描述内容不符合规范。"))
        except GenerateMarkdownError:
            raise error_codes.RESOURCE_DOC_IMPORT_ERROR.format(_("根据 swagger 描述生成 markdown 格式文档出现错误。"))

        return OKJsonResponse("OK")

    @swagger_auto_schema(
        request_body=serializers.ResourceDocExportConditionSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["Support"],
    )
    def export(self, request, gateway_id: int, *args, **kwargs):
        """导出资源文档"""
        slz = serializers.ResourceDocExportConditionSLZ(
            data=request.data,
            context={
                "api": request.gateway,
            },
        )
        slz.is_valid(raise_exception=True)

        file_type = slz.validated_data["file_type"]
        queryset = slz.get_exported_resource()
        resource_ids = list(queryset.values_list("id", flat=True))

        with TemporaryDirectory() as output_dir:
            # 导出文件名规范：bk_产品名_功能名_文件名.后缀
            archive_name = f"bk_apigw_docs_{request.gateway.name}.{file_type}"

            archivefile = ArchiveFileFactory.from_file_type(file_type)

            try:
                files = DocArchiveGenerator().generate(output_dir, gateway_id, resource_ids)
                archive_path = archivefile.archive(output_dir, archive_name, files)
            except NoResourceDocError:
                raise error_codes.RESOURCE_DOC_EXPORT_ERROR.format(_("选中的资源未创建文档。"))

            return DownloadableResponse(open(archive_path, "rb"), filename=archive_name)
