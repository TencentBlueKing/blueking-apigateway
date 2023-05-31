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
import pytest

from apigateway.utils.template import TemplatedStructureGenerator


class TestTemplatedStructureGenerator:
    @pytest.fixture()
    def template_dir(self, tmp_path):
        template_dir = tmp_path / "template_dir"
        template_dir.mkdir()

        return template_dir

    @pytest.fixture()
    def output_dir(self, tmp_path):
        output_dir = tmp_path / "output_dir"
        output_dir.mkdir()

        return output_dir

    @pytest.fixture()
    def template_under_root(self, template_dir):
        template = template_dir / "template.txt.j2"
        template.write_text("{{value}}")
        return template

    @pytest.fixture()
    def template_subdir(self, template_dir):
        subdir = template_dir / "sub"
        subdir.mkdir()

        return subdir

    @pytest.fixture()
    def template_under_subdir(self, template_subdir):
        template = template_subdir / "template.txt.j2"
        template.write_text("{{value}}")
        return template

    @pytest.fixture()
    def empty_dir(self, template_dir):
        empty_dir = template_dir / "empty"
        empty_dir.mkdir()
        return empty_dir

    @pytest.fixture()
    def file_under_root(self, template_dir):
        file = template_dir / "file.txt"
        file.write_text("{{value}}")
        return file

    @pytest.fixture()
    def file_under_subdir(self, template_subdir):
        file = template_subdir / "file.txt"
        file.write_text("{{value}}")
        return file

    @pytest.fixture()
    def template_under_root_output(self, output_dir):
        return output_dir / "template.txt"

    @pytest.fixture()
    def template_under_subdir_output(self, output_dir):
        return output_dir / "sub" / "template.txt"

    @pytest.fixture()
    def empty_dir_output(self, output_dir):
        return output_dir / "empty"

    @pytest.fixture()
    def file_under_root_output(self, output_dir):
        return output_dir / "file.txt"

    @pytest.fixture()
    def file_under_subdir_output(self, output_dir):
        return output_dir / "sub" / "file.txt"

    @pytest.fixture()
    def template_syntax_changed(self, template_dir):
        template = template_dir / "changed.txt.j2"
        template.write_text("{{ {$ value $} }}")
        return template

    @pytest.fixture()
    def template_syntax_changed_output(self, output_dir):
        return output_dir / "changed.txt"

    def test_generate(
        self,
        template_dir,
        output_dir,
        template_under_root,
        template_under_root_output,
        template_under_subdir,
        template_under_subdir_output,
        empty_dir,
        empty_dir_output,
        file_under_root,
        file_under_root_output,
        file_under_subdir,
        file_under_subdir_output,
    ):
        generator = TemplatedStructureGenerator(template_dir=template_dir)
        generator.generate(output_dir, {"value": "test"})

        assert template_under_root_output.read_text() == "test"
        assert template_under_subdir_output.read_text() == "test"
        assert empty_dir_output.exists()
        assert file_under_root_output.read_text() == file_under_root.read_text()
        assert file_under_subdir_output.read_text() == file_under_subdir.read_text()

    def test_generate_with_escaping(
        self,
        template_dir,
        output_dir,
        template_syntax_changed,
        template_syntax_changed_output,
    ):
        generator = TemplatedStructureGenerator(
            template_dir=template_dir,
            template_environment_attrs={
                "variable_start_string": "{$",
                "variable_end_string": "$}",
            },
        )
        generator.generate(output_dir, {"value": "test"})

        assert template_syntax_changed_output.read_text() == "{{ test }}"
