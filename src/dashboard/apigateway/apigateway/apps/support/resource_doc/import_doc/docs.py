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
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Optional

from bkapi_client_generator import generate_markdown
from jinja2 import FileSystemLoader
from jinja2.exceptions import TemplateNotFound, TemplatesNotFound, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.resource_doc.exceptions import (
    ResourceDocJinja2TemplateError,
    ResourceDocJinja2TemplateNotFound,
    ResourceDocJinja2TemplateSyntaxError,
)
from apigateway.utils.file import read_file, write_to_file


@dataclass
class BaseDoc:
    language: DocLanguageEnum
    resource_name: str
    resource_id: Optional[int] = None
    resource_doc_id: Optional[int] = None
    resource_doc_swagger_id: Optional[int] = None

    @property
    def doc_key(self) -> Optional[str]:
        if not self.resource_id:
            return None
        return f"{self.resource_id}:{self.language.value}"

    @property
    def resource_doc_markdown(self) -> str:
        raise NotImplementedError


@dataclass
class ArchiveDoc(BaseDoc):
    filename: str = ""
    resource_doc_path: str = ""

    @property
    def resource_doc_markdown(self) -> str:
        if self._is_jinja2_template():
            return self._render_jinja2_template()

        return read_file(self.resource_doc_path).decode()

    def _is_jinja2_template(self):
        return self.resource_doc_path.endswith(".md.j2")

    def _render_jinja2_template(self):
        env = SandboxedEnvironment(loader=FileSystemLoader(os.path.dirname(self.resource_doc_path)))
        try:
            template = env.get_template(os.path.basename(self.resource_doc_path))
            return template.render()
        except TemplateSyntaxError as err:
            raise ResourceDocJinja2TemplateSyntaxError(self._resource_doc_base_path, self.filename, err)
        except (TemplateNotFound, TemplatesNotFound) as err:
            raise ResourceDocJinja2TemplateNotFound(self.filename, err)
        except Exception as err:
            raise ResourceDocJinja2TemplateError(self.filename, err)

    @property
    def _resource_doc_base_path(self) -> str:
        """文档目录地址，如：/tmp/xxx，此目录下为文档语言目录"""
        return self.resource_doc_path[: -len(self.filename)]


@dataclass
class SwaggerDoc(BaseDoc):
    resource_doc_swagger: str = ""

    @property
    def resource_doc_markdown(self) -> str:
        if not self.resource_doc_swagger:
            return ""

        with TemporaryDirectory() as temp_dir:
            swagger = os.path.join(temp_dir, "swagger.yaml")
            write_to_file(self.resource_doc_swagger, swagger)

            doc_path = generate_markdown(
                swagger=swagger, language=self.language.value, output=os.path.join(temp_dir, "docs.md")
            )
            return read_file(doc_path).decode().strip()
