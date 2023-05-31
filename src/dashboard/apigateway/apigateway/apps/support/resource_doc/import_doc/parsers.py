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
"""解析资源文档"""
import os
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional

from bkapi_client_generator import expand_swagger
from django.utils.translation import gettext as _

from apigateway.apps.resource.swagger.swagger import SwaggerManager
from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.resource_doc.exceptions import NoResourceDocError
from apigateway.apps.support.resource_doc.import_doc.docs import ArchiveDoc, SwaggerDoc
from apigateway.core.constants import SwaggerFormatEnum
from apigateway.utils.file import read_file, write_to_file


class ArchiveParser:
    """归档文件解析"""

    def parse(self, files: Dict[str, str]) -> List[ArchiveDoc]:
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
                    language=DocLanguageEnum(language),
                    resource_name=resource_name,
                    filename=filename,
                    resource_doc_path=filepath,
                )
            )

        if not docs:
            raise NoResourceDocError(_("无有效的资源文档。"))

        return docs

    def _extract_language(self, filename: str) -> str:
        return filename.partition("/")[0]

    def _extract_resource_name(self, filename: str) -> Optional[str]:
        name = filename.partition("/")[2]

        if name.startswith("_"):
            return None

        elif name.endswith(".md"):
            return name[:-3]

        elif name.endswith(".md.j2"):
            # `.md.j2` 结尾的为 jinja2 模板文件，用于支持文档的模板渲染
            return name[:-6]

        return None


class SwaggerParser:
    """Swagger 描述文件解析"""

    def parse(self, swagger: str, language: DocLanguageEnum) -> List[SwaggerDoc]:
        expanded_swagger = self._expand_swagger(swagger)
        swagger_manager = SwaggerManager.load_from_swagger(expanded_swagger)
        swagger_manager.validate()

        docs = []
        for path, path_item in swagger_manager.get_paths().items():
            for method, operation in path_item.items():
                docs.append(
                    SwaggerDoc(
                        language=language,
                        resource_name=operation["operationId"],
                        resource_doc_swagger=SwaggerManager.to_swagger(
                            paths={
                                path: {method: operation},
                            },
                            title=operation["operationId"],
                            swagger_format=SwaggerFormatEnum.YAML,
                        ),
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
