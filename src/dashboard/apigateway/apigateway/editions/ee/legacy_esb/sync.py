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
"""将 PaaS2/ESB 数据迁移至 BK-ESB"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from django.db import models
from pydantic import BaseModel

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    ComponentDoc,
    ComponentSystem,
    DocCategory,
    ESBChannel,
    SystemDocCategory,
)
from apigateway.legacy_esb.models import AppComponentPerm as LegacyAppComponentPermission
from apigateway.legacy_esb.models import ComponentAPIDoc as LegacyComponentDoc
from apigateway.legacy_esb.models import ComponentSystem as LegacyComponentSystem
from apigateway.legacy_esb.models import ESBChannel as LegacyESBChannel
from apigateway.legacy_esb.models import LegacyModelMigrator
from apigateway.legacy_esb.models import SystemDocCategory as LegacyDocCategory

logger = logging.getLogger(__name__)

_BULK_CREATE_BATCH_SIZE = 50


class BaseSynchronizer:
    legacy_model: Optional[models.Model]
    ng_model: models.Model
    default_display_fields: List[str]
    pre_check_fields: List[str]
    assert_fields: List[str]

    def sync_legacy_to_ng(self, dry_run: bool, force: bool):
        create_ng_objs, update_ng_objs = self._prepare_sync_data(force)
        self._save_objs(create_ng_objs, update_ng_objs, dry_run)

    def assert_data(self):
        self._assert_count_and_fields()

    def pre_check_data(self) -> Tuple[bool, str]:
        """预检数据，如果预检失败，则不能执行数据同步操作"""
        legacy_key_to_obj = self._get_legacy_key_to_obj()
        ng_key_to_obj = self._get_ng_key_to_obj()

        for l_key, l_obj in legacy_key_to_obj.items():
            ng_obj = ng_key_to_obj.pop(l_key, None)
            if not ng_obj:
                continue

            different_fields = self._compare_field_value(l_obj, ng_obj, self.pre_check_fields)
            if different_fields:
                message = "%s[id/key=%s] has different fields, legacy: %s, ng: %s" % (
                    self.ng_model.__name__,
                    l_key,
                    self._stringify_obj_fields(l_obj, different_fields),
                    self._stringify_obj_fields(ng_obj, different_fields),
                )
                return False, message

        return True, ""

    def _prepare_sync_data(self, force: bool) -> Tuple[List[models.Model], List[models.Model]]:
        create_objs = []
        update_objs = []

        ng_key_to_obj = self._get_ng_key_to_obj()
        for l_obj_key, l_obj in self._get_legacy_key_to_obj().items():
            ng_obj = ng_key_to_obj.pop(l_obj_key, None)
            if not ng_obj:
                ng_obj = l_obj.clone_to_ng_obj()
                create_objs.append(ng_obj)
                continue

            if force or l_obj.is_changed(ng_obj):
                ng_obj = l_obj.update_ng_obj_fields(ng_obj)
                update_objs.append(ng_obj)

        return create_objs, update_objs

    def _get_legacy_key_to_obj(self) -> Dict[Union[str, int], LegacyModelMigrator]:
        if not self.legacy_model:
            raise ValueError("legacy_model can not be empty")
        return {obj.id: obj for obj in self.legacy_model.objects.all()}

    def _get_ng_key_to_obj(self) -> Dict[Union[str, int], models.Model]:
        return {obj.id: obj for obj in self.ng_model.objects.all()}

    def _save_objs(self, create_objs: List[models.Model], update_objs: List[models.Model], dry_run: bool):
        self._create_objs(create_objs, dry_run)
        self._update_objs(update_objs, dry_run)

    def _create_objs(self, objs: List[models.Model], dry_run: bool):
        if not objs:
            return

        if not dry_run:
            self.ng_model.objects.bulk_create(objs, batch_size=_BULK_CREATE_BATCH_SIZE)
            return

        for obj in objs:
            logger.info(
                "add %s: %s",
                self.ng_model.__name__,
                self._stringify_obj_fields(obj, self.default_display_fields),
            )

    def _update_objs(self, objs: List[models.Model], dry_run: bool):
        if not objs:
            return

        if not dry_run:
            for obj in objs:
                obj.save()
            return

        for obj in objs:
            logger.info(
                "update %s: %s",
                self.ng_model.__name__,
                self._stringify_obj_fields(obj, self.default_display_fields),
            )

    def _stringify_obj_fields(self, obj: Any, fields: List[str]) -> str:
        return ", ".join([f"{field}={getattr(obj, field)}" for field in fields])

    def _assert_count_and_fields(self):
        legacy_key_to_obj = self._get_legacy_key_to_obj()
        ng_key_to_obj = self._get_ng_key_to_obj()

        if len(legacy_key_to_obj) != len(ng_key_to_obj):
            logger.error(
                "%s count not equal: legacy count=%s, ng count=%s",
                self.ng_model.__name__,
                len(legacy_key_to_obj),
                len(ng_key_to_obj),
            )

        for l_key, l_obj in legacy_key_to_obj.items():
            ng_obj = ng_key_to_obj.pop(l_key, None)
            if not ng_obj:
                logger.error("ng %s not exist: id/key=%s", self.ng_model.__name__, l_key)
                continue

            different_fields = self._compare_field_value(l_obj, ng_obj, self.assert_fields)
            if different_fields:
                logger.error(
                    "%s[id/key=%s] has different fields, legacy: %s, ng: %s",
                    self.ng_model.__name__,
                    l_key,
                    self._stringify_obj_fields(l_obj, different_fields),
                    self._stringify_obj_fields(ng_obj, different_fields),
                )

    def _compare_field_value(self, src_obj: Any, dst_obj: Any, fields: List[str]) -> List[str]:
        """对比对象字段值的差异，返回有差异的字段"""
        different_fields = []
        for field in fields:
            if getattr(src_obj, field) == getattr(dst_obj, field):
                continue
            different_fields.append(field)

        return different_fields


class DocCategorySynchronizer(BaseSynchronizer):
    """同步文档分类"""

    legacy_model = LegacyDocCategory
    ng_model = DocCategory
    default_display_fields = ["id", "name"]
    pre_check_fields = ["name"]
    assert_fields = ["name"]


class ComponentSystemSynchronizer(BaseSynchronizer):
    """同步组件系统"""

    legacy_model = LegacyComponentSystem
    ng_model = ComponentSystem
    default_display_fields = ["id", "name"]
    pre_check_fields = ["name"]
    assert_fields = ["name", "description", "timeout"]


class SystemDocCategorySynchronizer(BaseSynchronizer):
    """同步系统-文档分类的对应关系"""

    legacy_model = None
    ng_model = SystemDocCategory
    default_display_fields = ["id", "system_id", "doc_category_id"]
    pre_check_fields: List[str] = []
    assert_fields = ["system_id", "doc_category_id"]

    # 旧版 System 和 DocCategory 对应关系，存储在 ComponentSystem 表中，
    # 定义一个新的 Model，与新版 Model 对应
    class LegacySystemDocCategoryInnerMigrator(LegacyModelMigrator, BaseModel):
        id: int
        system_id: int
        doc_category_id: int

        def clone_to_ng_obj(self):
            return SystemDocCategory(
                id=self.id,
                system_id=self.system_id,
                doc_category_id=self.doc_category_id,
            )

        def update_ng_obj_fields(self, ng_obj):
            ng_obj.__dict__.update(
                {
                    "doc_category_id": self.doc_category_id,
                }
            )
            return ng_obj

        def is_changed(self, ng_obj):
            return self.doc_category_id != ng_obj.doc_category_id

    def _get_legacy_key_to_obj(self) -> Dict[Union[str, int], LegacyModelMigrator]:
        legacy_system_id_to_category_id = dict(LegacyComponentSystem.objects.values_list("id", "doc_category_id"))
        legacy_category_ids = set(LegacyDocCategory.objects.values_list("id", flat=True))

        legacy_key_to_obj: Dict[Union[str, int], LegacyModelMigrator] = {}
        for l_system_id, l_category_id in legacy_system_id_to_category_id.items():
            if not l_category_id or l_category_id not in legacy_category_ids:
                continue

            legacy_key_to_obj[l_system_id] = SystemDocCategorySynchronizer.LegacySystemDocCategoryInnerMigrator(
                id=l_system_id,
                system_id=l_system_id,
                doc_category_id=l_category_id,
            )

        return legacy_key_to_obj


class ESBChannelSynchronizer(BaseSynchronizer):
    """同步组件"""

    legacy_model = LegacyESBChannel
    ng_model = ESBChannel
    default_display_fields = ["id", "method", "path"]
    pre_check_fields = ["name", "method", "path"]
    assert_fields = [
        "name",
        "path",
        "method",
        "system_id",
        "component_codename",
        "is_active",
        "timeout",
        "config",
        "permission_level",
    ]

    def _get_legacy_key_to_obj(self) -> Dict[Union[str, int], LegacyModelMigrator]:
        system_id_to_obj = {obj.id: obj for obj in ComponentSystem.objects.all()}
        legacy_key_to_obj = {obj.id: obj for obj in LegacyESBChannel.objects.all()}

        for l_obj in legacy_key_to_obj.values():
            l_obj.ng_system = system_id_to_obj.get(l_obj.component_system_id)

        return legacy_key_to_obj


class ComponentDocSynchronizer(BaseSynchronizer):
    """同步组件文档"""

    legacy_model = LegacyComponentDoc
    ng_model = ComponentDoc
    default_display_fields = ["component_id", "language", "content_md5"]
    pre_check_fields: List[str] = []
    assert_fields = ["component_id", "language", "content_md5"]

    # 旧版组件文档中，一个文档包含了中文、英文两种文档，新版中每个语言有单独一份文档
    # 需对旧版文档拆分，与新版文档一一对应
    class LegacyComponentDocInnerMigrator(LegacyModelMigrator, BaseModel):
        component_id: int
        language: str
        content: str
        content_md5: str

        def clone_to_ng_obj(self) -> ComponentDoc:
            return ComponentDoc(
                component_id=self.component_id,
                language=self.language,
                content=self.content,
                content_md5=self.content_md5,
            )

        def update_ng_obj_fields(self, ng_obj: ComponentDoc) -> ComponentDoc:
            ng_obj.__dict__.update(
                {
                    "content": self.content,
                    "content_md5": self.content_md5,
                }
            )
            return ng_obj

        def is_changed(self, ng_obj: ComponentDoc) -> bool:
            return self.content_md5 != ng_obj.content_md5

    def _get_legacy_key_to_obj(self) -> Dict[Union[str, int], LegacyModelMigrator]:
        legacy_component_ids = set(LegacyESBChannel.objects.values_list("id", flat=True))

        legacy_key_to_obj: Dict[Union[str, int], models.Model] = {}
        for l_doc in LegacyComponentDoc.objects.all():
            # 旧版文档对应的组件不存在
            if l_doc.component_id not in legacy_component_ids:
                continue

            for doc in l_doc.split_doc_by_language():
                key = self._generate_doc_key(doc)
                legacy_key_to_obj[key] = ComponentDocSynchronizer.LegacyComponentDocInnerMigrator.parse_obj(doc)

        return legacy_key_to_obj

    def _get_ng_key_to_obj(self) -> Dict[Union[str, int], models.Model]:
        return {self._generate_doc_key(obj.__dict__): obj for obj in ComponentDoc.objects.all()}

    def _generate_doc_key(self, doc: Dict[str, Any]) -> str:
        return f"{doc['component_id']}:{doc['language']}"


class AppComponentPermissionSynchronizer(BaseSynchronizer):
    """同步组件权限"""

    legacy_model = LegacyAppComponentPermission
    ng_model = AppComponentPermission
    default_display_fields = ["id", "bk_app_code", "component_id"]
    pre_check_fields = ["bk_app_code", "component_id"]
    assert_fields = ["bk_app_code", "component_id", "expires"]
