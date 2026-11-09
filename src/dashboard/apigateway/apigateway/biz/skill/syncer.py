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
"""内置 Skill 注入：data/skill/declarations/*.yaml -> 数据库"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from django.conf import settings

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata, SkillVersion

from .constants import SkillSyncStatusEnum
from .declaration import SkillDeclarationError, parse_declaration
from .renderer import render_skill_body
from .resource_loader import ReleasedResourceProvider
from .validator import validate_declaration
from .writer import save_skill_version

if TYPE_CHECKING:
    from .resource_definition import ResourceProvider

logger = logging.getLogger(__name__)

DECLARATION_FILE_PATTERN = "*.yaml"


@dataclass
class SkillSyncResult:
    name: str
    status: str
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata_id: Optional[int] = None


def sync_platform_skills(
    declarations_dir: Path,
    resources_dir: Optional[Path] = None,
    *,
    name: Optional[str] = None,
    dry_run: bool = False,
) -> List[SkillSyncResult]:
    """逐条处理目录下的声明文件；name 按文件名（不含扩展名，与声明的 name 相同）只处理一条"""
    paths = sorted(Path(declarations_dir).glob(DECLARATION_FILE_PATTERN))
    if name:
        paths = [path for path in paths if path.stem == name]

    provider = ReleasedResourceProvider(snapshot_dir=resources_dir)
    return [sync_platform_skill(path, provider, dry_run=dry_run) for path in paths]


def get_changed_metadata_ids(results: List[SkillSyncResult]) -> List[int]:
    """本次新建和新版本的 metadata ID"""
    changed = (SkillSyncStatusEnum.CREATED.value, SkillSyncStatusEnum.NEW_VERSION.value)
    return [result.metadata_id for result in results if result.status in changed and result.metadata_id]


def sync_platform_skill(path: Path, provider: ResourceProvider, *, dry_run: bool = False) -> SkillSyncResult:
    result = SkillSyncResult(name=path.stem, status=SkillSyncStatusEnum.FAILED.value)
    try:
        _sync(path, provider, dry_run, result)
    except Exception as err:  # pylint: disable=broad-except
        logger.exception("sync platform skill %s failed", path)
        result.status = SkillSyncStatusEnum.FAILED.value
        result.reasons.append(f"{type(err).__name__}: {err}")
    return result


def _sync(path: Path, provider: ResourceProvider, dry_run: bool, result: SkillSyncResult) -> None:
    try:
        declaration = parse_declaration(path.read_text(encoding="utf-8"))
    except SkillDeclarationError as err:
        result.status = SkillSyncStatusEnum.REJECTED.value
        result.reasons += err.errors
        return
    result.name = declaration.name

    metadata = SkillMetadata.objects.filter(
        type=SkillTypeEnum.PLATFORM.value, gateway__isnull=True, name=declaration.name
    ).first()
    if metadata and SkillVersion.objects.filter(metadata=metadata, version=declaration.version.lower()).exists():
        result.status = SkillSyncStatusEnum.SKIPPED_SAME_VERSION.value
        result.reasons.append(f"版本 {declaration.version} 已存在")
        result.metadata_id = metadata.id
        return

    validation = validate_declaration(declaration, provider)
    result.warnings += validation.warnings
    if validation.missing_resources:
        result.status = SkillSyncStatusEnum.SKIPPED_MISSING_RESOURCES.value
        result.reasons += [
            f"{item.gateway}.{item.resource}（环境 {item.stage}）在当前发布版本中不存在，下次部署重试"
            for item in validation.missing_resources
        ]
        return
    if validation.errors:
        result.status = SkillSyncStatusEnum.REJECTED.value
        result.reasons += validation.errors
        return

    rendered = render_skill_body(declaration, provider)
    result.warnings += rendered.warnings

    status = SkillSyncStatusEnum.NEW_VERSION.value if metadata else SkillSyncStatusEnum.CREATED.value
    if dry_run:
        result.status = status
        result.reasons.append("dry-run，未写库")
        return

    saved = save_skill_version(
        declaration,
        rendered.body,
        skill_type=SkillTypeEnum.PLATFORM.value,
        gateway=None,
        operator=settings.GATEWAY_DEFAULT_CREATOR,
    )
    result.status = SkillSyncStatusEnum.CREATED.value if saved.created else SkillSyncStatusEnum.NEW_VERSION.value
    result.metadata_id = saved.metadata.id
