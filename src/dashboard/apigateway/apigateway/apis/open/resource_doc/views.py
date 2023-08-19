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
from bkapi_client_generator import ExpandSwaggerError, GenerateMarkdownError
from django.db import transaction
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc.exceptions import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.biz.resource_doc.import_doc.importers import ResourceDocImporter
from apigateway.biz.resource_doc.import_doc.parsers import ArchiveParser, SwaggerParser
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import SchemaValidationError
from apigateway.common.permissions import GatewayRelatedAppPermission
from apigateway.utils.responses import V1OKJsonResponse

from .serializers import (
    ResourceDocImportByArchiveInputV1SLZ,
    ResourceDocImportBySwaggerInputV1SLZ,
)


class ResourceDocImportByArchiveApi(generics.CreateAPIView):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(
        request_body=ResourceDocImportByArchiveInputV1SLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.ResourceDoc"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """根据 tgz/zip 归档文件，导入资源文档"""
        slz = ResourceDocImportByArchiveInputV1SLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        parser = ArchiveParser(gateway_id=request.gateway.id)
        try:
            docs = parser.parse(slz.validated_data["file"])
        except NoResourceDocError:
            raise error_codes.INVALID_ARGUMENT.format(_("不存在符合条件的资源文档，请参考使用指南，检查归档文件中资源文档是否正确。"), replace=True)
        except ResourceDocJinja2TemplateError as err:
            raise error_codes.INTERNAL.format(_("导入资源文档失败，{err}。").format(err=err), replace=True)

        importer = ResourceDocImporter(gateway_id=request.gateway.id, selected_resource_docs=None)
        importer.import_docs(docs=docs)

        return V1OKJsonResponse()


class ResourceDocImportBySwaggerApi(generics.CreateAPIView):
    permission_classes = [GatewayRelatedAppPermission]

    @swagger_auto_schema(
        request_body=ResourceDocImportBySwaggerInputV1SLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.ResourceDoc"],
    )
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """根据 swagger 描述文件，导入资源文档"""
        slz = ResourceDocImportBySwaggerInputV1SLZ(data=request.data)
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

        importer = ResourceDocImporter(gateway_id=request.gateway.id, selected_resource_docs=None)
        importer.import_docs(docs=docs)

        return V1OKJsonResponse()
