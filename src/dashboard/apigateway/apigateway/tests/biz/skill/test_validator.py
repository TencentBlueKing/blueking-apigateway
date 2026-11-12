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

        assert result.missing_resources == [
            MissingResource(
                "jobv3-cloud", "prod", "get_job_instance_status", reason="fixture 中没有资源 get_job_instance_status"
            )
        ]
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
        _with(job_plan_data, 1)["bk_scope_id"] = "${{ inputs.not_exists }}"

        assert _validate(job_plan_data, static_provider).errors == [
            "wait-result.with.bk_scope_id：输入 not_exists 不存在"
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

    def test_required_param_missing_from_with(self, static_provider, job_plan_data):
        _with(job_plan_data, 0).pop("job_plan_id")
        job_plan_data["orchestration"]["inputs"].pop("job_plan_id")

        result = _validate(job_plan_data, static_provider)

        assert result.errors == ["run-plan：资源定义中必填的参数没有写进 with：job_plan_id"]
        assert result.warnings == []

    def test_optional_param_missing_from_with(self, static_provider, job_plan_data):
        _with(job_plan_data, 1).pop("return_ip_result")

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    def test_each_params_from_different_arrays(self, resources_data, job_plan_data):
        for resource in resources_data["resources"]:
            if resource["resource"] == "batch_get_job_instance_ip_log":
                resource["params"].append({"name": "step_name", "in": "body", "type": "string"})
            elif resource["resource"] == "get_job_instance_status":
                resource["response"].append({"field": "data.other_list[].name", "type": "string"})
        _with(job_plan_data, 2)["step_name"] = "${{ steps.wait-result.outputs.data.other_list[].name }}"

        result = _validate(job_plan_data, StaticResourceProvider.from_dict(resources_data))

        assert result.errors == [
            "collect-log：逐个调用的参数须取自同一个数组："
            "steps.wait-result.outputs.data.other_list, steps.wait-result.outputs.data.step_instance_list"
        ]

    def test_array_param_from_all_elements_is_not_each(self, resources_data, job_plan_data):
        for resource in resources_data["resources"]:
            if resource["resource"] == "batch_get_job_instance_ip_log":
                resource["params"].append({"name": "step_ids", "in": "body", "type": "array<integer>"})
            elif resource["resource"] == "get_job_instance_status":
                resource["response"].append({"field": "data.other_list[].id", "type": "integer"})
        _with(job_plan_data, 2)["step_ids"] = "${{ steps.wait-result.outputs.data.other_list[].id }}"

        result = _validate(job_plan_data, StaticResourceProvider.from_dict(resources_data))

        assert (result.errors, result.warnings) == ([], [])

    def test_literal_value_not_type_checked(self, static_provider, job_plan_data):
        _with(job_plan_data, 0)["job_plan_id"] = "1024"
        job_plan_data["orchestration"]["inputs"].pop("job_plan_id")

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    @pytest.mark.parametrize(
        "patch, expected",
        [
            (
                lambda data: _with(data, 1).update(bk_scope_id="${{ inputs.job_plan_id }}"),
                "inputs.job_plan_id：类型 integer 与绑定参数不一致：wait-result.with.bk_scope_id (string)",
            ),
            (
                lambda data: data["orchestration"]["inputs"]["job_plan_id"].update(type="string", example="1024"),
                "inputs.job_plan_id：类型 string 与绑定参数不一致：run-plan.with.job_plan_id (integer)",
            ),
            (
                lambda data: data["orchestration"]["inputs"]["bk_scope_id"].update(type="integer|string"),
                (
                    "inputs.bk_scope_id：类型 integer|string 与绑定参数不一致："
                    "run-plan.with.bk_scope_id (string), wait-result.with.bk_scope_id (string), "
                    "collect-log.with.bk_scope_id (string)"
                ),
            ),
            (
                lambda data: data["orchestration"]["inputs"]["job_plan_id"].update(required=False),
                "run-plan.with.job_plan_id：参数 job_plan_id 在资源定义中必填，输入 job_plan_id 却是选填且没有默认值",
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
    def test_field_errors(self, static_provider, job_plan_data, patch, expected):
        patch(job_plan_data)

        result = _validate(job_plan_data, static_provider)

        assert expected in result.errors, result.errors
        assert result.warnings == []

    def test_untyped_param_not_compared(self, static_provider, job_plan_data):
        resource = static_provider.get_resource("jobv3-cloud", "prod", "get_job_instance_status")
        resource.get_param("bk_scope_id").type = ""
        _with(job_plan_data, 1)["bk_scope_id"] = "${{ inputs.job_plan_id }}"

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    @pytest.mark.parametrize(
        "name, output, expected",
        [
            (
                "job_instance_id",
                {"type": "string"},
                "outputs.job_instance_id：类型 string 与来源不一致，应为 integer",
            ),
            # collect-log 逐个调用，单次响应的 data 是 object，汇总后是数组
            (
                "failed_host_logs",
                {"type": "object"},
                "outputs.failed_host_logs：类型 object 与来源不一致，应为 array<object>",
            ),
            (
                "step_results",
                {
                    "type": "integer",
                    "value": "${{ steps.wait-result.outputs.data.step_instance_list[].step_instance_id }}",
                },
                "outputs.step_results：类型 integer 与来源不一致，应为 array<integer>",
            ),
            (
                "job_status",
                {"type": "integer", "value": "${{ inputs.bk_scope_id }}"},
                "outputs.job_status：类型 integer 与来源不一致，应为 string",
            ),
        ],
    )
    def test_output_type_mismatch(self, static_provider, job_plan_data, name, output, expected):
        job_plan_data["orchestration"]["outputs"][name].update(output)

        result = _validate(job_plan_data, static_provider)

        assert result.errors == [expected]
        assert result.warnings == []

    @pytest.mark.parametrize(
        "name, output",
        [
            (
                "step_results",
                {
                    "type": "integer",
                    "value": "${{ steps.wait-result.outputs.data.step_instance_list[0].step_instance_id }}",
                },
            ),
            (
                "step_results",
                {
                    "type": "array<integer>",
                    "value": "${{ steps.wait-result.outputs.data.step_instance_list[].step_instance_id }}",
                },
            ),
            ("job_status", {"type": "string", "value": "${{ inputs.bk_scope_id }}"}),
        ],
    )
    def test_output_type_matches_source(self, static_provider, job_plan_data, name, output):
        job_plan_data["orchestration"]["outputs"][name].update(output)

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    def test_untyped_response_field_not_compared(self, static_provider, job_plan_data):
        resource = static_provider.get_resource("jobv3-cloud", "prod", "execute_job_plan")
        next(item for item in resource.responses if item.field == "data.job_instance_id").type = ""
        job_plan_data["orchestration"]["outputs"]["job_instance_id"]["type"] = "string"

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])

    def test_required_param_from_optional_input_with_default(self, static_provider, job_plan_data):
        job_plan_data["orchestration"]["inputs"]["job_plan_id"].update(required=False, default=1024)

        result = _validate(job_plan_data, static_provider)

        assert (result.errors, result.warnings) == ([], [])
