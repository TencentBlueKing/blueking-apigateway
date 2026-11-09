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

from apigateway.biz.skill import SkillDeclarationError, normalize_tag_name, parse_declaration
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

        assert data["outputs"][0]["from"] == "run-plan.execute_job_plan.data.job_instance_id"
        assert "from_" not in data["outputs"][0]
        # global_var_list 没写 default，不能导出成 default: null
        global_var_list = next(item for item in data["inputs"] if item["name"] == "global_var_list")
        assert "default" not in global_var_list

    def test_has_default(self, job_plan_data):
        orchestration = parse_declaration(job_plan_data).orchestration

        assert orchestration.get_input("bk_scope_type").has_default
        assert not orchestration.get_input("global_var_list").has_default
        assert orchestration.is_omittable_input_ref("inputs.global_var_list")
        assert not orchestration.is_omittable_input_ref("inputs.bk_scope_id")


class TestTopLevelRules:
    @pytest.mark.parametrize(
        "field, value",
        [
            ("name", "Bad_Name"),
            ("name", "a" * 65),
            ("display_name", ""),
            ("display_name_en", None),
            ("description", ""),
            ("version", "1.0"),
            ("version", 1.0),
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


class TestOrchestrationRules:
    def test_duplicate_step_name(self, job_plan_data):
        steps = job_plan_data["orchestration"]["steps"]
        steps[1]["name"] = steps[0]["name"]

        assert _errors(job_plan_data)

    def test_empty_calls(self, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["calls"] = []

        assert _errors(job_plan_data)

    def test_each_without_for_each(self, job_plan_data):
        job_plan_data["orchestration"]["steps"][2]["calls"][0].pop("for_each")

        assert _errors(job_plan_data)

    def test_for_each_must_reference_call(self, job_plan_data):
        job_plan_data["orchestration"]["steps"][2]["calls"][0]["for_each"]["from"] = "inputs.bk_scope_id"

        assert _errors(job_plan_data)

    def test_poll_with_for_each(self, job_plan_data):
        call = job_plan_data["orchestration"]["steps"][2]["calls"][0]
        call["poll"] = copy.deepcopy(job_plan_data["orchestration"]["steps"][1]["calls"][0]["poll"])

        assert _errors(job_plan_data)

    @pytest.mark.parametrize(
        "patch",
        [
            {"interval": 0},
            {"max": -1},
            {"max": True},
            {"until": "data.finished"},
            {"until": "data.list[].status == 1"},
            {"stop_when": [{"expr": "data.status == 3", "times": 0}]},
        ],
    )
    def test_invalid_poll(self, job_plan_data, patch):
        job_plan_data["orchestration"]["steps"][1]["calls"][0]["poll"].update(patch)

        assert _errors(job_plan_data)

    @pytest.mark.parametrize(
        "ref",
        [
            "a.b",
            {"value": 1, "extra": 2},
            {"ref": "inputs.limit", "where": ""},
            1,
        ],
    )
    def test_invalid_ref(self, job_plan_data, ref):
        job_plan_data["orchestration"]["steps"][0]["calls"][0]["params"]["job_plan_id"] = ref

        assert _errors(job_plan_data)

    def test_where_requires_array_path(self, job_plan_data):
        job_plan_data["orchestration"]["steps"][1]["calls"][0]["params"]["job_instance_id"] = {
            "ref": "run-plan.execute_job_plan.data.job_instance_id",
            "where": "id == 1",
        }

        errors = _errors(job_plan_data)

        assert any("where" in error for error in errors), errors

    def test_guide_fields_required(self, job_plan_data):
        job_plan_data["orchestration"]["guide"]["example"] = ""

        assert _errors(job_plan_data)

    def test_unknown_call_field(self, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["calls"][0]["foo"] = 1

        errors = _errors(job_plan_data)

        assert errors == ["orchestration.steps[0].calls[0].foo: 未知字段"]
