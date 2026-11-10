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
import copy

import pytest
import yaml

from apigateway.biz.skill.declaration import SkillDeclarationError, normalize_tag_name, parse_declaration
from apigateway.tests.biz.skill.conftest import DECLARATIONS_DIR, GOLDEN_NAMES

pytestmark = pytest.mark.no_meta_schema


def _errors(data: dict) -> list:
    with pytest.raises(SkillDeclarationError) as exc_info:
        parse_declaration(data)
    return exc_info.value.errors


class TestParseDeclaration:
    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_golden_declarations(self, name):
        declaration = parse_declaration((DECLARATIONS_DIR / f"{name}.yaml").read_text(encoding="utf-8"))

        assert declaration.name == name
        assert declaration.normalized_tags

    def test_yaml_text_and_dict(self, job_plan_data):
        from_text = parse_declaration(yaml.safe_dump(job_plan_data, allow_unicode=True))
        from_dict = parse_declaration(job_plan_data)

        assert from_text == from_dict

    @pytest.mark.parametrize("text", ["", "- a\n- b\n", "name: [\n"])
    def test_not_a_mapping(self, text):
        errors = _errors(text)

        assert errors
        assert all("\n" not in error for error in errors)

    def test_orchestration_data_keeps_unset_fields_out(self, job_plan_data):
        data = parse_declaration(job_plan_data).orchestration_data()

        assert data["outputs"]["job_instance_id"]["value"] == "${{ steps.run-plan.outputs.data.job_instance_id }}"
        # global_var_list 没写 default，不能导出成 default: null
        assert "default" not in data["inputs"]["global_var_list"]
        # if、with 按原键名导出；没写 if 的步骤不导出 if: null
        assert data["steps"][2]["if"] == job_plan_data["orchestration"]["steps"][2]["if"]
        assert "if" not in data["steps"][0]
        assert data["steps"][1]["with"]["return_ip_result"] is True
        assert data == job_plan_data["orchestration"]

    def test_has_default(self, job_plan_data):
        orchestration = parse_declaration(job_plan_data).orchestration

        assert orchestration.get_input("bk_scope_type").has_default
        assert not orchestration.get_input("global_var_list").has_default
        assert orchestration.is_omittable_input_ref("${{ inputs.global_var_list }}")
        assert not orchestration.is_omittable_input_ref("${{ inputs.bk_scope_id }}")
        assert not orchestration.is_omittable_input_ref("inputs.global_var_list")

    def test_step_target(self, job_plan_data):
        step = parse_declaration(job_plan_data).orchestration.steps[0]

        assert step.key == ("jobv3-cloud", "prod", "execute_job_plan")
        assert (step.gateway, step.stage, step.resource) == step.key


class TestTopLevelRules:
    @pytest.mark.parametrize(
        "field, value",
        [
            ("name", "Bad_Name"),
            ("name", "a" * 65),
            ("name", "job-plan-run-and-log\n"),
            ("display_name", ""),
            ("display_name", "   "),
            ("display_name", "x" * 65),
            ("display_name", "执行\n作业方案"),
            ("display_name", "执行\r作业方案"),
            ("display_name_en", "   "),
            ("display_name_en", "x" * 65),
            ("description", ""),
            ("version", "1.0"),
            ("version", 1.0),
            ("version", "1.0.0\n"),
            ("tags", []),
            ("tags", ["JOB", " job "]),
            ("tags", ["x" * 65]),
        ],
    )
    def test_invalid_field(self, job_plan_data, field, value):
        job_plan_data[field] = value

        errors = _errors(job_plan_data)

        assert any(error.startswith(f"{field}") for error in errors), errors

    @pytest.mark.parametrize("field", ["featured", "categories"])
    def test_unknown_field(self, job_plan_data, field):
        job_plan_data[field] = True

        assert _errors(job_plan_data)

    def test_tags_normalized(self, job_plan_data):
        job_plan_data["tags"] = [" JOB ", "写操作"]

        assert parse_declaration(job_plan_data).normalized_tags == ["job", "写操作"]
        assert normalize_tag_name("  Job ") == "job"

    def test_changelog_optional(self, job_plan_data):
        job_plan_data.pop("changelog")

        assert parse_declaration(job_plan_data).changelog == ""

    def test_display_name_en_null(self, job_plan_data):
        job_plan_data["display_name_en"] = None

        assert parse_declaration(job_plan_data).display_name_en is None

    def test_display_name_strips_and_allows_punctuation(self, job_plan_data):
        job_plan_data["display_name"] = "  作业_方案（生产）/日志 𠀀\n"
        job_plan_data["display_name_en"] = "  Run_Job (prod)\n"

        declaration = parse_declaration(job_plan_data)

        assert declaration.display_name == "作业_方案（生产）/日志 𠀀"
        assert declaration.display_name_en == "Run_Job (prod)"


