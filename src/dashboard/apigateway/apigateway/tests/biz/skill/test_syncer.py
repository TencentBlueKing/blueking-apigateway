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
import yaml

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion
from apigateway.biz.skill import SkillSyncStatusEnum, sync_platform_skills
from apigateway.biz.skill.renderer import render_skill_body
from apigateway.tests.biz.skill.conftest import release_fixture_gateway, release_resources

pytestmark = pytest.mark.django_db

JOB_PLAN = "job-plan-run-and-log"


@pytest.fixture
def declarations_dir(tmp_path, resources_data):
    release_fixture_gateway(resources_data, "jobv3-cloud")
    return tmp_path / "declarations"


@pytest.fixture
def write_declaration(declarations_dir):
    declarations_dir.mkdir(exist_ok=True)

    def write(data, file_name=None):
        path = declarations_dir / f"{file_name or data['name']}.yaml"
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return path

    return write


def _sync(declarations_dir, **kwargs):
    return sync_platform_skills(declarations_dir, **kwargs)


def _statuses(results):
    return [(result.name, result.status) for result in results]


class TestSyncPlatformSkills:
    def test_created(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(job_plan_data)

        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.CREATED.value)]
        assert results[0].warnings == []
        metadata = SkillMetadata.objects.get(type=SkillTypeEnum.PLATFORM.value, gateway=None, name=JOB_PLAN)
        assert results[0].metadata_id == metadata.id
        body = metadata.current_version.artifact["SKILL.md"]
        assert body.startswith("# 执行作业方案并收集日志")
        assert "execute_job_plan" in body

    def test_same_version_then_new_version(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(job_plan_data)
        _sync(declarations_dir)

        assert _statuses(_sync(declarations_dir)) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]

        job_plan_data["version"] = "1.1.0"
        write_declaration(job_plan_data)
        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.RELEASED.value)]
        assert SkillVersion.objects.filter(metadata_id=results[0].metadata_id).count() == 2

    def test_lower_version_rejected(self, declarations_dir, write_declaration, job_plan_data):
        job_plan_data["version"] = "1.1.0"
        write_declaration(job_plan_data)
        _sync(declarations_dir)

        job_plan_data["version"] = "1.0.1"
        write_declaration(job_plan_data)
        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]
        assert results[0].reasons == [f"{JOB_PLAN} 的版本 1.0.1 不高于当前版本 1.1.0"]
        metadata = SkillMetadata.objects.get(name=JOB_PLAN)
        assert metadata.current_version.version == "1.1.0"
        assert metadata.versions.count() == 1

    def test_param_not_in_definition_rejected(self, declarations_dir, write_declaration, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["with"]["unknown"] = "${{ inputs.bk_scope_id }}"
        write_declaration(job_plan_data)

        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]
        assert results[0].reasons == ["run-plan：参数 unknown 不在资源定义中"]
        assert not SkillMetadata.objects.exists()

    def test_missing_resources(self, caplog, declarations_dir, write_declaration, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["uses"] = "jobv3-cloud/not_released@prod"
        write_declaration(job_plan_data)

        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]
        assert "jobv3-cloud.not_released（环境 prod）不可编排" in results[0].reasons[0]
        assert "已配置 OpenAPI 请求参数和响应参数" in results[0].reasons[0]
        assert f"skip platform skill {JOB_PLAN}" in caplog.text
        assert not SkillMetadata.objects.exists()

    def test_rejected_does_not_stop_others(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration({"name": "Bad_Name"}, file_name="a-bad")
        outputs = job_plan_data["orchestration"]["outputs"]
        invalid_ref = {**job_plan_data, "name": "b-invalid-ref"}
        invalid_ref["orchestration"] = {
            **job_plan_data["orchestration"],
            "outputs": {"job_instance_id": {**outputs["job_instance_id"], "value": "${{ inputs.not_exists }}"}},
        }
        write_declaration(invalid_ref)
        write_declaration(job_plan_data)

        results = _sync(declarations_dir)

        assert _statuses(results) == [
            ("a-bad", SkillSyncStatusEnum.SKIPPED.value),
            ("b-invalid-ref", SkillSyncStatusEnum.SKIPPED.value),
            (JOB_PLAN, SkillSyncStatusEnum.CREATED.value),
        ]
        assert results[1].reasons == ["outputs.job_instance_id：输入 not_exists 不存在"]
        assert list(SkillMetadata.objects.values_list("name", flat=True)) == [JOB_PLAN]

    def test_failed_does_not_stop_others(self, mocker, declarations_dir, write_declaration, job_plan_data):
        write_declaration({**job_plan_data, "name": "a-first"})
        write_declaration(job_plan_data)

        def render(declaration, provider):
            if declaration.name == "a-first":
                raise RuntimeError("boom")
            return render_skill_body(declaration, provider)

        mocker.patch("apigateway.biz.skill.syncer.render_skill_body", side_effect=render)

        results = _sync(declarations_dir)

        assert _statuses(results) == [
            ("a-first", SkillSyncStatusEnum.SKIPPED.value),
            (JOB_PLAN, SkillSyncStatusEnum.CREATED.value),
        ]
        assert results[0].reasons == ["RuntimeError: boom"]

    def test_dry_run(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(job_plan_data)

        results = _sync(declarations_dir, dry_run=True)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.CREATED.value)]
        assert not SkillMetadata.objects.exists()

    def test_name_filter(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(job_plan_data)
        write_declaration({**job_plan_data, "name": "other-skill"})

        assert _statuses(_sync(declarations_dir, name="other-skill")) == [
            ("other-skill", SkillSyncStatusEnum.CREATED.value)
        ]

    def test_file_name_must_match_declaration_name(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(job_plan_data, file_name="other-file")

        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]
        assert results[0].reasons == ["文件名 other-file 与声明的 name job-plan-run-and-log 不一致"]
        assert not SkillMetadata.objects.exists()

    def test_no_openapi_schema_skipped(self, tmp_path, resources_data, job_plan_data):
        resources = [item for item in resources_data["resources"] if item["gateway"] == "jobv3-cloud"]
        release_resources("jobv3-cloud", "prod", resources)
        declarations_dir = tmp_path / "declarations"
        declarations_dir.mkdir()
        (declarations_dir / f"{JOB_PLAN}.yaml").write_text(
            yaml.safe_dump(job_plan_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        results = sync_platform_skills(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]
        assert results[0].warnings == []
        assert len(results[0].reasons) == 3
        assert all("已配置 OpenAPI 请求参数和响应参数" in reason for reason in results[0].reasons)
        assert not SkillMetadata.objects.exists()
