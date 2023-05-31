#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import json

import pytest
from ddf import G
from pydantic import BaseModel

from apigateway.apps.esb.bkcore import models
from apigateway.legacy_esb import models as legacy_models
from apigateway.legacy_esb import sync

pytestmark = pytest.mark.django_db


class TestDocCategorySynchronizer:
    @pytest.mark.parametrize(
        "mock_legacy_key_to_obj, mock_ng_key_to_obj, expected",
        [
            (
                {
                    1: legacy_models.SystemDocCategory(id=1, name="test"),
                    2: legacy_models.SystemDocCategory(id=2, name="test"),
                },
                {
                    1: models.DocCategory(id=1, name="test"),
                },
                True,
            ),
            (
                {
                    1: legacy_models.SystemDocCategory(id=1, name="test"),
                },
                {
                    1: models.DocCategory(id=1, name="test-new"),
                },
                False,
            ),
        ],
    )
    def test_pre_check_data(self, mocker, mock_legacy_key_to_obj, mock_ng_key_to_obj, expected):
        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategorySynchronizer._get_legacy_key_to_obj",
            return_value=mock_legacy_key_to_obj,
        )
        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategorySynchronizer._get_ng_key_to_obj",
            return_value=mock_ng_key_to_obj,
        )

        synchronizer = sync.DocCategorySynchronizer()
        result, _ = synchronizer.pre_check_data()
        assert result is expected

    def test_prepare_sync_data(self, mocker):
        legacy_category1 = G(legacy_models.SystemDocCategory)
        legacy_category2 = G(legacy_models.SystemDocCategory)
        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategorySynchronizer._get_legacy_key_to_obj",
            return_value={
                legacy_category1.id: legacy_category1,
                legacy_category2.id: legacy_category2,
            },
        )

        ng_category = models.DocCategory(id=legacy_category1.id)
        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategorySynchronizer._get_ng_key_to_obj",
            return_value={
                legacy_category1.id: ng_category,
            },
        )

        create_objs, update_objs = sync.DocCategorySynchronizer()._prepare_sync_data(True)
        assert len(create_objs) == 1
        assert len(update_objs) == 1
        assert create_objs[0].id == legacy_category2.id
        assert update_objs[0].id == legacy_category1.id

    def test_get_legacy_key_to_obj(self, mocker):
        legacy_category = G(legacy_models.SystemDocCategory)
        mocker.patch("apigateway.legacy_esb.sync.LegacyDocCategory.objects.all", return_value=[legacy_category])
        result = sync.DocCategorySynchronizer()._get_legacy_key_to_obj()
        assert result == {legacy_category.id: legacy_category}

    def test_get_ng_key_to_obj(self, mocker, unique_id):
        ng_category = G(models.DocCategory, name=unique_id)
        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategory.objects.all",
            return_value=[ng_category],
        )
        result = sync.DocCategorySynchronizer()._get_ng_key_to_obj()
        assert result == {ng_category.id: ng_category}

    def test_create_objs(self, unique_id):
        synchronizer = sync.DocCategorySynchronizer()
        assert synchronizer._create_objs([], dry_run=False) is None

        ng_categories = [models.DocCategory(name=unique_id)]
        assert synchronizer._create_objs(ng_categories, dry_run=True) is None
        assert models.DocCategory.objects.filter(name=unique_id).exists() is False

        assert synchronizer._create_objs(ng_categories, dry_run=False) is None
        assert models.DocCategory.objects.filter(name=unique_id).exists() is True

    def test_update_objs(self, unique_id):
        ng_categories = [G(models.DocCategory, name=unique_id)]
        synchronizer = sync.DocCategorySynchronizer()

        assert synchronizer._update_objs([], dry_run=False) is None

        assert synchronizer._update_objs(ng_categories, dry_run=True) is None
        assert models.DocCategory.objects.filter(name=unique_id).exists() is True

        assert synchronizer._update_objs(ng_categories, dry_run=False) is None
        assert models.DocCategory.objects.filter(name=unique_id).exists() is True

    def test_stringify_obj_fields(self):
        synchronizer = sync.DocCategorySynchronizer()

        category = models.DocCategory(id=1, name="test")
        assert synchronizer._stringify_obj_fields(category, ["id", "name"]) == "id=1, name=test"

    def test_assert_count_and_fields(self, mocker):
        legacy_category = legacy_models.SystemDocCategory(id=1, name="test")
        ng_category = models.DocCategory(id=1, name="test2")

        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategorySynchronizer._get_legacy_key_to_obj",
            return_value={legacy_category.id: legacy_category},
        )
        mocker.patch(
            "apigateway.legacy_esb.sync.DocCategorySynchronizer._get_ng_key_to_obj",
            return_value={ng_category.id: ng_category},
        )

        synchronizer = sync.DocCategorySynchronizer()
        assert synchronizer._assert_count_and_fields() is None

    @pytest.mark.parametrize(
        "src_obj, dst_obj, fields, expected",
        [
            (
                {"name": "n1", "address": "a1"},
                {"name": "n1", "address": "a1"},
                ["name", "address"],
                [],
            ),
            (
                {"name": "n1", "address": "a1"},
                {"name": "n2", "address": "a2"},
                ["name", "address"],
                ["name", "address"],
            ),
            (
                {"name": "n1", "address": "a1"},
                {"name": "n2", "address": "a2"},
                ["name"],
                ["name"],
            ),
        ],
    )
    def test_compare_field_value(self, src_obj, dst_obj, fields, expected):
        class Company(BaseModel):
            name: str = ""
            address: str = ""

        synchronizer = sync.DocCategorySynchronizer()
        assert synchronizer._compare_field_value(Company(**src_obj), Company(**dst_obj), fields) == expected


