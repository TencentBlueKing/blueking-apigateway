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
import re
import textwrap

import pytest
import yaml
from openapi_spec_validator import validate

from apigateway.biz.skill import SkillRenderError, StaticResourceProvider, parse_declaration, render_skill_body
from apigateway.tests.biz.skill.conftest import EXPECTED_DIR, GOLDEN_NAMES, load_declaration_data

pytestmark = pytest.mark.no_meta_schema

YAML_BLOCK_PATTERN = re.compile(r"^( *)```yaml\n(.*?)^\1```$", re.MULTILINE | re.DOTALL)


def _render(name: str, provider: StaticResourceProvider) -> str:
    return render_skill_body(parse_declaration(load_declaration_data(name)), provider).body


class TestRenderSkillBody:
    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_golden(self, static_provider, name):
        result = render_skill_body(parse_declaration(load_declaration_data(name)), static_provider)

        assert result.body == (EXPECTED_DIR / f"{name}.md").read_text(encoding="utf-8")
        assert result.warnings == []

    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_openapi_snippets_are_valid(self, static_provider, name):
        blocks = YAML_BLOCK_PATTERN.findall(_render(name, static_provider))

        assert blocks
        for _, block in blocks:
            snippet = yaml.safe_load(textwrap.dedent(block))
            validate({"openapi": "3.1.0", "info": {"title": name, "version": "1.0.0"}, **snippet})

    def test_no_interface_available_column(self, static_provider):
        body = _render("job-plan-run-and-log", static_provider)

        assert "可用" not in body.split("## 输入", 1)[0]

    def test_write_mode(self, static_provider, resources_data):
        assert "会改动线上状态的接口" in _render("job-plan-run-and-log", static_provider)

        for item in resources_data["resources"]:
            item["method"] = "GET"

        assert "会改动线上状态的接口" not in _render(
            "job-plan-run-and-log", StaticResourceProvider.from_dict(resources_data)
        )

    def test_too_many_lines(self, mocker, static_provider):
        mocker.patch("apigateway.biz.skill.renderer.SKILL_BODY_MAX_LINES", 10)

        result = render_skill_body(parse_declaration(load_declaration_data("job-plan-run-and-log")), static_provider)

        assert len(result.warnings) == 1
        assert "超过 10 行" in result.warnings[0]

    def test_missing_resource(self, resources_data):
        resources_data["resources"] = [
            item for item in resources_data["resources"] if item["resource"] != "get_job_instance_status"
        ]

        with pytest.raises(SkillRenderError, match="get_job_instance_status"):
            _render("job-plan-run-and-log", StaticResourceProvider.from_dict(resources_data))
