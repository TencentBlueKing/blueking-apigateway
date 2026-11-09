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


def _run_call(data: dict) -> dict:
    return data["orchestration"]["steps"][0]["calls"][0]


def _status_call(data: dict) -> dict:
    return data["orchestration"]["steps"][1]["calls"][0]


def _log_call(data: dict) -> dict:
    return data["orchestration"]["steps"][2]["calls"][0]


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

    def test_unknown_input(self, static_provider, job_plan_data):
        _run_call(job_plan_data)["params"]["job_plan_id"] = "inputs.not_exists"

        assert _validate(job_plan_data, static_provider).errors == [
            "run-plan.execute_job_plan.params.job_plan_id：输入 not_exists 不存在"
        ]

    def test_ref_to_later_call(self, static_provider, job_plan_data):
        _run_call(job_plan_data)["params"]["bk_scope_id"] = "wait-result.get_job_instance_status.data.finished"

        errors = _validate(job_plan_data, static_provider).errors

        assert errors == [
            "run-plan.execute_job_plan.params.bk_scope_id：引用的调用 wait-result.get_job_instance_status 不在当前调用之前"
        ]

    def test_ref_to_call_repeated_in_step(self, static_provider, job_plan_data):
        steps = job_plan_data["orchestration"]["steps"]
        steps[0]["calls"].append(dict(_run_call(job_plan_data)))

        errors = _validate(job_plan_data, static_provider).errors

        assert any("在步骤 run-plan 内出现多次" in error for error in errors), errors

    @pytest.mark.parametrize(
        "patch, expected",
        [
            (
                lambda data: _run_call(data)["params"].update(unknown="inputs.bk_scope_id"),
                "run-plan.execute_job_plan：参数 unknown 不在资源定义中",
            ),
            (
                lambda data: _run_call(data)["params"].update(job_plan_id="inputs.bk_scope_id"),
                "run-plan.execute_job_plan.params.job_plan_id：输入类型 string 与参数类型 integer 不一致",
            ),
            (
                lambda data: _run_call(data)["params"].pop("job_plan_id"),
                "run-plan.execute_job_plan：必填参数 job_plan_id 未映射，需在步骤说明中交代",
            ),
            (
                lambda data: _log_call(data)["params"].update(step_instance_id="each.not_exists"),
                (
                    "collect-log.batch_get_job_instance_ip_log.params.step_instance_id："
                    "get_job_instance_status 的响应定义中没有 data.step_instance_list[].not_exists"
                ),
            ),
            (
                lambda data: _status_call(data)["reads"].append("data.not_exists"),
                "wait-result.get_job_instance_status.reads：响应定义中没有 data.not_exists",
            ),
            (
                lambda data: data["orchestration"]["outputs"][0].update({"from": "run-plan.execute_job_plan.missing"}),
                "outputs.job_instance_id：execute_job_plan 的响应定义中没有 missing",
            ),
        ],
    )
    def test_field_warnings(self, static_provider, job_plan_data, patch, expected):
        patch(job_plan_data)

        result = _validate(job_plan_data, static_provider)

        assert result.errors == []
        assert expected in result.warnings, result.warnings

    def test_poll_field_warning(self, static_provider, job_plan_data):
        job_plan_data["orchestration"]["steps"][1]["calls"][0]["poll"]["until"] = "data.not_exists == true"

        warnings = _validate(job_plan_data, static_provider).warnings

        assert "wait-result.get_job_instance_status.poll：响应定义中没有 data.not_exists" in warnings
