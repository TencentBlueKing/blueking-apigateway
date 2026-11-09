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
import re

import pytest
from ddf import G
from django.db import IntegrityError, connection, transaction
from django.db.models import F
from django.db.models.deletion import ProtectedError
from django.test.utils import CaptureQueriesContext
from django.utils.translation import override

from apigateway.apps.skill.constants import SkillStatusEnum, SkillTypeEnum
from apigateway.apps.skill.models import (
    SkillConfig,
    SkillMetadata,
    SkillTag,
    SkillVersion,
    SkillVersionRelation,
)
from apigateway.core.models import Gateway

DELETE_TABLE_PATTERN = re.compile(r'^DELETE FROM [`"](\w+)[`"]')


@pytest.fixture
def fake_skill_metadata():
    return G(
        SkillMetadata,
        type=SkillTypeEnum.PLATFORM.value,
        name="job-plan-run-and-log",
        display_name="执行作业方案并收集日志",
        display_name_en=None,
        description="执行作业平台的作业执行方案并跟踪到结束",
        gateway=None,
        current_version=None,
    )


@pytest.fixture
def fake_gateway_skill_metadata(fake_gateway):
    return G(
        SkillMetadata,
        type=SkillTypeEnum.GATEWAY.value,
        gateway=fake_gateway,
        name="task-status",
        current_version=None,
    )


@pytest.fixture
def fake_skill_version(fake_skill_metadata):
    return G(
        SkillVersion,
        metadata=fake_skill_metadata,
        version="1.0.0",
        orchestration={"steps": []},
        artifact={"SKILL.md": "# 执行作业方案并收集日志"},
    )


