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
import logging
import os
from typing import TYPE_CHECKING

from django.conf import settings
from jinja2 import FileSystemLoader, StrictUndefined
from jinja2.exceptions import TemplateError, TemplateNotFound, TemplatesNotFound, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment

from apigateway.biz.resource_doc import (
    OpenAPIDocGenerationError,
    ResourceDocJinja2TemplateError,
    ResourceDocJinja2TemplateNotFound,
    ResourceDocJinja2TemplateSyntaxError,
)
from apigateway.utils.file import read_file

if TYPE_CHECKING:
    from apigateway.apps.support.constants import DocLanguageEnum

    from .models import OperationDocContext

logger = logging.getLogger(__name__)

DOC_LABELS = {
    "en": {
        "api_information": "API information",
        "method": "Method",
        "path": "Path",
        "operation_id": "Operation ID",
        "tags": "Tags",
        "deprecated": "Deprecated",
        "description": "Description",
        "request_parameters": "Request parameters",
        "path_parameters": "Path parameters",
        "query_parameters": "Query parameters",
        "header_parameters": "Header parameters",
        "cookie_parameters": "Cookie parameters",
        "name": "Name",
        "type": "Type",
        "required": "Required",
        "default": "Default",
        "constraints": "Constraints",
        "example": "Example",
        "request_body": "Request body",
        "responses": "Responses",
        "status_code": "Status code",
        "status": "Status",
        "response_headers": "Response headers",
        "field": "Field",
        "yes": "Yes",
        "no": "No",
    },
    "zh": {
        "api_information": "API 信息",
        "method": "方法",
        "path": "路径",
        "operation_id": "操作 ID",
        "tags": "标签",
        "deprecated": "已废弃",
        "description": "描述",
        "request_parameters": "请求参数",
        "path_parameters": "路径参数",
        "query_parameters": "查询参数",
        "header_parameters": "请求头参数",
        "cookie_parameters": "Cookie 参数",
        "name": "名称",
        "type": "类型",
        "required": "必填",
        "default": "默认值",
        "constraints": "约束",
        "example": "示例",
        "request_body": "请求体",
        "responses": "响应",
        "status_code": "状态码",
        "status": "状态",
        "response_headers": "响应头",
        "field": "字段",
        "yes": "是",
        "no": "否",
    },
}


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
        except Exception as err:  # pylint: disable=broad-except
            logger.exception("File reading failure for generate_doc_content %s", self.filepath)
            raise ValueError(f"Failed to read file {self.filepath}: {err}")

        # 检查文件编码是否正确
        try:
            decoded_content = content.decode()
        except UnicodeDecodeError as err:
            logger.exception("File encoding error for generate_doc_content %s", self.filepath)
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
        except Exception as err:  # pylint: disable=broad-except
            logger.exception("Unexpected error for _render_jinja2_template %s", self.filepath)
            raise ResourceDocJinja2TemplateError(self.filename, err)

    @property
    def _base_path(self) -> str:
        """文档目录地址，如：/tmp/xxx，此目录下为文档语言目录"""
        return self.filepath[: -len(self.filename)]


class OpenAPIToMarkdownGenerator:
    """根据 openapi 生成 markdown 格式文档"""

    template_name = "operation.md.j2"

    def __init__(self, context: OperationDocContext, language: DocLanguageEnum):
        self.context = context
        self.language = language

    def generate_doc_content(self) -> str:
        template_dir = os.path.join(settings.BASE_DIR, "templates", "resource_doc", "openapi")
        env = SandboxedEnvironment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        try:
            language = str(getattr(self.language, "value", self.language))
            labels = DOC_LABELS[language]
            return env.get_template(self.template_name).render(doc=self.context, labels=labels).strip()
        except (KeyError, TemplateError) as err:
            logger.exception("failed to render built-in OpenAPI resource documentation")
            raise OpenAPIDocGenerationError("failed to render OpenAPI resource documentation") from err
