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


def _body_properties(body: str, index: int) -> dict:
    """第 index 步（从 0 起）YAML 调用说明里的请求体字段"""
    _, block = YAML_BLOCK_PATTERN.findall(body)[index]
    return yaml.safe_load(textwrap.dedent(block))["requestBody"]["content"]["application/json"]["schema"]["properties"]


class TestRenderSkillBody:
    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_golden(self, static_provider, name):
        result = render_skill_body(parse_declaration(load_declaration_data(name)), static_provider)

        assert result.body == (EXPECTED_DIR / f"{name}.md").read_text(encoding="utf-8")
        assert result.warnings == []

    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_openapi_sections_are_valid(self, static_provider, name):
        blocks = YAML_BLOCK_PATTERN.findall(_render(name, static_provider))

        assert blocks
        for _, block in blocks:
            call = yaml.safe_load(textwrap.dedent(block))
            assert all(call[key] for key in ("gateway_name", "stage_name", "resource_name", "method", "path"))

            operation = {key: call[key] for key in ("parameters", "requestBody", "responses") if key in call}
            validate(
                {
                    "openapi": "3.1.0",
                    "info": {"title": name, "version": "1.0.0"},
                    "paths": {call["path"]: {call["method"].lower(): operation}},
                }
            )

    def test_oauth2_client_columns(self, resources_data):
        for resource in resources_data["resources"]:
            if resource["resource"] == "execute_job_plan":
                resource["auth"]["oauth2_public_client_enabled"] = True
                resource["auth"]["oauth2_personal_client_enabled"] = True

        catalog = (
            _render("job-plan-run-and-log", StaticResourceProvider.from_dict(resources_data))
            .split("## 接口清单", 1)[1]
            .split("## 输入", 1)[0]
        )

        assert "| OAuth2 public client | OAuth2 personal client |" in catalog
        execute = next(line for line in catalog.splitlines() if line.startswith("| `execute_job_plan`"))
        status = next(line for line in catalog.splitlines() if line.startswith("| `get_job_instance_status`"))
        assert execute.endswith("| 是 | 是 | 是 | 是 | 是 |")
        assert status.endswith("| 是 | 是 | 是 | 否 | 否 |")

    def test_no_interface_available_column(self, static_provider):
        body = _render("job-plan-run-and-log", static_provider)

        assert "可用" not in body.split("## 输入", 1)[0]

    def test_input_description_comes_from_openapi(self, resources_data):
        data = load_declaration_data("job-plan-run-and-log")
        data["orchestration"]["inputs"]["bk_scope_id"]["description"] = "声明中的编排提示"
        for resource in resources_data["resources"]:
            if resource["resource"] == "execute_job_plan":
                resource["params"][1]["description"] = "完整 OpenAPI 说明，包含枚举 A | B 和其他内容"
            elif resource["resource"] == "get_job_instance_status":
                resource["params"][1]["description"] = "第二个接口的不同说明"

        body = render_skill_body(
            parse_declaration(data),
            StaticResourceProvider.from_dict(resources_data),
        ).body
        input_section = body.split("## 输入", 1)[1].split("## 输出", 1)[0]

        assert (
            "| `bk_scope_id` | string | 是 | 完整 OpenAPI 说明，包含枚举 A \\| B 和其他内容；第二个接口的不同说明；"
            "资源范围 ID | 声明中的编排提示 |"
        ) in input_section
        assert "| `global_var_list` | array<object> |" in input_section

    def test_param_schema_copied_from_openapi(self, resources_data):
        execute = next(item for item in resources_data["resources"] if item["resource"] == "execute_job_plan")
        scope = execute["params"][0]
        scope["schema"] = {"type": "string", "enum": ["biz", "biz_set"], "x-from": "源 schema 的扩展"}
        global_var_list = next(item for item in execute["params"] if item["name"] == "global_var_list")

        properties = _body_properties(
            _render("job-plan-run-and-log", StaticResourceProvider.from_dict(resources_data)), 0
        )

        assert properties["bk_scope_type"] == {
            "type": "string",
            "enum": ["biz", "biz_set"],
            "description": scope["description"],
            "x-from": "${{ inputs.bk_scope_type }}",
        }
        assert properties["global_var_list"]["items"] == global_var_list["schema"]["items"]

    def test_output_type_comes_from_declaration(self, static_provider):
        output_section = (
            _render("job-plan-run-and-log", static_provider).split("## 输出", 1)[1].split("## 执行步骤", 1)[0]
        )

        assert "| 字段 | 类型 | 说明 | 来源 |" in output_section
        assert "| `job_instance_id` | integer | 作业实例 ID |" in output_section
        # collect-log 按失败步骤逐个调用，单次响应的 data 是 object，汇总后是数组
        assert "| `failed_host_logs` | array<object> |" in output_section

    def test_input_descriptions_drop_duplicates_and_contained(self, static_provider):
        input_section = _render("job-plan-run-and-log", static_provider).split("## 输入", 1)[1].split("## 输出", 1)[0]

        assert input_section.count("资源范围类型：biz 业务，biz_set 业务集") == 1
        assert "| 资源范围 ID，与 bk_scope_type 对应的业务 ID 或业务集 ID | - |" in input_section

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

    def test_step_description_and_ref_text(self, static_provider):
        body = _render("job-plan-run-and-log", static_provider)

        assert "3. collect-log / batch_get_job_instance_ip_log：拉取失败主机日志" in body
        assert "   仅当 wait-result 正常结束（`data.finished` 为 true）且 `data.job_instance.status` 不是 3" in body
        assert "执行条件" not in body
        assert "x-from: ${{ steps.run-plan.outputs.data.job_instance_id }}" in body
        assert "x-value: true" in body

    def test_each_binding(self, static_provider):
        body = _render("job-plan-run-and-log", static_provider)
        properties = _body_properties(body, 2)

        assert properties["step_instance_id"]["x-from"] == (
            "${{ steps.wait-result.outputs.data.step_instance_list[].step_instance_id }}"
        )
        assert properties["step_instance_id"]["x-each"] is True
        assert "x-each" not in properties["job_instance_id"]
        assert "`x-each: true` 表示逐个调用" in body
        # 只有逐个调用用到 `[]`，不写「组成的数组」
        assert "组成的数组" not in body

    def test_array_param_from_all_elements(self, resources_data):
        data = load_declaration_data("job-plan-run-and-log")
        data["orchestration"]["steps"][2]["with"]["step_ids"] = (
            "${{ steps.wait-result.outputs.data.step_instance_list[].step_instance_id }}"
        )
        for resource in resources_data["resources"]:
            if resource["resource"] == "batch_get_job_instance_ip_log":
                resource["params"].append({"name": "step_ids", "in": "body", "type": "array<integer>"})

        body = render_skill_body(parse_declaration(data), StaticResourceProvider.from_dict(resources_data)).body

        assert "x-each" not in _body_properties(body, 2)["step_ids"]
        assert "`[]` 是数组每个元素的该字段组成的数组" in body

    def test_parameter_name_does_not_define_authentication(self, resources_data):
        data = load_declaration_data("job-plan-run-and-log")
        data["orchestration"]["inputs"]["access_token"] = {
            "type": "string",
            "required": True,
            "description": "接口业务参数，不是网关认证凭据",
            "example": "example-token",
        }
        data["orchestration"]["steps"][0]["with"]["access_token"] = "${{ inputs.access_token }}"
        resources_data["resources"][0]["params"].append(
            {
                "name": "access_token",
                "in": "query",
                "type": "string",
                "required": True,
                "description": "接口业务参数",
            }
        )

        body = render_skill_body(
            parse_declaration(data),
            StaticResourceProvider.from_dict(resources_data),
        ).body
        run_plan = body.split("1. run-plan", 1)[1].split("2. wait-result", 1)[0]

        assert "name: access_token" in run_plan
        assert "x-from: ${{ inputs.access_token }}" in run_plan

    def test_responses_keep_unreferenced_schema(self, resources_data):
        data = load_declaration_data("job-plan-run-and-log")
        outputs = data["orchestration"]["outputs"]
        data["orchestration"]["outputs"] = {"job_instance_id": outputs["job_instance_id"]}
        for resource in resources_data["resources"]:
            if resource["resource"] == "get_job_instance_status":
                resource["response"].append(
                    {
                        "field": "data.step_instance_list",
                        "type": "array<object>",
                        "description": "步骤列表，含状态码 12 强制终止失败和其他说明",
                    }
                )

        body = render_skill_body(
            parse_declaration(data),
            StaticResourceProvider.from_dict(resources_data),
        ).body
        wait_result = body.split("2. wait-result", 1)[1].split("3. collect-log", 1)[0]

        assert "已发布接口的响应字段" in wait_result
        assert "作业是否结束" in wait_result
        assert "步骤列表，含状态码 12 强制终止失败和其他说明" in wait_result
        assert "step_ip_result_list:" in wait_result