class TestSkillMetadata:
    @pytest.mark.parametrize(
        "type_, gateway_name, name, expected",
        [
            (SkillTypeEnum.PLATFORM.value, None, "job-plan-run-and-log", "p_job-plan-run-and-log"),
            (SkillTypeEnum.GATEWAY.value, "bk-sops", "task-status", "g_bk-sops_task-status"),
        ],
    )
    def test_code(self, type_, gateway_name, name, expected):
        gateway = Gateway(name=gateway_name) if gateway_name else None
        metadata = SkillMetadata(type=type_, gateway=gateway, name=name)

        assert metadata.code == expected

    def test_defaults(self):
        metadata = SkillMetadata.objects.create(
            type=SkillTypeEnum.PLATFORM.value,
            name="task-status",
            display_name="查任务状态",
            description="查询标准运维任务状态",
        )

        assert metadata.status == SkillStatusEnum.UNPUBLISHED.value
        assert metadata.current_version is None
        assert metadata.gateway is None
        assert metadata.download_count == 0
        assert metadata.display_name_en is None
        assert metadata.metadata == {}

    def test_metadata_round_trip(self, fake_skill_metadata):
        metadata = {
            "custom_key": "custom_value",
            "labels": ["official", "recommended"],
            "options": {"enabled": True},
        }
        fake_skill_metadata.metadata = metadata
        fake_skill_metadata.save()

        fake_skill_metadata.refresh_from_db()
        assert fake_skill_metadata.metadata == metadata

    def test_display_name_i18n(self, fake_skill_metadata):
        with override("en"):
            assert fake_skill_metadata.display_name_i18n == "执行作业方案并收集日志"
            fake_skill_metadata.display_name_en = "Run JOB Plan and Collect Logs"
            assert fake_skill_metadata.display_name_i18n == "Run JOB Plan and Collect Logs"
        with override("zh-cn"):
            assert fake_skill_metadata.display_name_i18n == "执行作业方案并收集日志"

    def test_same_name_with_different_type(self, fake_skill_metadata, fake_gateway):
        other = G(
            SkillMetadata,
            type=SkillTypeEnum.GATEWAY.value,
            gateway=fake_gateway,
            name=fake_skill_metadata.name,
            current_version=None,
        )

        assert other.pk != fake_skill_metadata.pk

    def test_gateway_skill_unique_within_gateway(self, fake_gateway_skill_metadata):
        other_gateway = G(Gateway, name="bk-job-skill-test")
        other = G(
            SkillMetadata,
            type=SkillTypeEnum.GATEWAY.value,
            gateway=other_gateway,
            name=fake_gateway_skill_metadata.name,
            current_version=None,
        )

        assert other.pk is not None
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillMetadata.objects.create(
                type=SkillTypeEnum.GATEWAY.value,
                gateway=fake_gateway_skill_metadata.gateway,
                name=fake_gateway_skill_metadata.name,
                display_name="查任务状态",
                description="查询标准运维任务状态",
            )

    def test_increase_download_count_keeps_updated_time(self, fake_skill_metadata):
        updated_time = fake_skill_metadata.updated_time

        SkillMetadata.objects.filter(pk=fake_skill_metadata.pk).update(download_count=F("download_count") + 1)

        fake_skill_metadata.refresh_from_db()
        assert fake_skill_metadata.download_count == 1
        assert fake_skill_metadata.updated_time == updated_time

    def test_delete_referenced_version_protected(self, fake_skill_metadata, fake_skill_version):
        fake_skill_metadata.current_version = fake_skill_version
        fake_skill_metadata.save()

        with pytest.raises(ProtectedError), transaction.atomic():
            fake_skill_version.delete()

        fake_skill_metadata.refresh_from_db()
        assert fake_skill_metadata.current_version_id == fake_skill_version.pk
        assert SkillVersion.objects.filter(pk=fake_skill_version.pk).exists()

    def test_delete_metadata_with_current_version_protected(self, fake_skill_metadata, fake_skill_version):
        fake_skill_metadata.current_version = fake_skill_version
        fake_skill_metadata.save()

        with pytest.raises(ProtectedError), transaction.atomic():
            fake_skill_metadata.delete()

        assert SkillMetadata.objects.filter(pk=fake_skill_metadata.pk).exists()
        assert SkillVersion.objects.filter(pk=fake_skill_version.pk).exists()

    def test_delete_version_after_clearing_reference(self, fake_skill_metadata, fake_skill_version):
        newer = G(SkillVersion, metadata=fake_skill_metadata, version="1.1.0")
        fake_skill_metadata.current_version = newer
        fake_skill_metadata.save()
        # delete() 会把实例 pk 置为 None，需提前保存
        version_id = fake_skill_version.pk

        fake_skill_version.delete()

        fake_skill_metadata.refresh_from_db()
        assert fake_skill_metadata.current_version_id == newer.pk
        assert not SkillVersion.objects.filter(pk=version_id).exists()

    def test_delete_cascade(self, fake_skill_metadata, fake_skill_version):
        G(SkillConfig, metadata=fake_skill_metadata, orchestration={"steps": []})
        G(
            SkillVersionRelation,
            metadata=fake_skill_metadata,
            version=fake_skill_version,
            gateway_name="jobv3-cloud",
            resource_name="execute_job_plan",
        )
        tag = G(SkillTag, name="作业运维")
        fake_skill_metadata.tags.add(tag)
        # delete() 会把实例 pk 置为 None，需提前保存
        metadata_id = fake_skill_metadata.pk

        fake_skill_metadata.delete()

        assert not SkillMetadata.objects.filter(pk=metadata_id).exists()
        assert not SkillConfig.objects.filter(metadata_id=metadata_id).exists()
        assert not SkillVersion.objects.filter(metadata_id=metadata_id).exists()
        assert not SkillVersionRelation.objects.filter(metadata_id=metadata_id).exists()
        assert not SkillMetadata.tags.through.objects.filter(skillmetadata_id=metadata_id).exists()
        assert SkillTag.objects.filter(pk=tag.pk).exists()

    def test_delete_versions_before_metadata(self, fake_skill_metadata, fake_skill_version):
        # MySQL 立即检查外键，必须先删版本再删 metadata；SQLite 延迟检查，只能通过语句顺序验证
        with CaptureQueriesContext(connection) as context:
            SkillMetadata.objects.filter(pk=fake_skill_metadata.pk).delete()

        statements = []
        for query in context.captured_queries:
            match = DELETE_TABLE_PATTERN.match(query["sql"])
            if match:
                statements.append(match.group(1))
        assert statements.index("skill_version") < statements.index("skill_metadata")

    def test_delete_gateway_with_current_version_protected(self, fake_gateway_skill_metadata):
        version = G(SkillVersion, metadata=fake_gateway_skill_metadata, version="1.0.0")
        fake_gateway_skill_metadata.current_version = version
        fake_gateway_skill_metadata.save()

        with pytest.raises(ProtectedError), transaction.atomic():
            fake_gateway_skill_metadata.gateway.delete()

        assert SkillMetadata.objects.filter(pk=fake_gateway_skill_metadata.pk).exists()

    def test_delete_gateway_cascade(self, fake_skill_metadata, fake_gateway_skill_metadata):
        version = G(SkillVersion, metadata=fake_gateway_skill_metadata, version="1.0.0")
        G(SkillConfig, metadata=fake_gateway_skill_metadata, orchestration={"steps": []})

        fake_gateway_skill_metadata.gateway.delete()

        assert not SkillMetadata.objects.filter(pk=fake_gateway_skill_metadata.pk).exists()
        assert not SkillConfig.objects.filter(metadata_id=fake_gateway_skill_metadata.pk).exists()
        assert not SkillVersion.objects.filter(pk=version.pk).exists()
        assert SkillMetadata.objects.filter(pk=fake_skill_metadata.pk).exists()


