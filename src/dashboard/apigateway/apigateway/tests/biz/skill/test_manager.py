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
import datetime

import pytest
from ddf import G

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import (
    SkillConfig,
    SkillMetadata,
    SkillTag,
    SkillVersion,
    SkillVersionRelation,
)
from apigateway.biz.skill.manager import delete_skill, set_current_version, set_skill_status, update_skill_basic_info
from apigateway.biz.skill.package import build_skill_package_files
from apigateway.common.error_codes import APIError
from apigateway.core.models import Gateway
from apigateway.tests.biz.skill.conftest import create_skill

pytestmark = pytest.mark.django_db

OLD_TIME = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


@pytest.fixture
def metadata():
    gateway = G(Gateway, name="demo")
    create_skill("release-check", gateway=gateway, version="1.0.0", operator="alice")
    metadata = create_skill("release-check", gateway=gateway, version="1.1.0", operator="alice")
    SkillMetadata.objects.filter(id=metadata.id).update(updated_time=OLD_TIME, download_count=5)
    return SkillMetadata.objects.select_related("gateway", "current_version").get(id=metadata.id)


def _reload(metadata):
    return SkillMetadata.objects.select_related("current_version").get(id=metadata.id)


class TestUpdateSkillBasicInfo:
    def test_update(self, metadata):
        version_count = SkillVersion.objects.count()

        update_skill_basic_info(metadata, "发布核对", "", "新的描述", ["只读", " JOB "], operator="bob")

        metadata = _reload(metadata)
        assert metadata.display_name == "发布核对"
        assert metadata.display_name_en is None
        assert metadata.description == "新的描述"
        assert sorted(tag.name for tag in metadata.tags.all()) == ["job", "只读"]
        assert metadata.updated_by == "bob"
        assert metadata.updated_time > OLD_TIME
        assert metadata.download_count == 5
        assert SkillVersion.objects.count() == version_count
        files = build_skill_package_files(metadata, metadata.current_version)
        assert "display_name: 发布核对" in files[0][1]
        assert "\n# 发布核对\n" in files[0][1]

    def test_archived(self, metadata):
        metadata.status = SkillStatusEnum.ARCHIVED.value
        with pytest.raises(APIError, match="FAILED_PRECONDITION"):
            update_skill_basic_info(metadata, "x", None, "x", ["x"], operator="bob")


class TestSetCurrentVersion:
    def test_switch(self, metadata):
        old = metadata.versions.get(version="1.0.0")
        created_time = old.created_time

        set_current_version(metadata, old, operator="bob")

        metadata = _reload(metadata)
        assert metadata.current_version_id == old.id
        assert metadata.current_version.created_time == created_time
        assert metadata.updated_by == "bob"
        assert metadata.updated_time > OLD_TIME

    def test_archived(self, metadata):
        metadata.status = SkillStatusEnum.ARCHIVED.value
        with pytest.raises(APIError, match="FAILED_PRECONDITION"):
            set_current_version(metadata, metadata.current_version, operator="bob")


class TestSetSkillStatus:
    def test_archive_and_restore(self, metadata):
        set_skill_status(metadata, SkillStatusEnum.ARCHIVED.value, operator="bob")
        metadata = _reload(metadata)
        assert metadata.status == SkillStatusEnum.ARCHIVED.value
        assert metadata.updated_by == "bob"
        assert metadata.updated_time > OLD_TIME

        set_skill_status(metadata, SkillStatusEnum.PUBLISHED.value, operator="carol")
        assert _reload(metadata).status == SkillStatusEnum.PUBLISHED.value


class TestDeleteSkill:
    def test_not_archived(self, metadata):
        with pytest.raises(APIError, match="FAILED_PRECONDITION"):
            delete_skill(metadata)

    def test_delete(self, metadata):
        metadata_id = metadata.id
        tag_ids = list(metadata.tags.values_list("id", flat=True))
        set_skill_status(metadata, SkillStatusEnum.ARCHIVED.value, operator="bob")

        delete_skill(metadata)

        assert not SkillMetadata.objects.filter(id=metadata_id).exists()
        assert not SkillVersion.objects.filter(metadata_id=metadata_id).exists()
        assert not SkillConfig.objects.filter(metadata_id=metadata_id).exists()
        assert not SkillVersionRelation.objects.filter(metadata_id=metadata_id).exists()
        assert not SkillMetadata.tags.through.objects.filter(skillmetadata_id=metadata_id).exists()
        assert SkillTag.objects.filter(id__in=tag_ids).count() == len(tag_ids)
