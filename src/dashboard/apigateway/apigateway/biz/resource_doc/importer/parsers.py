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
import hashlib
from tempfile import TemporaryDirectory
from typing import IO, AnyStr, Dict, List, Optional, Union

from django.utils.translation import gettext as _
from openapi_spec_validator.versions import OPENAPIV2

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.constants import OpenAPIFormatEnum
from apigateway.biz.resource.importer.openapi import OpenAPIExportManager, OpenAPIImportManager
from apigateway.biz.resource.importer.schema import convert_operation_v3_to_v2
from apigateway.biz.resource_doc.archive_factory import ArchiveFileFactory
from apigateway.biz.resource_doc.exceptions import NoResourceDocError
from apigateway.common.exceptions import SchemaValidationError
from apigateway.core.models import Gateway, Resource

from .generators import Jinja2ToMarkdownGenerator, OpenAPIToMarkdownGenerator
from .models import ArchiveDoc, OpenAPIDoc


class BaseParser:
    def __init__(self, gateway_id: int):
        self.gateway_id = gateway_id

    def _enrich_docs(self, docs: Union[List[ArchiveDoc], List[OpenAPIDoc]]):
        """
        丰富文档数据
        - 补全解析文档对应的资源、资源文档对象
        - 判断文档内容是否变更
        """
        resources = {resource.name: resource for resource in Resource.objects.filter(gateway_id=self.gateway_id)}
        # en/zh share the same resource_id, use add language to distinguish
        resource_docs = {
            f"{resource_doc.language}:{resource_doc.resource_id}": resource_doc
            for resource_doc in ResourceDoc.objects.filter(gateway_id=self.gateway_id)
        }
        for doc in docs:
            doc.resource = resources.get(doc.resource_name)
            if doc.resource:
                doc.resource_doc = resource_docs.get(f"{doc.language.value}:{doc.resource.id}")

            if doc.resource_doc:
                doc.content_changed = self._generate_md5(doc.content) != self._generate_md5(doc.resource_doc.content)

    def _generate_md5(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()


class ArchiveParser(BaseParser):
    """
    归档文件解析
    - 解析归档文件，提取文档语言、文档内容、资源名称
    - 根据文档语言、资源名称，获取出资源、资源文档对象
    """

    def parse(self, archive_file: IO[AnyStr]) -> List[ArchiveDoc]:
        """
        :param archive_file: 归档文件
        """
        with TemporaryDirectory() as output_dir:
            files = ArchiveFileFactory.from_fileobj(archive_file).extractall(output_dir, archive_file)
            files = self._filter_files(files)
            docs = self._parse(files)
            self._enrich_docs(docs)
            return docs

    def _filter_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """
        过滤文件
        - 只保留 1 ~ 2 级目录的文件，如 en/get_users.md, docs/en/get_users.md
        """
        return {filename: filepath for filename, filepath in files.items() if len(filename.split("/")) in [2, 3]}

    def _parse(self, files: Dict[str, str]) -> List[ArchiveDoc]:
        """
        :param files: filename to full filepath
        """
        docs = []
        for filename, filepath in files.items():
            language = self._extract_language(filename)
            if not language:
                continue

            resource_name = self._extract_resource_name(filename)
            if not resource_name:
                continue

            docs.append(
                ArchiveDoc(
                    resource_name=resource_name,
                    language=DocLanguageEnum(language),
                    content=Jinja2ToMarkdownGenerator(filename, filepath).generate_doc_content(),
                    filename=filename,
                )
            )

        if not docs:
            raise NoResourceDocError(_("无有效的资源文档。"))

        return docs

    def _extract_language(self, filename: str) -> Optional[str]:
        """
        根据文件名提取语言

        :param filename: 形如：en/get_user.md, docs/en/get_users.md
        """
        parts = filename.rsplit("/", 2)
        if len(parts) < 2:
            return None

        language = parts[-2]

        available_languages = DocLanguageEnum.get_values()
        if language not in available_languages:
            return None

        return language

    def _extract_resource_name(self, filename: str) -> Optional[str]:
        """
        根据文件名提取资源名称
        - 忽略下划线开头的文件
        - 忽略非 .md, .md.j2 结尾的文件

        :param filename: 形如：en/get_user.md, docs/en/get_users.md
        """
        name = filename.rsplit("/", 1)[-1]

        if name.startswith("_"):
            return None

        if name.endswith(".md"):
            return name[:-3]

        if name.endswith(".md.j2"):
            # `.md.j2` 结尾的为 jinja2 模板文件，用于支持文档的模板渲染
            return name[:-6]

        return None


class OpenAPIParser(BaseParser):
    """Swagger 描述文件解析"""

    def parse(self, swagger: str, language: DocLanguageEnum) -> List[OpenAPIDoc]:
        docs = self._parse(swagger, language)
        self._enrich_docs(docs)
        return docs

    def _parse(self, openapi: str, language: DocLanguageEnum) -> List[OpenAPIDoc]:
        gateway = Gateway.objects.get(id=self.gateway_id)
        openapi_manager = OpenAPIImportManager.load_from_content(gateway, openapi)

        validate_err_list = openapi_manager.validate()
        if len(validate_err_list) > 0 or not openapi_manager.parser:
            raise SchemaValidationError("")

        docs = []
        for path, path_item in openapi_manager.parser.get_paths().items():
            for method, original_operation in path_item.items():
                converted_operation = original_operation
                if openapi_manager.version != OPENAPIV2:
                    converted_operation = convert_operation_v3_to_v2(original_operation)
                openapi = OpenAPIExportManager(title=converted_operation["operationId"]).get_swagger_by_paths(
                    paths={
                        path: {method: converted_operation},
                    },
                    openapi_format=OpenAPIFormatEnum.YAML,
                )
                docs.append(
                    OpenAPIDoc(
                        resource_name=converted_operation["operationId"],
                        language=language,
                        content=OpenAPIToMarkdownGenerator(openapi, language).generate_doc_content(),
                        openapi=openapi,
                    )
                )

        return docs
