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
import os
from tempfile import TemporaryDirectory
from typing import IO, AnyStr, Dict, List, Optional, Union

from bkapi_client_generator import expand_swagger
from django.utils.translation import gettext as _

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.resource_doc.archive_factory import ArchiveFileFactory
from apigateway.biz.resource_doc.exceptions import NoResourceDocError
from apigateway.biz.resource_import.swagger.swagger import SwaggerManager
from apigateway.core.constants import SwaggerFormatEnum
from apigateway.core.models import Resource
from apigateway.utils.file import read_file, write_to_file

from .generators import Jinja2ToMarkdownGenerator, SwaggerToMarkdownGenerator
from .models import ArchiveDoc, SwaggerDoc


class BaseParser:
    def __init__(self, gateway_id: int):
        self.gateway_id = gateway_id

    def _enrich_docs(self, docs: Union[List[ArchiveDoc], List[SwaggerDoc]]):
        """
        丰富文档数据
        - 补全解析文档对应的资源、资源文档对象
        - 判断文档内容是否变更
        """
        resources = {resource.name: resource for resource in Resource.objects.filter(api_id=self.gateway_id)}
        # en/zh share the same resource_id, use add language to distinguish
        resource_docs = {
            f"{resource_doc.language}:{resource_doc.resource_id}": resource_doc
            for resource_doc in ResourceDoc.objects.filter(api_id=self.gateway_id)
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
            docs = self._parse(files)
            self._enrich_docs(docs)
            return docs

    def _parse(self, files: Dict[str, str]) -> List[ArchiveDoc]:
        """
        :param files: filename to full filepath
        """
        available_languages = DocLanguageEnum.get_values()

        docs = []
        for filename, filepath in files.items():
            language = self._extract_language(filename)
            if language not in available_languages:
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

    def _extract_language(self, filename: str) -> str:
        """
        根据文件名提取语言

        :param filename: 形如：en/get_user.md
        """
        return filename.partition("/")[0]

    def _extract_resource_name(self, filename: str) -> Optional[str]:
        """
        根据文件名提取资源名称
        - 忽略下划线开头的文件
        - 忽略非 .md, .md.j2 结尾的文件

        :param filename: 形如：en/get_user.md
        """
        name = filename.partition("/")[2]

        if name.startswith("_"):
            return None

        elif name.endswith(".md"):
            return name[:-3]

        elif name.endswith(".md.j2"):
            # `.md.j2` 结尾的为 jinja2 模板文件，用于支持文档的模板渲染
            return name[:-6]

        return None


class SwaggerParser(BaseParser):
    """Swagger 描述文件解析"""

    def parse(self, swagger: str, language: DocLanguageEnum) -> List[SwaggerDoc]:
        docs = self._parse(swagger, language)
        self._enrich_docs(docs)
        return docs

    def _parse(self, swagger: str, language: DocLanguageEnum) -> List[SwaggerDoc]:
        expanded_swagger = self._expand_swagger(swagger)
        swagger_manager = SwaggerManager.load_from_swagger(expanded_swagger)
        swagger_manager.validate()

        docs = []
        for path, path_item in swagger_manager.get_paths().items():
            for method, operation in path_item.items():
                swagger = SwaggerManager.to_swagger(
                    paths={
                        path: {method: operation},
                    },
                    title=operation["operationId"],
                    swagger_format=SwaggerFormatEnum.YAML,
                )
                docs.append(
                    SwaggerDoc(
                        resource_name=operation["operationId"],
                        language=language,
                        content=SwaggerToMarkdownGenerator(swagger, language).generate_doc_content(),
                        swagger=swagger,
                    )
                )

        return docs

    def _expand_swagger(self, swagger: str) -> str:
        """展开 swagger 描述

        - 参考：https://goswagger.io/usage/expand.html
        """
        swagger_format = SwaggerManager.guess_swagger_format(swagger)

        with TemporaryDirectory() as output_dir:
            src = os.path.join(output_dir, f"swagger.{swagger_format.value}")
            dst = os.path.join(output_dir, f"expanded_swagger.{swagger_format.value}")

            write_to_file(swagger, src)
            expand_swagger(src, swagger_format.value, dst)
            return read_file(dst).decode()
