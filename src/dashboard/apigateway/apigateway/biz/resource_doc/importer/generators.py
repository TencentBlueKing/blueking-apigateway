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
import os
import logging
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

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


class Jinja2ToMarkdownGenerator:
    def __init__(self, filename: str, filepath: str):
        self.filename = filename
        self.filepath = filepath

    def generate_doc_content(self) -> str:
        try:
            if self._is_jinja2_template():
                return self._render_jinja2_template()
            else:
                with open(self.filepath, 'r', encoding='utf-8') as file:
                    return file.read()
        except Exception as e:
            # 记录错误日志
            logging.error(f"Error processing file {self.filepath}: {e}")
            # 返回给前端的错误信息
            return f"Error processing file {self.filepath}: {str(e)}"

    def _is_jinja2_template(self) -> bool:
        return self.filepath.endswith(".md.j2")

    def _render_jinja2_template(self) -> str:
        env = SandboxedEnvironment(loader=FileSystemLoader(os.path.dirname(self.filepath)))
        try:
            template = env.get_template(os.path.basename(self.filepath))
            # 假设没有上下文，如果有需要，可以传递一个 context 字典
            return template.render()
        except TemplateSyntaxError as err:
            logging.error(f"Syntax error in template {self.filepath}: {err}")
            return f"Syntax error in template {self.filepath}: {str(err)}"
        except TemplateNotFound as err:
            logging.error(f"Template {self.filename} not found: {err}")
            return f"Template {self.filename} not found: {str(err)}"
        except Exception as err:
            logging.error(f"Unexpected error rendering template {self.filepath}: {err}")
            return f"Unexpected error rendering template {self.filepath}: {str(err)}"

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
