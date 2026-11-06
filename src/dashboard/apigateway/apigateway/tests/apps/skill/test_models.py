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
from django.test.utils import CaptureQueriesContext
from django.utils.translation import override

from apigateway.apps.skill.constants import SKILL_MD_ARTIFACT_KEY, SkillStatusEnum, SkillTypeEnum
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
        code="p_job-plan-run-and-log",
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
        code=SkillMetadata.build_code(SkillTypeEnum.GATEWAY.value, fake_gateway.name, "task-status"),
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
        artifact={SKILL_MD_ARTIFACT_KEY: "# 执行作业方案并收集日志"},
    )


class TestSkillMetadata:
    @pytest.mark.parametrize(
        "type_, gateway_name, name, expected",
        [
            (SkillTypeEnum.PLATFORM.value, None, "job-plan-run-and-log", "p_job-plan-run-and-log"),
            (SkillTypeEnum.GATEWAY.value, "bk-sops", "task-status", "g_bk-sops_task-status"),
        ],
    )
    def test_build_code(self, type_, gateway_name, name, expected):
        assert SkillMetadata.build_code(type_, gateway_name, name) == expected

    def test_longest_code_fits_column(self):
        code = SkillMetadata.build_code(SkillTypeEnum.GATEWAY.value, "a" * 64, "b" * 64)

        assert len(code) <= SkillMetadata._meta.get_field("code").max_length

    def test_defaults(self):
        metadata = SkillMetadata.objects.create(
            type=SkillTypeEnum.PLATFORM.value,
            code="p_task-status",
            name="task-status",
            display_name="查任务状态",
            description="查询标准运维任务状态",
        )

        assert metadata.status == SkillStatusEnum.UNPUBLISHED.value
        assert metadata.current_version is None
        assert metadata.gateway is None
        assert metadata.download_count == 0
        assert metadata.display_name_en is None

    def test_display_name_i18n(self, fake_skill_metadata):
        with override("en"):
            assert fake_skill_metadata.display_name_i18n == "执行作业方案并收集日志"
            fake_skill_metadata.display_name_en = "Run JOB Plan and Collect Logs"
            assert fake_skill_metadata.display_name_i18n == "Run JOB Plan and Collect Logs"
        with override("zh-cn"):
            assert fake_skill_metadata.display_name_i18n == "执行作业方案并收集日志"

    def test_unique_code(self, fake_skill_metadata):
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillMetadata.objects.create(
                type=SkillTypeEnum.PLATFORM.value,
                code=fake_skill_metadata.code,
                name=fake_skill_metadata.name,
                display_name="执行作业方案",
                description="执行作业平台的作业执行方案",
            )

    def test_same_name_with_different_type(self, fake_skill_metadata, fake_gateway):
        other = G(
            SkillMetadata,
            type=SkillTypeEnum.GATEWAY.value,
            gateway=fake_gateway,
            code=SkillMetadata.build_code(SkillTypeEnum.GATEWAY.value, fake_gateway.name, fake_skill_metadata.name),
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
            code=SkillMetadata.build_code(
                SkillTypeEnum.GATEWAY.value, other_gateway.name, fake_gateway_skill_metadata.name
            ),
            name=fake_gateway_skill_metadata.name,
            current_version=None,
        )

        assert other.pk is not None
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillMetadata.objects.create(
                type=SkillTypeEnum.GATEWAY.value,
                gateway=fake_gateway_skill_metadata.gateway,
                code="g_another_task-status",
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

    def test_delete_current_version_set_null(self, fake_skill_metadata, fake_skill_version):
        fake_skill_metadata.current_version = fake_skill_version
        fake_skill_metadata.save()

        fake_skill_version.delete()

        fake_skill_metadata.refresh_from_db()
        assert fake_skill_metadata.current_version is None

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
        fake_skill_metadata.current_version = fake_skill_version
        fake_skill_metadata.save()

        fake_skill_metadata.delete()

        assert not SkillMetadata.objects.filter(pk=fake_skill_metadata.pk).exists()
        assert not SkillConfig.objects.filter(metadata_id=fake_skill_metadata.pk).exists()
        assert not SkillVersion.objects.filter(metadata_id=fake_skill_metadata.pk).exists()
        assert not SkillVersionRelation.objects.filter(metadata_id=fake_skill_metadata.pk).exists()
        assert not SkillMetadata.tags.through.objects.filter(skillmetadata_id=fake_skill_metadata.pk).exists()
        assert SkillTag.objects.filter(pk=tag.pk).exists()

    def test_delete_versions_before_metadata(self, fake_skill_metadata, fake_skill_version):
        # MySQL 立即检查外键，必须先删版本再删 metadata；SQLite 延迟检查，只能通过语句顺序验证
        fake_skill_metadata.current_version = fake_skill_version
        fake_skill_metadata.save()

        with CaptureQueriesContext(connection) as context:
            SkillMetadata.objects.filter(pk=fake_skill_metadata.pk).delete()

        deleted_tables = []
        for query in context.captured_queries:
            match = DELETE_TABLE_PATTERN.match(query["sql"])
            if match:
                deleted_tables.append(match.group(1))
        assert deleted_tables.index("skill_version") < deleted_tables.index("skill_metadata")

    def test_delete_gateway_cascade(self, fake_skill_metadata, fake_gateway_skill_metadata):
        version = G(SkillVersion, metadata=fake_gateway_skill_metadata, version="1.0.0")
        G(SkillConfig, metadata=fake_gateway_skill_metadata, orchestration={"steps": []})
        fake_gateway_skill_metadata.current_version = version
        fake_gateway_skill_metadata.save()

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

    def test_artifact_round_trip(self, fake_skill_version):
        artifact = {SKILL_MD_ARTIFACT_KEY: "# 执行作业方案并收集日志\n\n## 不适用场景\n\n无\n"}
        fake_skill_version.artifact = artifact
        fake_skill_version.save()

        fake_skill_version.refresh_from_db()
        assert fake_skill_version.artifact == artifact

    def test_unique_metadata_version(self, fake_skill_version):
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillVersion.objects.create(metadata=fake_skill_version.metadata, version=fake_skill_version.version)


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
        index_columns = [c["columns"] for c in constraints.values() if c["index"]]

        assert ["gateway_name", "resource_name"] in index_columns
        assert ["resource_name"] in index_columns

    def test_delete_version_cascade(self, fake_skill_version):
        G(
            SkillVersionRelation,
            metadata=fake_skill_version.metadata,
            version=fake_skill_version,
            gateway_name="jobv3-cloud",
            resource_name="execute_job_plan",
        )

        fake_skill_version.delete()

        assert not SkillVersionRelation.objects.filter(version_id=fake_skill_version.pk).exists()


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


def test_no_category_tables():
    table_names = connection.introspection.table_names()

    assert "skill_version_relation" in table_names
    assert "skill_category" not in table_names
    assert "skill_metadata_categories" not in table_names
