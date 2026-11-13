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
"""Skill 发版写库：内置 Skill 注入和网关 Skill 上传共用"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Tuple

from django.db import transaction
from django.utils.translation import gettext as _

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillConfig, SkillMetadata, SkillTag, SkillVersion, SkillVersionRelation

from .constants import SKILL_FILE_NAME
from .declaration import parse_version

if TYPE_CHECKING:
    from apigateway.core.models import Gateway

    from .declaration import SkillDeclaration


class SkillVersionExistsError(Exception):
    pass


class SkillVersionNotNewerError(Exception):
    pass


def check_new_version(metadata: SkillMetadata, version: str) -> None:
    """新版本必须不存在，且按 major.minor.patch 高于当前版本

    低版本若成为当前版本，之后再注入更高的版本时，那个版本已存在但不是当前版本，会被跳过，
    当前版本就停在低版本上。
    与当前版本号一致的覆盖不走这里，由 save_skill_version(overwrite_existing=True) 处理。

    例如：已有 1.0.0、1.1.0，当前版本 1.1.0 时
        "1.2.0" -> 通过
        "1.0.0" -> SkillVersionExistsError
        "1.0.10" -> SkillVersionNotNewerError
    """
    if SkillVersion.objects.filter(metadata=metadata, version=version).exists():
        raise SkillVersionExistsError(_("{name} 已有版本 {version}").format(name=metadata.name, version=version))
    current = metadata.current_version
    if current and parse_version(version) <= parse_version(current.version):
        raise SkillVersionNotNewerError(
            _("{name} 的版本 {version} 不高于当前版本 {current}").format(
                name=metadata.name, version=version, current=current.version
            )
        )


@dataclass
class SavedSkillVersion:
    metadata: SkillMetadata
    version: SkillVersion
    created: bool
    overwritten: bool = False


@transaction.atomic
def save_skill_version(
    declaration: SkillDeclaration,
    body: str,
    skill_type: str,
    gateway: Optional[Gateway],
    operator: str,
    overwrite_existing: bool = False,
) -> SavedSkillVersion:
    """按 (type, gateway, name) 找到或新建 metadata，写入版本并设为当前版本

    内置 Skill 的 gateway 为空，唯一约束拦不住同名，同名由这里在事务内先查再建保证；
    调用方需保证同一来源的写入串行执行。
    overwrite_existing 为真且声明版本与当前版本一致时，覆盖这一版的
    changelog、编排、正文和关联资源，不新增版本行，created_time 保持不变。
    已存在但不是当前版本的版本仍拒绝写入。

    例如：
        首次写入 1.0.0 -> created 为真，新建 metadata、编排、版本和关联资源
        再写入 1.1.0 -> 新增版本行并设为当前版本，download_count 等统计不变
        overwrite_existing 为真时再写入 1.1.0 -> overwritten 为真，版本行和 created_time 不变
    """
    metadata = (
        SkillMetadata.objects.select_for_update()
        .filter(type=skill_type, gateway=gateway, name=declaration.name)
        .first()
    )
    created = metadata is None
    existing_version: Optional[SkillVersion] = None
    if metadata is None:
        metadata = SkillMetadata(type=skill_type, gateway=gateway, name=declaration.name, created_by=operator)
    else:
        if overwrite_existing and metadata.current_version_id is not None:
            existing_version = (
                SkillVersion.objects.select_for_update()
                .filter(id=metadata.current_version_id, metadata=metadata, version=declaration.version)
                .first()
            )
        if existing_version is None:
            check_new_version(metadata, declaration.version)

    metadata.display_name = declaration.display_name
    metadata.display_name_en = declaration.display_name_en
    metadata.description = declaration.description
    metadata.updated_by = operator
    if created:
        metadata.save()
    else:
        metadata.save(update_fields=["display_name", "display_name_en", "description", "updated_by", "updated_time"])
    metadata.tags.set(_get_or_create_tags(declaration.normalized_tags))

    orchestration = declaration.orchestration_data()
    _save_config(metadata, orchestration, operator)

    if existing_version is None:
        version = SkillVersion.objects.create(
            metadata=metadata,
            version=declaration.version,
            changelog=declaration.current_changelog.model_dump(mode="json"),
            orchestration=orchestration,
            artifact={SKILL_FILE_NAME: body},
            created_by=operator,
            updated_by=operator,
        )
    else:
        version = existing_version
        version.changelog = declaration.current_changelog.model_dump(mode="json")
        version.orchestration = orchestration
        version.artifact = {SKILL_FILE_NAME: body}
        version.updated_by = operator
        version.save(update_fields=["changelog", "orchestration", "artifact", "updated_by", "updated_time"])
        version.relations.all().delete()
    SkillVersionRelation.objects.bulk_create(
        [
            SkillVersionRelation(
                metadata=metadata, version=version, gateway_name=gateway_name, resource_name=resource_name
            )
            for gateway_name, resource_name in _get_relation_pairs(declaration)
        ]
    )

    metadata.current_version = version
    metadata.status = SkillStatusEnum.PUBLISHED.value
    metadata.save(update_fields=["current_version", "status", "updated_time"])
    return SavedSkillVersion(
        metadata=metadata, version=version, created=created, overwritten=existing_version is not None
    )


def _get_or_create_tags(names: List[str]) -> List[SkillTag]:
    """按名字取标签，不存在的新建；标签在所有 Skill 之间共用

    例如：["运维", "job"]，「运维」已存在 -> 复用它，新建「job」
    """
    return [SkillTag.objects.get_or_create(name=name)[0] for name in names]


def _save_config(metadata: SkillMetadata, orchestration: dict, operator: str) -> None:
    """写入或更新 Skill 当前的编排；每个 Skill 只有一条 SkillConfig

    例如：首次注入时新建，created_by、updated_by 都是 operator；之后发版只更新 orchestration 和 updated_by
    """
    SkillConfig.objects.update_or_create(
        metadata=metadata,
        defaults={"orchestration": orchestration, "updated_by": operator},
        create_defaults={"orchestration": orchestration, "created_by": operator, "updated_by": operator},
    )


def _get_relation_pairs(declaration: SkillDeclaration) -> List[Tuple[str, str]]:
    """步骤用到的 (网关名, 资源名)，按步骤顺序去重，写入 SkillVersionRelation 供检索

    例如：三步依次用 execute_job_plan、get_job_instance_status、get_job_instance_status ->
        [("jobv3-cloud", "execute_job_plan"), ("jobv3-cloud", "get_job_instance_status")]
    """
    pairs: List[Tuple[str, str]] = []
    for step in declaration.orchestration.steps:
        pair = (step.gateway, step.resource)
        if pair not in pairs:
            pairs.append(pair)
    return pairs