class TestOrchestrationRules:
    def test_step_id_trailing_newline(self, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["id"] = "run-plan\n"

        assert _errors(job_plan_data)

    def test_duplicate_step_id(self, job_plan_data):
        steps = job_plan_data["orchestration"]["steps"]
        steps[1]["id"] = steps[0]["id"]

        errors = _errors(job_plan_data)

        assert any("步骤 id 重复：run-plan" in error for error in errors), errors

    @pytest.mark.parametrize("field", ["id", "uses", "description"])
    def test_step_required_field(self, job_plan_data, field):
        job_plan_data["orchestration"]["steps"][0].pop(field)

        errors = _errors(job_plan_data)

        assert f"orchestration.steps[0].{field}: 缺少必填字段" in errors

    @pytest.mark.parametrize("field", ["name", "if", "description"])
    def test_step_text_not_empty(self, job_plan_data, field):
        job_plan_data["orchestration"]["steps"][2][field] = " "

        errors = _errors(job_plan_data)

        assert any(error.startswith(f"orchestration.steps[2].{field}") for error in errors), errors

    def test_name_if_with_optional(self, job_plan_data):
        step = job_plan_data["orchestration"]["steps"][1]
        for field in ("name", "if", "with"):
            step.pop(field, None)

        parsed = parse_declaration(job_plan_data).orchestration.steps[1]

        assert (parsed.name, parsed.if_, parsed.with_) == (None, None, {})

    @pytest.mark.parametrize(
        "uses",
        [
            "jobv3-cloud/execute_job_plan",
            "jobv3-cloud@prod",
            "jobv3-cloud/execute_job_plan@prod/x",
            "../../etc/execute_job_plan@prod",
            "Job/execute_job_plan@prod",
            "jobv3-cloud/get-task@prod",
            "jobv3-cloud/execute_job_plan@../prod",
        ],
    )
    def test_invalid_uses(self, job_plan_data, uses):
        job_plan_data["orchestration"]["steps"][0]["uses"] = uses

        errors = _errors(job_plan_data)

        assert any(error.startswith("orchestration.steps[0].uses") for error in errors), errors

    @pytest.mark.parametrize(
        "value",
        [
            "${{ inputs.job_plan_id }} ",
            "id-${{ inputs.job_plan_id }}",
            "${{ inputs.a }}${{ inputs.b }}",
            "${{ env.JOB_PLAN_ID }}",
            "${{ steps.run-plan.data.job_instance_id }}",
            "${{ steps.run-plan.outputs. }}",
            "${{ inputs.作业 }}",
            {"id": "${{ inputs.job_plan_id }}"},
            ["${{ inputs.job_plan_id }}"],
        ],
    )
    def test_invalid_ref(self, job_plan_data, value):
        job_plan_data["orchestration"]["steps"][0]["with"]["job_plan_id"] = value

        errors = _errors(job_plan_data)

        assert any(error.startswith("orchestration.steps[0].with.job_plan_id") for error in errors), errors

    @pytest.mark.parametrize("value", [1, "inputs.job_plan_id", {"value": 1}, [1, 2], None, "${ip_list}"])
    def test_literal_value(self, job_plan_data, value):
        job_plan_data["orchestration"]["steps"][0]["with"]["job_plan_id"] = value
        job_plan_data["orchestration"]["inputs"].pop("job_plan_id")

        step = parse_declaration(job_plan_data).orchestration.steps[0]

        assert step.with_["job_plan_id"] == value

    @pytest.mark.parametrize("value", [1, "data.job_instance_id", "x ${{ inputs.bk_scope_id }}"])
    def test_output_must_be_ref(self, job_plan_data, value):
        job_plan_data["orchestration"]["outputs"]["job_instance_id"]["value"] = value

        errors = _errors(job_plan_data)

        assert any(error.startswith("orchestration.outputs.job_instance_id.value") for error in errors), errors

    @pytest.mark.parametrize("name", ["1st", "业务", "a.b"])
    def test_invalid_input_name(self, job_plan_data, name):
        job_plan_data["orchestration"]["inputs"][name] = copy.deepcopy(
            job_plan_data["orchestration"]["inputs"]["bk_scope_id"]
        )

        errors = _errors(job_plan_data)

        assert any("输入名不合规" in error for error in errors), errors

    def test_inputs_must_be_mapping(self, job_plan_data):
        job_plan_data["orchestration"]["inputs"] = [{"name": "bk_scope_id"}]

        errors = _errors(job_plan_data)

        assert errors == ["orchestration.inputs: 应为对象"]

    @pytest.mark.parametrize("section, name", [("inputs", "bk_scope_id"), ("outputs", "job_instance_id")])
    def test_type_not_declared(self, job_plan_data, section, name):
        job_plan_data["orchestration"][section][name]["type"] = "string"

        errors = _errors(job_plan_data)

        assert errors == [f"orchestration.{section}.{name}.type: 未知字段"]

    def test_input_description_optional(self, job_plan_data):
        assert "description" not in job_plan_data["orchestration"]["inputs"]["bk_scope_id"]

        assert parse_declaration(job_plan_data).orchestration.get_input("bk_scope_id").description == ""

    def test_input_must_be_bound(self, job_plan_data):
        job_plan_data["orchestration"]["inputs"]["unused"] = {"required": False, "example": 1}

        errors = _errors(job_plan_data)

        assert errors == ["orchestration: 输入没有绑定到任何步骤的 with，类型和说明无从取得：unused"]

    def test_guide_fields_required(self, job_plan_data):
        job_plan_data["orchestration"]["guide"]["example"] = ""

        assert _errors(job_plan_data)

    @pytest.mark.parametrize("field", ["calls", "params", "poll", "for_each", "reads", "run", "env"])
    def test_unknown_step_field(self, job_plan_data, field):
        job_plan_data["orchestration"]["steps"][0][field] = 1

        errors = _errors(job_plan_data)

        assert errors == [f"orchestration.steps[0].{field}: 未知字段"]
