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
from django.db.models import F

from apigateway.apps.skill.constants import SkillStatusEnum, SkillTypeEnum
from apigateway.apps.skill.models import SkillConfig, SkillMetadata, SkillTag, SkillVersion, SkillVersionRelation
from apigateway.biz.skill.declaration import parse_declaration
from apigateway.biz.skill.writer import SkillVersionExistsError, SkillVersionNotNewerError, save_skill_version
from apigateway.tests.biz.skill.conftest import set_version

pytestmark = pytest.mark.django_db

OPERATOR = "admin"


def _save(data: dict, body: str = "# body\n", overwrite_existing: bool = False):
    return save_skill_version(
        parse_declaration(data),
        body,
        skill_type=SkillTypeEnum.PLATFORM.value,
        gateway=None,
        operator=OPERATOR,
        overwrite_existing=overwrite_existing,
    )


class TestSaveSkillVersion:
    def test_create(self, job_plan_data):
        saved = _save(job_plan_data)

        metadata = SkillMetadata.objects.get(id=saved.metadata.id)
        assert saved.created
        assert (metadata.type, metadata.gateway, metadata.name) == (
            SkillTypeEnum.PLATFORM.value,
            None,
            "job-plan-run-and-log",
        )
        assert metadata.display_name == job_plan_data["display_name"]
        assert metadata.display_name_en == job_plan_data["display_name_en"]
        assert metadata.status == SkillStatusEnum.PUBLISHED.value
        assert metadata.current_version_id == saved.version.id
        assert metadata.created_by == OPERATOR
        assert sorted(metadata.tags.values_list("name", flat=True)) == sorted(
            tag.strip().lower() for tag in job_plan_data["tags"]
        )

        assert saved.version.artifact == {"SKILL.md": "# body\n"}
        saved.version.refresh_from_db()
        assert saved.version.changelog == {
            "version": "1.0.0",
            "date": "2026-11-11 11:00:00",
            "content": "首个官方版本：execute_job_plan → get_job_instance_status → batch_get_job_instance_ip_log。",
        }
        assert saved.version.orchestration == parse_declaration(job_plan_data).orchestration_data()
        assert SkillConfig.objects.get(metadata=metadata).orchestration == saved.version.orchestration
        assert list(
            SkillVersionRelation.objects.filter(version=saved.version)
            .order_by("id")
            .values_list("gateway_name", "resource_name")
        ) == [
            ("jobv3-cloud", "execute_job_plan"),
            ("jobv3-cloud", "get_job_instance_status"),
            ("jobv3-cloud", "batch_get_job_instance_ip_log"),
        ]

    def test_new_version(self, job_plan_data):
        first = _save(job_plan_data)
        SkillMetadata.objects.filter(id=first.metadata.id).update(download_count=F("download_count") + 5)

        set_version(job_plan_data, "1.1.0-RC1").update(display_name="新名字", tags=["job"])
        second = _save(job_plan_data, body="# v2\n")

        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert not second.created
        assert second.metadata.id == first.metadata.id
        assert second.version.version == "1.1.0-rc1"
        assert second.version.changelog["version"] == "1.1.0-RC1"
        assert metadata.current_version_id == second.version.id
        assert metadata.display_name == "新名字"
        assert metadata.download_count == 5
        assert list(metadata.tags.values_list("name", flat=True)) == ["job"]
        assert SkillConfig.objects.filter(metadata=metadata).count() == 1
        assert metadata.versions.count() == 2

    def test_same_version(self, job_plan_data):
        _save(set_version(job_plan_data, "1.0.0-rc1"))
        set_version(job_plan_data, "1.0.0-RC1")

        with pytest.raises(SkillVersionExistsError):
            _save(job_plan_data)

    def test_overwrite_current_version(self, job_plan_data):
        first = _save(set_version(job_plan_data, "1.0.0-rc1"))
        SkillMetadata.objects.filter(id=first.metadata.id).update(download_count=F("download_count") + 5)
        created_time = first.version.created_time

        set_version(job_plan_data, "1.0.0-RC1").update(display_name="覆盖后的名字", tags=["job"])
        job_plan_data["orchestration"]["steps"] = job_plan_data["orchestration"]["steps"][:1]
        second = _save(job_plan_data, body="# overwritten\n", overwrite_existing=True)

        assert second.overwritten
        assert not second.created
        assert second.version.id == first.version.id
        version = SkillVersion.objects.get(id=first.version.id)
        assert version.version == "1.0.0-rc1"
        assert version.artifact == {"SKILL.md": "# overwritten\n"}
        assert version.changelog["content"] == "发布 1.0.0-RC1"
        assert version.created_time == created_time
        assert version.created_by == OPERATOR
        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert metadata.current_version_id == first.version.id
        assert metadata.display_name == "覆盖后的名字"
        assert metadata.download_count == 5
        assert list(metadata.tags.values_list("name", flat=True)) == ["job"]
        assert metadata.versions.count() == 1
        assert SkillConfig.objects.get(metadata=metadata).orchestration == version.orchestration
        assert list(SkillVersionRelation.objects.filter(version=version).values_list("resource_name", flat=True)) == [
            "execute_job_plan"
        ]

    def test_overwrite_does_not_replace_historical_version(self, job_plan_data):
        first = _save(job_plan_data)
        _save(set_version(job_plan_data, "1.1.0"), body="# v2\n")
        set_version(job_plan_data, "1.0.0")

        with pytest.raises(SkillVersionExistsError):
            _save(job_plan_data, body="# old\n", overwrite_existing=True)

        first.version.refresh_from_db()
        assert first.version.artifact == {"SKILL.md": "# body\n"}
        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert metadata.current_version.version == "1.1.0"
        assert metadata.versions.count() == 2

    @pytest.mark.parametrize("version", ["1.0.1", "1.1.0-rc1", "1.0.9+build"])
    def test_not_newer_than_current(self, job_plan_data, version):
        first = _save(set_version(job_plan_data, "1.1.0"))
        set_version(job_plan_data, version)

        with pytest.raises(SkillVersionNotNewerError):
            _save(job_plan_data)

        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert metadata.current_version_id == first.version.id
        assert metadata.versions.count() == 1

    def test_newer_by_numeric_order(self, job_plan_data):
        _save(set_version(job_plan_data, "1.9.0"))

        assert _save(set_version(job_plan_data, "1.10.0")).version.version == "1.10.0"

    def test_relations_deduplicated(self, job_plan_data):
        steps = job_plan_data["orchestration"]["steps"]
        steps.append({**steps[1], "id": "wait-again"})

        saved = _save(job_plan_data)

        assert sorted(
            SkillVersionRelation.objects.filter(version=saved.version).values_list("resource_name", flat=True)
        ) == [
            "batch_get_job_instance_ip_log",
            "execute_job_plan",
            "get_job_instance_status",
        ]

    def test_rollback(self, mocker, job_plan_data):
        mocker.patch.object(SkillVersionRelation.objects, "bulk_create", side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError):
            _save(job_plan_data)

        assert not SkillMetadata.objects.exists()
        assert not SkillTag.objects.exists()
        assert not SkillConfig.objects.exists()

    def test_tags_reused(self, job_plan_data):
        other = copy.deepcopy(job_plan_data)
        other["name"] = "job-plan-copy"
        other["tags"] = ["运维"]
        job_plan_data["tags"] = ["运维", "Job"]

        _save(job_plan_data)
        _save(other)

        assert SkillTag.objects.filter(name="运维").count() == 1
