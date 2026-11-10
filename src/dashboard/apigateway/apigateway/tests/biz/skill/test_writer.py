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
from apigateway.apps.skill.models import SkillConfig, SkillMetadata, SkillTag, SkillVersionRelation
from apigateway.biz.skill.declaration import parse_declaration
from apigateway.biz.skill.writer import SkillVersionExistsError, SkillVersionNotNewerError, save_skill_version

pytestmark = pytest.mark.django_db

OPERATOR = "admin"


def _save(data: dict, body: str = "# body\n"):
    return save_skill_version(
        parse_declaration(data), body, skill_type=SkillTypeEnum.PLATFORM.value, gateway=None, operator=OPERATOR
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

        job_plan_data.update(version="1.1.0-RC1", display_name="新名字", tags=["job"])
        second = _save(job_plan_data, body="# v2\n")

        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert not second.created
        assert second.metadata.id == first.metadata.id
        assert second.version.version == "1.1.0-rc1"
        assert metadata.current_version_id == second.version.id
        assert metadata.display_name == "新名字"
        assert metadata.download_count == 5
        assert list(metadata.tags.values_list("name", flat=True)) == ["job"]
        assert SkillConfig.objects.filter(metadata=metadata).count() == 1
        assert metadata.versions.count() == 2

    def test_same_version(self, job_plan_data):
        _save(job_plan_data)
        job_plan_data["version"] = job_plan_data["version"].upper()

        with pytest.raises(SkillVersionExistsError):
            _save(job_plan_data)

    @pytest.mark.parametrize("version", ["1.0.1", "1.1.0-rc1", "1.0.9+build"])
    def test_not_newer_than_current(self, job_plan_data, version):
        job_plan_data["version"] = "1.1.0"
        first = _save(job_plan_data)
        job_plan_data["version"] = version

        with pytest.raises(SkillVersionNotNewerError):
            _save(job_plan_data)

        metadata = SkillMetadata.objects.get(id=first.metadata.id)
        assert metadata.current_version_id == first.version.id
        assert metadata.versions.count() == 1

    def test_newer_by_numeric_order(self, job_plan_data):
        job_plan_data["version"] = "1.9.0"
        _save(job_plan_data)
        job_plan_data["version"] = "1.10.0"

        assert _save(job_plan_data).version.version == "1.10.0"

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
