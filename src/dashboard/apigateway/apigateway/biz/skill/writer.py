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

from apigateway.apps.skill.constants import SkillStatusEnum
from apigateway.apps.skill.models import SkillConfig, SkillMetadata, SkillTag, SkillVersion, SkillVersionRelation

from .constants import SKILL_FILE_NAME

if TYPE_CHECKING:
    from apigateway.core.models import Gateway

    from .declaration import SkillDeclaration


class SkillVersionExistsError(Exception):
    pass


@dataclass
class SavedSkillVersion:
    metadata: SkillMetadata
    version: SkillVersion
    created: bool


@transaction.atomic
def save_skill_version(
    declaration: SkillDeclaration,
    body: str,
    *,
    skill_type: str,
    gateway: Optional[Gateway],
    operator: str,
) -> SavedSkillVersion:
    """按 (type, gateway, name) 找到或新建 metadata，追加一个版本并设为当前版本

    内置 Skill 的 gateway 为空，唯一约束拦不住同名，同名由这里在事务内先查再建保证；
    调用方需保证同一来源的写入串行执行。
    """
    metadata = (
        SkillMetadata.objects.select_for_update()
        .filter(type=skill_type, gateway=gateway, name=declaration.name)
        .first()
    )
    created = metadata is None
    if metadata is None:
        metadata = SkillMetadata(type=skill_type, gateway=gateway, name=declaration.name, created_by=operator)
    elif SkillVersion.objects.filter(metadata=metadata, version=declaration.version.lower()).exists():
        raise SkillVersionExistsError(f"{declaration.name} 已有版本 {declaration.version}")

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

    version = SkillVersion.objects.create(
        metadata=metadata,
        version=declaration.version,
        changelog=declaration.changelog,
        orchestration=orchestration,
        artifact={SKILL_FILE_NAME: body},
        created_by=operator,
        updated_by=operator,
    )
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
    return SavedSkillVersion(metadata=metadata, version=version, created=created)


def _get_or_create_tags(names: List[str]) -> List[SkillTag]:
    return [SkillTag.objects.get_or_create(name=name)[0] for name in names]


def _save_config(metadata: SkillMetadata, orchestration: dict, operator: str) -> None:
    SkillConfig.objects.update_or_create(
        metadata=metadata,
        defaults={"orchestration": orchestration, "updated_by": operator},
        create_defaults={"orchestration": orchestration, "created_by": operator, "updated_by": operator},
    )


def _get_relation_pairs(declaration: SkillDeclaration) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for _, call in declaration.orchestration.iter_calls():
        pair = (call.gateway, call.resource)
        if pair not in pairs:
            pairs.append(pair)
    return pairs
