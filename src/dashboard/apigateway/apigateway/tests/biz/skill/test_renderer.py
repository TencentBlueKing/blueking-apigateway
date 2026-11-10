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

from apigateway.biz.skill.declaration import parse_declaration
from apigateway.biz.skill.renderer import SkillRenderError, render_skill_body
from apigateway.tests.biz.skill.conftest import EXPECTED_DIR, GOLDEN_NAMES, load_declaration_data
from apigateway.tests.biz.skill.static_provider import StaticResourceProvider

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

    def test_param_not_in_definition(self, static_provider):
        data = load_declaration_data("job-plan-run-and-log")
        data["orchestration"]["steps"][0]["with"]["unknown"] = "${{ inputs.bk_scope_id }}"

        with pytest.raises(SkillRenderError, match="没有参数 unknown"):
            render_skill_body(parse_declaration(data), static_provider)

    def test_condition_and_ref_text(self, static_provider):
        body = _render("job-plan-run-and-log", static_provider)

        assert "3. collect-log / batch_get_job_instance_ip_log：拉取失败主机日志" in body
        assert "   执行条件：`data.job_instance.status` 不是 3（执行成功）" in body
        assert "带「执行条件」的步骤，条件不成立时跳过。" in body
        assert "x-from: ${{ steps.run-plan.outputs.data.job_instance_id }}" in body
        assert "x-value: true" in body

    def test_unmapped_param_listed(self, static_provider):
        data = load_declaration_data("job-plan-run-and-log")
        data["orchestration"]["steps"][0]["with"].pop("job_plan_id")
        data["orchestration"]["steps"][2].pop("if")

        body = render_skill_body(parse_declaration(data), static_provider).body

        assert "资源定义中必填但未映射：`job_plan_id`，按本步说明处理。" in body
        assert "没有 `x-from`、`x-value` 的参数按该步说明取值" in body
        assert "执行条件" not in body

    def test_responses_only_referenced_fields(self, static_provider):
        data = load_declaration_data("job-plan-run-and-log")
        outputs = data["orchestration"]["outputs"]
        data["orchestration"]["outputs"] = {"job_instance_id": outputs["job_instance_id"]}

        body = render_skill_body(parse_declaration(data), static_provider).body
        wait_result = body.split("2. wait-result", 1)[1].split("3. collect-log", 1)[0]

        assert "responses" not in wait_result
