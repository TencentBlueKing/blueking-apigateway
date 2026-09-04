#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import hashlib
from tempfile import TemporaryDirectory
from typing import IO, Any, AnyStr, Dict, List, Optional, Union

from django.utils.translation import gettext as _

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.openapi import OpenAPIImportManager
from apigateway.biz.resource_doc import ArchiveFileFactory, NoResourceDocError
from apigateway.common.exceptions import SchemaValidationError
from apigateway.core.constants import HTTP_METHOD_ANY
from apigateway.core.models import Gateway, Resource
from apigateway.service.resource_version import OpenAPIExportManager
from apigateway.utils.yaml import yaml_export_dumps

from .generators import Jinja2ToMarkdownGenerator, OpenAPIToMarkdownGenerator
from .models import ArchiveDoc, OpenAPIDoc
from .presenters import OperationDocBuilder


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
        - 忽略下划线开头的文件以及._开头的(mac压缩的文件解压会包含._重名文件)
        - 忽略非 .md, .md.j2 结尾的文件

        :param filename: 形如：en/get_user.md, docs/en/get_users.md
        """
        name = filename.rsplit("/", 1)[-1]

        if name.startswith(("_", "._")):
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

    def parse_resource_data(self, resources: List[Dict[str, Any]], language: DocLanguageEnum) -> List[OpenAPIDoc]:
        """根据已校验的资源导入 DTO 生成文档，避免再次走 OpenAPI 资源导入校验。"""
        docs = self._parse_resources(resources, language)
        self._enrich_docs(docs)
        return docs

    def _parse_resources(
        self,
        resources: List[Dict[str, Any]],
        language: DocLanguageEnum,
    ) -> List[OpenAPIDoc]:
        docs = []
        for resource in resources:
            method = resource["method"].upper()
            if method == HTTP_METHOD_ANY:
                continue

            openapi_data = OpenAPIExportManager(
                title=resource["name"],
                include_bk_apigateway_resource=False,
            ).get_openapi_content([resource])
            operation = openapi_data["paths"][resource["path"]][method.lower()]
            operation["summary"] = resource.get("summary", "")
            operation["deprecated"] = resource.get("deprecated", False)
            context = OperationDocBuilder(openapi_data).build()
            docs.append(
                OpenAPIDoc(
                    resource_name=resource["name"],
                    language=language,
                    content=OpenAPIToMarkdownGenerator(context, language).generate_doc_content(),
                    openapi=yaml_export_dumps(openapi_data),
                )
            )

        return docs

    def _parse(self, openapi: str, language: DocLanguageEnum) -> List[OpenAPIDoc]:
        gateway = Gateway.objects.get(id=self.gateway_id)
        openapi_manager = OpenAPIImportManager.load_from_content(gateway, openapi)

        validate_err_list = openapi_manager.validate()
        if len(validate_err_list) > 0 or not openapi_manager.parser:
            raise SchemaValidationError("")

        return self._parse_resources(openapi_manager.get_resource_list(raw=True), language)
