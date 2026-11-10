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
from apigateway.tests.biz.skill.conftest import EXPECTED_DIR, release_fixture_gateway, write_snapshots

pytestmark = pytest.mark.django_db

JOB_PLAN = "job-plan-run-and-log"


@pytest.fixture
def sync_dirs(tmp_path, resources_data):
    """jobv3-cloud 已发布但没有 schema，参数和响应由补丁快照补齐"""
    resources = release_fixture_gateway(resources_data, "jobv3-cloud")
    return tmp_path / "declarations", write_snapshots(tmp_path / "resources", resources)


@pytest.fixture
def write_declaration(sync_dirs):
    declarations_dir = sync_dirs[0]
    declarations_dir.mkdir(exist_ok=True)

    def write(data, file_name=None):
        path = declarations_dir / f"{file_name or data['name']}.yaml"
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return path

    return write


def _sync(sync_dirs, **kwargs):
    return sync_platform_skills(*sync_dirs, **kwargs)


def _statuses(results):
    return [(result.name, result.status) for result in results]


class TestSyncPlatformSkills:
    def test_created(self, sync_dirs, write_declaration, job_plan_data):
        write_declaration(job_plan_data)

        results = _sync(sync_dirs)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.CREATED.value)]
        assert results[0].warnings == []
        metadata = SkillMetadata.objects.get(type=SkillTypeEnum.PLATFORM.value, gateway=None, name=JOB_PLAN)
        assert results[0].metadata_id == metadata.id
        assert metadata.current_version.artifact["SKILL.md"] == (EXPECTED_DIR / f"{JOB_PLAN}.md").read_text(
            encoding="utf-8"
        )

    def test_same_version_then_new_version(self, sync_dirs, write_declaration, job_plan_data):
        write_declaration(job_plan_data)
        _sync(sync_dirs)

        assert _statuses(_sync(sync_dirs)) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED_SAME_VERSION.value)]

        job_plan_data["version"] = "1.1.0"
        write_declaration(job_plan_data)
        results = _sync(sync_dirs)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.NEW_VERSION.value)]
        assert SkillVersion.objects.filter(metadata_id=results[0].metadata_id).count() == 2

    def test_lower_version_rejected(self, sync_dirs, write_declaration, job_plan_data):
        job_plan_data["version"] = "1.1.0"
        write_declaration(job_plan_data)
        _sync(sync_dirs)

        job_plan_data["version"] = "1.0.1"
        write_declaration(job_plan_data)
        results = _sync(sync_dirs)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.REJECTED.value)]
        assert results[0].reasons == [f"{JOB_PLAN} 的版本 1.0.1 不高于当前版本 1.1.0"]
        metadata = SkillMetadata.objects.get(name=JOB_PLAN)
        assert metadata.current_version.version == "1.1.0"
        assert metadata.versions.count() == 1

    def test_param_not_in_definition_rejected(self, sync_dirs, write_declaration, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["with"]["unknown"] = "${{ inputs.bk_scope_id }}"
        write_declaration(job_plan_data)

        results = _sync(sync_dirs)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.REJECTED.value)]
        assert results[0].reasons == ["run-plan：参数 unknown 不在资源定义中"]
        assert not SkillMetadata.objects.exists()

    def test_missing_resources(self, sync_dirs, write_declaration, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["uses"] = "jobv3-cloud/not_released@prod"
        write_declaration(job_plan_data)

        results = _sync(sync_dirs)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED_MISSING_RESOURCES.value)]
        assert "jobv3-cloud.not_released（环境 prod）在当前发布版本中不存在，下次部署重试" in results[0].reasons
        assert not SkillMetadata.objects.exists()

    def test_rejected_does_not_stop_others(self, sync_dirs, write_declaration, job_plan_data):
        write_declaration({"name": "Bad_Name"}, file_name="a-bad")
        outputs = job_plan_data["orchestration"]["outputs"]
        invalid_ref = {**job_plan_data, "name": "b-invalid-ref"}
        invalid_ref["orchestration"] = {
            **job_plan_data["orchestration"],
            "outputs": {"job_instance_id": {**outputs["job_instance_id"], "value": "${{ inputs.not_exists }}"}},
        }
        write_declaration(invalid_ref)
        write_declaration(job_plan_data)

        results = _sync(sync_dirs)

        assert _statuses(results) == [
            ("a-bad", SkillSyncStatusEnum.REJECTED.value),
            ("b-invalid-ref", SkillSyncStatusEnum.REJECTED.value),
            (JOB_PLAN, SkillSyncStatusEnum.CREATED.value),
        ]
        assert results[1].reasons == ["outputs.job_instance_id：输入 not_exists 不存在"]
        assert list(SkillMetadata.objects.values_list("name", flat=True)) == [JOB_PLAN]

    def test_failed_does_not_stop_others(self, mocker, sync_dirs, write_declaration, job_plan_data):
        write_declaration({**job_plan_data, "name": "a-first"})
        write_declaration(job_plan_data)

        def render(declaration, provider):
            if declaration.name == "a-first":
                raise RuntimeError("boom")
            return render_skill_body(declaration, provider)

        mocker.patch("apigateway.biz.skill.syncer.render_skill_body", side_effect=render)

        results = _sync(sync_dirs)

        assert _statuses(results) == [
            ("a-first", SkillSyncStatusEnum.FAILED.value),
            (JOB_PLAN, SkillSyncStatusEnum.CREATED.value),
        ]
        assert results[0].reasons == ["RuntimeError: boom"]

    def test_dry_run(self, sync_dirs, write_declaration, job_plan_data):
        write_declaration(job_plan_data)

        results = _sync(sync_dirs, dry_run=True)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.CREATED.value)]
        assert not SkillMetadata.objects.exists()

    def test_name_filter(self, sync_dirs, write_declaration, job_plan_data):
        write_declaration(job_plan_data)
        write_declaration({**job_plan_data, "name": "other-skill"})

        assert _statuses(_sync(sync_dirs, name="other-skill")) == [("other-skill", SkillSyncStatusEnum.CREATED.value)]

    def test_file_name_must_match_declaration_name(self, sync_dirs, write_declaration, job_plan_data):
        write_declaration(job_plan_data, file_name="other-file")

        results = _sync(sync_dirs)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.REJECTED.value)]
        assert results[0].reasons == ["文件名 other-file 与声明的 name job-plan-run-and-log 不一致"]
        assert not SkillMetadata.objects.exists()

    def test_no_schema_no_snapshot_rejected(self, tmp_path, resources_data, job_plan_data):
        release_fixture_gateway(resources_data, "jobv3-cloud")
        declarations_dir = tmp_path / "declarations"
        declarations_dir.mkdir()
        (declarations_dir / f"{JOB_PLAN}.yaml").write_text(
            yaml.safe_dump(job_plan_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        resources_dir = tmp_path / "resources"
        resources_dir.mkdir()

        results = sync_platform_skills(declarations_dir, resources_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.REJECTED.value)]
        assert results[0].warnings == []
        assert results[0].reasons == [
            "jobv3-cloud.execute_job_plan：资源无 schema、无快照，参数和响应字段无法核对",
            "jobv3-cloud.get_job_instance_status：资源无 schema、无快照，参数和响应字段无法核对",
            "jobv3-cloud.batch_get_job_instance_ip_log：资源无 schema、无快照，参数和响应字段无法核对",
        ]
        assert not SkillMetadata.objects.exists()