class TestSkillVersion:
    def test_defaults(self, fake_skill_metadata):
        version = SkillVersion.objects.create(metadata=fake_skill_metadata, version="1.0.0")

        assert version.changelog == ""
        assert version.orchestration == {}
        assert version.artifact == {}

    def test_artifact_round_trip(self, fake_skill_metadata):
        artifact = {"SKILL.md": "# 执行作业方案并收集日志\n\n## 不适用场景\n\n无\n"}
        version = SkillVersion.objects.create(metadata=fake_skill_metadata, version="1.0.0", artifact=artifact)

        version.refresh_from_db()
        assert version.artifact == artifact

    def test_unique_metadata_version(self, fake_skill_version):
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillVersion.objects.create(metadata=fake_skill_version.metadata, version=fake_skill_version.version)

    def test_version_saved_as_lowercase(self, fake_skill_metadata):
        version = SkillVersion.objects.create(metadata=fake_skill_metadata, version="1.0.0-Alpha")

        version.refresh_from_db()
        assert version.version == "1.0.0-alpha"
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillVersion.objects.create(metadata=fake_skill_metadata, version="1.0.0-ALPHA")


class TestSkillVersionRelation:
    def test_unique_version_gateway_resource(self, fake_skill_version):
        G(
            SkillVersionRelation,
            metadata=fake_skill_version.metadata,
            version=fake_skill_version,
            gateway_name="jobv3-cloud",
            resource_name="execute_job_plan",
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            SkillVersionRelation.objects.create(
                metadata=fake_skill_version.metadata,
                version=fake_skill_version,
                gateway_name="jobv3-cloud",
                resource_name="execute_job_plan",
            )

    def test_indexes(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, "skill_version_relation")
        unique_columns = [c["columns"] for c in constraints.values() if c["unique"]]
        non_unique_index_columns = [c["columns"] for c in constraints.values() if c["index"] and not c["unique"]]

        assert ["gateway_name", "resource_name", "version_id"] in unique_columns
        assert ["resource_name"] in non_unique_index_columns
        assert ["gateway_name", "resource_name"] not in non_unique_index_columns

    def test_delete_version_cascade(self, fake_skill_version):
        G(
            SkillVersionRelation,
            metadata=fake_skill_version.metadata,
            version=fake_skill_version,
            gateway_name="jobv3-cloud",
            resource_name="execute_job_plan",
        )
        # delete() 会把实例 pk 置为 None，需提前保存
        version_id = fake_skill_version.pk

        fake_skill_version.delete()

        assert not SkillVersionRelation.objects.filter(version_id=version_id).exists()


class TestSkillTag:
    def test_unique_name(self):
        G(SkillTag, name="作业运维")

        with pytest.raises(IntegrityError), transaction.atomic():
            SkillTag.objects.create(name="作业运维")

    def test_metadata_tags_table(self):
        assert SkillMetadata.tags.through._meta.db_table == "skill_metadata_tags"

    def test_unique_metadata_tag(self, fake_skill_metadata):
        tag = G(SkillTag, name="作业运维")
        fake_skill_metadata.tags.add(tag)

        with pytest.raises(IntegrityError), transaction.atomic():
            SkillMetadata.tags.through.objects.create(skillmetadata=fake_skill_metadata, skilltag=tag)
