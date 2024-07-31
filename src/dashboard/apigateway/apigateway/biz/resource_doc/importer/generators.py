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
import os
from tempfile import TemporaryDirectory

from bkapi_client_generator import generate_markdown
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound, TemplatesNotFound, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc.exceptions import (
    ResourceDocJinja2TemplateError,
    ResourceDocJinja2TemplateNotFound,
    ResourceDocJinja2TemplateSyntaxError,
)
from apigateway.utils.file import read_file, write_to_file

logger = logging.getLogger(__name__)


class Jinja2ToMarkdownGenerator:
    """根据 Jinja2 模版文件，生成 markdown 格式文档"""

    def __init__(self, filename: str, filepath: str):
        self.filename = filename
        self.filepath = filepath

    def generate_doc_content(self) -> str:
        if self._is_jinja2_template():
            return self._render_jinja2_template()

        # 检查是否能够打开文件
        try:
            content = read_file(self.filepath)
        except Exception as err:
            logger.exception("File reading failure for _render_jinja2_template %s", self.filepath)
            raise ValueError(f"Failed to read file {self.filepath}: {err}")

        # 检查文件编码是否正确
        try:
            decoded_content = content.decode()
        except UnicodeDecodeError as err:
            logger.exception("File encoding error for _render_jinja2_template %s", self.filepath)
            raise ValueError(f"Error decoding file {self.filepath}: {err}")

        return decoded_content

    def _is_jinja2_template(self) -> bool:
        return self.filepath.endswith(".md.j2")

    def _render_jinja2_template(self) -> str:
        env = SandboxedEnvironment(loader=FileSystemLoader(os.path.dirname(self.filepath)))
        try:
            template = env.get_template(os.path.basename(self.filepath))
            return template.render()
        except TemplateSyntaxError as err:
            logger.exception("TemplateSyntaxError for _render_jinja2_template %s", self.filepath)
            raise ResourceDocJinja2TemplateSyntaxError(self._base_path, self.filename, err)
        except (TemplateNotFound, TemplatesNotFound) as err:
            logger.exception("TemplateNotFound for _render_jinja2_template %s", self.filepath)
            raise ResourceDocJinja2TemplateNotFound(self.filename, err)
        except Exception as err:
            logger.exception("Unexpected error for _render_jinja2_template %s", self.filepath)
            raise ResourceDocJinja2TemplateError(self.filename, err)

    @property
    def _base_path(self) -> str:
        """文档目录地址，如：/tmp/xxx，此目录下为文档语言目录"""
        return self.filepath[: -len(self.filename)]


class OpenAPIToMarkdownGenerator:
    """根据 openapi 生成 markdown 格式文档"""

    def __init__(self, openapi_data: str, language: DocLanguageEnum):
        self.openapi_data = openapi_data
        self.language = language

    def generate_doc_content(self) -> str:
        if not self.openapi_data:
            return ""

        with TemporaryDirectory() as output_dir:
            openapi_filepath = os.path.join(output_dir, "swagger.yaml")
            write_to_file(self.openapi_data, openapi_filepath)
            doc_filepath = generate_markdown(
                swagger=openapi_filepath,
                language=self.language.value,
                output=os.path.join(output_dir, "docs.md"),
            )
            return read_file(doc_filepath).decode().strip()