class TestSystemDocCategorySynchronizer:
    @pytest.fixture
    def fake_legacy_system_doc_category(self, faker, unique_id):
        return sync.SystemDocCategorySynchronizer.LegacySystemDocCategoryInnerMigrator(
            id=1,
            system_id=1,
            doc_category_id=1,
        )

    def test_clone_to_ng_obj(self, fake_legacy_system_doc_category):
        assert fake_legacy_system_doc_category.clone_to_ng_obj() == models.SystemDocCategory(
            id=fake_legacy_system_doc_category.id,
            system_id=fake_legacy_system_doc_category.system_id,
            doc_category_id=fake_legacy_system_doc_category.doc_category_id,
        )

    def test_update_ng_obj_fields(self, fake_legacy_system_doc_category):
        ng_system_doc_category = models.SystemDocCategory(id=1)
        result = fake_legacy_system_doc_category.update_ng_obj_fields(ng_system_doc_category)
        assert result == models.SystemDocCategory(
            id=fake_legacy_system_doc_category.id,
            system_id=fake_legacy_system_doc_category.system_id,
            doc_category_id=fake_legacy_system_doc_category.doc_category_id,
        )

    def test_is_changed(self, fake_legacy_system_doc_category):
        ng_obj = fake_legacy_system_doc_category.clone_to_ng_obj()
        assert fake_legacy_system_doc_category.is_changed(ng_obj) is False

        ng_obj.__dict__.update(
            {
                "doc_category_id": 2,
            }
        )
        assert fake_legacy_system_doc_category.is_changed(ng_obj) is True

    def test_get_legacy_key_to_obj(self, mocker):
        mocker.patch(
            "apigateway.legacy_esb.sync.LegacyComponentSystem.objects.values_list",
            return_value={1: 2},
        )
        mocker.patch(
            "apigateway.legacy_esb.sync.LegacyDocCategory.objects.values_list",
            return_value=[2],
        )

        synchronizer = sync.SystemDocCategorySynchronizer()
        assert synchronizer._get_legacy_key_to_obj() == {
            1: sync.SystemDocCategorySynchronizer.LegacySystemDocCategoryInnerMigrator(
                id=1,
                system_id=1,
                doc_category_id=2,
            )
        }


