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
"""网关 Skill 的管理操作：只改基本信息、切换线上版本、归档和恢复、删除。

都会刷新 Skill 的 updated_by、updated_time（删除除外）；auto_now 字段不在 update_fields 里时不会刷新，
所以每个 update_fields 都带上 updated_time。不改任何版本的 created_*。
"""

from typing import List, Optional

from django.db import transaction
from django.utils.translation import gettext as _

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion

from .declaration import normalize_tag_name
from .writer import SkillArchivedError, get_or_create_tags


class SkillNotArchivedError(Exception):
    pass


def ensure_not_archived(metadata: SkillMetadata) -> None:
    """已归档时抛 SkillArchivedError：已归档的 Skill 不能改基本信息、发布新版本、切换版本

    例如：status 为 published -> 通过；status 为 archived -> SkillArchivedError「请先恢复」
    """
    if metadata.status == SkillStatusEnum.ARCHIVED.value:
        raise SkillArchivedError(_("Skill {name} 已归档，请先恢复").format(name=metadata.name))


@transaction.atomic
def update_skill_basic_info(
    metadata: SkillMetadata,
    display_name: str,
    display_name_en: Optional[str],
    description: str,
    tags: List[str],
    operator: str,
) -> None:
    """只改基本信息：展示名、描述、标签；不产生新版本，版本里冻结的正文不改，下载包打包时按新值生成

    例如：把 display_name 改成「发布核对」 -> 下载包 frontmatter 的 display_name 和正文一级标题都变成「发布核对」，
        版本数和 download_count 不变
    """
    ensure_not_archived(metadata)
    metadata.display_name = display_name
    metadata.display_name_en = display_name_en or None
    metadata.description = description
    metadata.updated_by = operator
    metadata.save(update_fields=["display_name", "display_name_en", "description", "updated_by", "updated_time"])
    metadata.tags.set(get_or_create_tags([normalize_tag_name(tag) for tag in tags]))


def set_current_version(metadata: SkillMetadata, version: SkillVersion, operator: str) -> None:
    """切换线上版本：只改 current_version，各版本的发布时间都不变

    例如：线上 1.2.0 切回 1.1.0 -> 市场的「发布于」变成 1.1.0 的发布时间，Skill 的 updated_time 是这次
    """
    ensure_not_archived(metadata)
    metadata.current_version = version
    metadata.updated_by = operator
    metadata.save(update_fields=["current_version", "updated_by", "updated_time"])


def set_skill_status(metadata: SkillMetadata, status: str, operator: str) -> None:
    """归档（archived）或恢复（published）：只改 status

    例如：归档后 Skill 市场和免登录下载都看不到它，网关页仍能查看、下载；恢复后重新可见
    """
    metadata.status = status
    metadata.updated_by = operator
    metadata.save(update_fields=["status", "updated_by", "updated_time"])


@transaction.atomic
def delete_skill(metadata: SkillMetadata) -> None:
    """删除已归档的 Skill，config、版本、relation、标签中间表级联删除，标签本身保留；未归档时抛 SkillNotArchivedError

    current_version 是 PROTECT 外键，先清空再删 metadata，否则级联删除版本时被拦住。

    例如：已归档、有 2 个版本 -> metadata 和 2 个版本都删除；使用中 -> SkillNotArchivedError「请先归档」
    """
    if metadata.status != SkillStatusEnum.ARCHIVED.value:
        raise SkillNotArchivedError(_("Skill {name} 未归档，请先归档再删除").format(name=metadata.name))
    SkillMetadata.objects.filter(id=metadata.id).update(current_version=None)
    SkillMetadata.objects.filter(id=metadata.id).delete()
