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
import pytest

from apigateway.biz.skill.declaration import parse_declaration
from apigateway.biz.skill.validator import MissingResource, validate_declaration
from apigateway.tests.biz.skill.conftest import GOLDEN_NAMES, load_declaration_data
from apigateway.tests.biz.skill.static_provider import StaticResourceProvider

pytestmark = pytest.mark.no_meta_schema


def _validate(data: dict, provider):
    return validate_declaration(parse_declaration(data), provider)


def _with(data: dict, index: int) -> dict:
    return data["orchestration"]["steps"][index]["with"]


class TestValidateDeclaration:
    @pytest.mark.parametrize("name", GOLDEN_NAMES)
    def test_golden(self, static_provider, name):
        result = _validate(load_declaration_data(name), static_provider)

        assert (result.errors, result.warnings, result.missing_resources) == ([], [], [])

    def test_missing_resource(self, resources_data, job_plan_data):
        resources_data["resources"] = [
            item for item in resources_data["resources"] if item["resource"] != "get_job_instance_status"
        ]

        result = _validate(job_plan_data, StaticResourceProvider.from_dict(resources_data))

        assert result.missing_resources == [MissingResource("jobv3-cloud", "prod", "get_job_instance_status")]
        assert result.errors == []
        # 缺失资源相关的字段级检查跳过，不产生 warning
        assert result.warnings == []

    def test_resource_warnings_passed_through(self, static_provider, job_plan_data):
        static_provider.get_resource("jobv3-cloud", "prod", "execute_job_plan").warnings.append("schema 缺失")

        assert _validate(job_plan_data, static_provider).warnings == ["schema 缺失"]

    def test_resource_errors_skip_field_checks(self, static_provider, job_plan_data):
        resource = static_provider.get_resource("jobv3-cloud", "prod", "execute_job_plan")
        resource.params = []
        resource.responses = []
        resource.errors.append("jobv3-cloud.execute_job_plan：请求体不是 application/json")

        result = _validate(job_plan_data, static_provider)

        assert result.errors == ["jobv3-cloud.execute_job_plan：请求体不是 application/json"]
        assert result.warnings == []

    def test_param_not_in_definition_is_error(self, static_provider, job_plan_data):
        _with(job_plan_data, 0)["unknown"] = "${{ inputs.bk_scope_id }}"

        result = _validate(job_plan_data, static_provider)

        assert result.errors == ["run-plan：参数 unknown 不在资源定义中"]
        assert result.warnings == []

    def test_unknown_input(self, static_provider, job_plan_data):
        _with(job_plan_data, 0)["job_plan_id"] = "${{ inputs.not_exists }}"

        assert _validate(job_plan_data, static_provider).errors == [
            "run-plan.with.job_plan_id：输入 not_exists 不存在"
        ]

    @pytest.mark.parametrize("ref_step", ["wait-result", "run-plan", "not-exists"])
    def test_ref_to_non_previous_step(self, static_provider, job_plan_data, ref_step):
        _with(job_plan_data, 0)["bk_scope_id"] = f"${{{{ steps.{ref_step}.outputs.data.finished }}}}"

        errors = _validate(job_plan_data, static_provider).errors

        assert errors == [f"run-plan.with.bk_scope_id：引用的步骤 {ref_step} 不在当前步骤之前"]

    def test_output_ref_to_unknown_step(self, static_provider, job_plan_data):
        job_plan_data["orchestration"]["outputs"]["job_status"]["value"] = "${{ steps.not-exists.outputs.data }}"

        errors = _validate(job_plan_data, static_provider).errors

        assert errors == ["outputs.job_status：引用的步骤 not-exists 不在当前步骤之前"]

    def test_unmapped_required_param_not_reported(self, static_provider, job_plan_data):
        _with(job_plan_data, 0).pop("job_plan_id")

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    def test_literal_value_not_type_checked(self, static_provider, job_plan_data):
        _with(job_plan_data, 0)["job_plan_id"] = "1024"

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    @pytest.mark.parametrize(
        "patch, expected",
        [
            (
                lambda data: _with(data, 0).update(job_plan_id="${{ inputs.bk_scope_id }}"),
                "run-plan.with.job_plan_id：输入类型 string 与参数类型 integer 不一致",
            ),
            (
                lambda data: _with(data, 2).update(
                    job_instance_id="${{ steps.wait-result.outputs.data.step_instance_list[].not_exists }}"
                ),
                (
                    "collect-log.with.job_instance_id："
                    "get_job_instance_status 的响应定义中没有 data.step_instance_list[].not_exists"
                ),
            ),
            (
                lambda data: data["orchestration"]["outputs"]["job_instance_id"].update(
                    value="${{ steps.run-plan.outputs.missing }}"
                ),
                "outputs.job_instance_id：execute_job_plan 的响应定义中没有 missing",
            ),
        ],
    )
    def test_field_warnings(self, static_provider, job_plan_data, patch, expected):
        patch(job_plan_data)

        result = _validate(job_plan_data, static_provider)

        assert result.errors == []
        assert expected in result.warnings, result.warnings