class TestESBChannelSynchronizer:
    def test_get_legacy_key_to_obj(self, mocker, unique_id):
        legacy_system = G(legacy_models.ComponentSystem)
        ng_system = models.ComponentSystem(id=legacy_system.id)
        legacy_channel = G(legacy_models.ESBChannel, component_system=legacy_system, path=unique_id)

        mocker.patch("apigateway.legacy_esb.sync.ComponentSystem.objects.all", return_value=[ng_system])
        mocker.patch("apigateway.legacy_esb.sync.LegacyESBChannel.objects.all", return_value=[legacy_channel])

        synchronizer = sync.ESBChannelSynchronizer()
        assert synchronizer._get_legacy_key_to_obj()[legacy_channel.id].ng_system == ng_system


class ComponentDocSynchronizer:
    @pytest.fixture
    def fake_component_doc(self, faker, unique_id):
        return sync.ComponentDocSynchronizer.LegacyComponentDocInnerMigrator(
            component_id=1,
            language="en",
            content="test",
            content_md5="a1e9bdcb475b92b59261b145f881015e",
        )

    def test_clone_to_ng_obj(self, fake_component_doc):
        assert fake_component_doc.clone_to_ng_obj() == models.ComponentDoc(
            component_id=fake_component_doc.component_id,
            language=fake_component_doc.language,
            content=fake_component_doc.content,
            content_md5=fake_component_doc.content_md5,
        )

    def test_update_ng_obj_fields(self, fake_component_doc):
        ng_component_doc = models.ComponentDoc(component_id=1)
        result = fake_component_doc.update_ng_obj_fields(ng_component_doc)
        assert result == models.ComponentDoc(
            component_id=fake_component_doc.component_id,
            language=fake_component_doc.language,
            content=fake_component_doc.content,
            content_md5=fake_component_doc.content_md5,
        )

    def test_is_changed(self, fake_component_doc):
        ng_obj = fake_component_doc.clone_to_ng_obj()
        assert fake_component_doc.is_changed(ng_obj) is False

        ng_obj.__dict__.update(
            {
                "content_md5": "test",
            }
        )
        assert fake_component_doc.is_changed(ng_obj) is True

    def test_get_legacy_key_to_obj(self, mocker, unique_id):
        legacy_channel = G(legacy_models.ESBChannel, path=unique_id)
        legacy_doc = G(
            legacy_models.ComponentAPIDoc,
            component_id=legacy_channel.id,
            doc_md=json.dumps(
                {
                    "zh-hans": "中文文档",
                    "en": "english document",
                }
            ),
        )

        mocker.patch(
            "apigateway.legacy_esb.sync.LegacyESBChannel.objects.values_list",
            return_value=[legacy_channel.id],
        )
        mocker.patch("apigateway.legacy_esb.sync.LegacyComponentDoc.objects.all", return_value=[legacy_doc])

        synchronizer = sync.ComponentDocSynchronizer()
        assert synchronizer._get_legacy_key_to_obj() == {
            f"{legacy_channel.id}:en": sync.ComponentDocSynchronizer.LegacyComponentDocInnerMigrator(
                component_id=legacy_channel.id,
                language="en",
                content="english document",
                content_md5="378807031f9afc4a23b176d617af2a81",
            ),
            f"{legacy_channel.id}:zh-hans": sync.ComponentDocSynchronizer.LegacyComponentDocInnerMigrator(
                component_id=legacy_channel.id,
                language="zh-hans",
                content="中文文档",
                content_md5="f6d3aaa4e3aa9cf7674f8a2331190d64",
            ),
        }

    def test_get_ng_key_to_obj(self, mocker):
        ng_doc = models.ComponentDoc(component_id=1, language="en")
        mocker.patch(
            "apigateway.legacy_esb.sync.ComponentDocSynchronizer.ComponentDoc.objects.all", return_value=[ng_doc]
        )

        synchronizer = sync.ComponentDocSynchronizer()
        assert synchronizer._get_ng_key_to_obj() == {
            "1:en": ng_doc,
        }
