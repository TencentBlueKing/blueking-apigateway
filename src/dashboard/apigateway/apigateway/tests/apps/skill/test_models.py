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
        code="job-plan-run-and-log",
        name="执行作业方案并收集日志",
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
        code="task-status",
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
    def test_skill_id(self, fake_skill_metadata):
        assert fake_skill_metadata.skill_id == "p_job-plan-run-and-log"

    def test_gateway_skill_id(self, fake_gateway_skill_metadata):
        assert fake_gateway_skill_metadata.skill_id == f"g_{fake_gateway_skill_metadata.gateway.name}_task-status"

    def test_skill_id_is_not_column(self):
        with connection.cursor() as cursor:
            columns = [c.name for c in connection.introspection.get_table_description(cursor, "skill_metadata")]

        assert "skill_id" not in columns

    def test_defaults(self, fake_skill_metadata):
        assert fake_skill_metadata.status == SkillStatusEnum.UNPUBLISHED.value
        assert fake_skill_metadata.current_version is None
        assert fake_skill_metadata.gateway is None
        assert fake_skill_metadata.download_count == 0

    def test_same_code_with_different_type(self, fake_skill_metadata, fake_gateway):
        other = G(
            SkillMetadata,
            type=SkillTypeEnum.GATEWAY.value,
            gateway=fake_gateway,
            code=fake_skill_metadata.code,
            current_version=None,
        )

        assert other.pk != fake_skill_metadata.pk

    def test_gateway_skill_unique_within_gateway(self, fake_gateway_skill_metadata):
        other_gateway = G(Gateway, name="bk-job-skill-test")
        other = G(
            SkillMetadata,
            type=SkillTypeEnum.GATEWAY.value,
            gateway=other_gateway,
            code=fake_gateway_skill_metadata.code,
            current_version=None,
        )

        assert other.pk is not None
        with pytest.raises(IntegrityError), transaction.atomic():
            SkillMetadata.objects.create(
                type=SkillTypeEnum.GATEWAY.value,
                gateway=fake_gateway_skill_metadata.gateway,
                code=fake_gateway_skill_metadata.code,
                name="查任务状态",
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
