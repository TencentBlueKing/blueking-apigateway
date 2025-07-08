#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from tempfile import TemporaryDirectory

import pytest

from apigateway.biz.resource_doc.exceptions import (
    ResourceDocJinja2TemplateError,
    ResourceDocJinja2TemplateNotFound,
    ResourceDocJinja2TemplateSyntaxError,
)
from apigateway.biz.resource_doc.importer.generators import Jinja2ToMarkdownGenerator
from apigateway.utils.file import write_to_file


class TestJinja2ToMarkdownGenerator:
    def test_generate_doc_content(self):
        with TemporaryDirectory() as output_dir:
            filepath_1 = os.path.join(output_dir, "get_user.md.j2")
            filepath_2 = os.path.join(output_dir, "create_user.md")

            write_to_file("get_user", filepath_1)
            write_to_file("create_user", filepath_2)

            result = Jinja2ToMarkdownGenerator("zh/get_user.md.j2", filepath_1).generate_doc_content()
            assert result == "get_user"

            result = Jinja2ToMarkdownGenerator("zh/create_user.md", filepath_2).generate_doc_content()
            assert result == "create_user"

    @pytest.mark.parametrize(
        "filepath, expected",
        [
            ("get_user.md.j2", True),
            ("get_user.md", False),
            ("get_user.j2", False),
        ],
    )
    def test_is_jinja2_template(self, faker, filepath, expected):
        generator = Jinja2ToMarkdownGenerator(faker.pystr(), filepath)
        assert generator._is_jinja2_template() is expected

    def test_render_jinja2_template(self, mocker):
        with TemporaryDirectory() as output_dir:
            filepath = os.path.join(output_dir, "get_user.md.j2")
            generator = Jinja2ToMarkdownGenerator("get_user.md.j2", filepath)

            write_to_file("{% include '_common.md.j2' %}, get_user", filepath)
            write_to_file("hi", os.path.join(output_dir, "_common.md.j2"))
            assert generator._render_jinja2_template() == "hi, get_user"

            write_to_file("{% include '_common.md.j2 %}, get_user", filepath)
            with pytest.raises(ResourceDocJinja2TemplateSyntaxError) as err:
                generator._render_jinja2_template()
            assert output_dir not in str(err.value)

            write_to_file("{% include '_not_found.md.j2' %}, get_user", filepath)
            with pytest.raises(ResourceDocJinja2TemplateNotFound):
                generator._render_jinja2_template()

            mocker.patch(
                "apigateway.biz.resource_doc.importer.generators.SandboxedEnvironment.get_template",
                side_effect=ValueError(),
            )
            write_to_file("{% include '_common.md.j2' %}, get_user", filepath)
            with pytest.raises(ResourceDocJinja2TemplateError):
                generator._render_jinja2_template()
