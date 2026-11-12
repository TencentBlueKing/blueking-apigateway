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
import logging

import pytest
import yaml

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion, SkillVersionRelation
from apigateway.biz.skill import SkillSyncStatusEnum, sync_platform_skills
from apigateway.biz.skill.renderer import render_skill_body
from apigateway.tests.biz.skill.conftest import release_fixture_gateway, release_resources, set_version

pytestmark = pytest.mark.django_db

JOB_PLAN = "job-plan-run-and-log"
SYNCER_LOGGER = "apigateway.biz.skill.syncer"


TE_GATEWAY_NAMES = {"jobv3-cloud": "jobv3-cloud", "bk-job": "jobv3-cloud"}
EE_GATEWAY_NAMES = {"jobv3-cloud": "bk-job", "bk-job": "bk-job"}


@pytest.fixture(autouse=True)
def te_edition(settings):
    """fixture 资源和声明用的是内部名 jobv3-cloud"""
    settings.EDITION_GATEWAY_NAMES = TE_GATEWAY_NAMES


def _rename_gateway(resources_data, old, new):
    return {
        **resources_data,
        "resources": [
            {**item, "gateway": new} if item["gateway"] == old else item for item in resources_data["resources"]
        ],
    }


def _use_gateway(data, gateway):
    for step in data["orchestration"]["steps"]:
        step["uses"] = f"{gateway}/{step['uses'].split('/', 1)[1]}"
    data["tags"] = [gateway if tag == "jobv3-cloud" else tag for tag in data["tags"]]
    return data


def _relation_gateways(metadata_id):
    return set(SkillVersionRelation.objects.filter(metadata_id=metadata_id).values_list("gateway_name", flat=True))


def _tag_names(metadata_id):
    return list(SkillMetadata.objects.get(id=metadata_id).tags.order_by("id").values_list("name", flat=True))


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


def _syncer_logs(caplog):
    return [(record.levelname, record.getMessage()) for record in caplog.records if record.name == SYNCER_LOGGER]


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

        write_declaration(set_version(job_plan_data, "1.1.0"))
        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.RELEASED.value)]
        assert SkillVersion.objects.filter(metadata_id=results[0].metadata_id).count() == 2

    def test_lower_version_rejected(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(set_version(job_plan_data, "1.1.0"))
        _sync(declarations_dir)

        write_declaration(set_version(job_plan_data, "1.0.1"))
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

        reason = "jobv3-cloud.not_released（环境 prod）不可编排：当前发布版本中没有资源 not_released"
        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.SKIPPED.value)]
        assert results[0].reasons == [reason]
        assert f"skip platform skill {JOB_PLAN}: {reason}" in caplog.text
        assert not SkillMetadata.objects.exists()

    def test_skip_reasons_logged(self, caplog, declarations_dir, write_declaration, job_plan_data):
        job_plan_data["orchestration"]["steps"][0]["with"]["unknown"] = "${{ inputs.bk_scope_id }}"
        write_declaration(job_plan_data)

        _sync(declarations_dir)

        assert _syncer_logs(caplog) == [
            ("WARNING", f"skip platform skill {JOB_PLAN}: run-plan：参数 unknown 不在资源定义中")
        ]

    def test_version_exists_logged_as_info(self, caplog, declarations_dir, write_declaration, job_plan_data):
        caplog.set_level(logging.INFO, logger=SYNCER_LOGGER)
        write_declaration(job_plan_data)
        _sync(declarations_dir)
        caplog.clear()

        _sync(declarations_dir)

        assert _syncer_logs(caplog) == [("INFO", f"skip platform skill {JOB_PLAN}: 版本 1.0.0 已存在")]

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

    def test_ee_localizes_internal_gateway_name(self, settings, tmp_path, resources_data, job_plan_data):
        settings.EDITION_GATEWAY_NAMES = EE_GATEWAY_NAMES
        release_fixture_gateway(_rename_gateway(resources_data, "jobv3-cloud", "bk-job"), "bk-job")
        declarations_dir = tmp_path / "declarations"
        declarations_dir.mkdir()
        (declarations_dir / f"{JOB_PLAN}.yaml").write_text(
            yaml.safe_dump(job_plan_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        results = sync_platform_skills(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.CREATED.value)]
        assert _relation_gateways(results[0].metadata_id) == {"bk-job"}
        assert "bk-job" in _tag_names(results[0].metadata_id)
        assert "jobv3-cloud" not in _tag_names(results[0].metadata_id)

    def test_te_localizes_external_gateway_name(self, declarations_dir, write_declaration, job_plan_data):
        write_declaration(_use_gateway(job_plan_data, "bk-job"))

        results = _sync(declarations_dir)

        assert _statuses(results) == [(JOB_PLAN, SkillSyncStatusEnum.CREATED.value)]
        assert _relation_gateways(results[0].metadata_id) == {"jobv3-cloud"}
        assert "jobv3-cloud" in _tag_names(results[0].metadata_id)
        assert "bk-job" not in _tag_names(results[0].metadata_id)

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
        assert results[0].reasons == [
            f"jobv3-cloud.{name}（环境 prod）不可编排：OpenAPI schema 未定义请求参数; OpenAPI schema 的响应未定义字段"
            for name in ("execute_job_plan", "get_job_instance_status", "batch_get_job_instance_ip_log")
        ]
        assert not SkillMetadata.objects.exists()
