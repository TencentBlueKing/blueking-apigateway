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
from typing import List, Optional

from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata

from .constants import SkillSyncStatusEnum
from .declaration import SkillDeclaration, SkillDeclarationError, parse_declaration
from .renderer import render_skill_body
from .resource_loader import ReleasedResourceProvider, ResourceProvider
from .validator import validate_declaration
from .writer import SkillVersionExistsError, SkillVersionNotNewerError, check_new_version, save_skill_version

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
    name: Optional[str] = None,
    dry_run: bool = False,
) -> List[SkillSyncResult]:
    """逐条处理目录下的声明文件；name 按文件名（不含扩展名，与声明的 name 相同）只处理一条"""
    paths = sorted(Path(declarations_dir).glob(DECLARATION_FILE_PATTERN))
    if name:
        paths = [path for path in paths if path.stem == name]

    provider = ReleasedResourceProvider()
    return [sync_platform_skill(path, provider, dry_run) for path in paths]


def sync_platform_skill(path: Path, provider: ResourceProvider, dry_run: bool = False) -> SkillSyncResult:
    result = SkillSyncResult(name=path.stem, status=SkillSyncStatusEnum.SKIPPED.value)
    try:
        _sync(path, provider, dry_run, result)
    except Exception as err:  # pylint: disable=broad-except
        logger.exception("sync platform skill %s failed", path)
        result.reasons.append(f"{type(err).__name__}: {err}")
        return result
    if result.status == SkillSyncStatusEnum.SKIPPED.value:
        # 版本已存在但不是当前版本时带 metadata_id，记为信息；其余跳过记为警告
        level = logging.INFO if result.metadata_id else logging.WARNING
        logger.log(level, "skip platform skill %s: %s", result.name, "; ".join(result.reasons))
    return result


def _localize_gateway_names(declaration: SkillDeclaration) -> None:
    """内外版名字不同的网关，换成当前版本的网关名"""
    names = settings.EDITION_GATEWAY_NAMES
    for step in declaration.orchestration.steps:
        gateway, rest = step.uses.split("/", 1)
        step.uses = f"{names.get(gateway, gateway)}/{rest}"
    declaration.tags = [names.get(tag, tag) for tag in declaration.tags]


def _sync(path: Path, provider: ResourceProvider, dry_run: bool, result: SkillSyncResult) -> None:
    try:
        declaration = parse_declaration(path.read_text(encoding="utf-8"))
    except SkillDeclarationError as err:
        result.reasons += err.errors
        return
    result.name = declaration.name
    if path.stem != declaration.name:
        result.reasons.append(
            _("文件名 {file_name} 与声明的 name {name} 不一致").format(file_name=path.stem, name=declaration.name)
        )
        return
    _localize_gateway_names(declaration)

    metadata = SkillMetadata.objects.filter(
        type=SkillTypeEnum.PLATFORM.value, gateway__isnull=True, name=declaration.name
    ).first()
    overwrite_existing = False
    if metadata:
        current = metadata.current_version
        # 与当前版本号一致时继续往下走，写库时覆盖这一版
        if current is not None and current.version == declaration.version.lower():
            overwrite_existing = True
        else:
            try:
                check_new_version(metadata, declaration.version)
            except SkillVersionExistsError:
                result.reasons.append(_("版本 {version} 已存在").format(version=declaration.version))
                result.metadata_id = metadata.id
                return
            except SkillVersionNotNewerError as err:
                result.reasons.append(str(err))
                return

    validation = validate_declaration(declaration, provider)
    result.warnings += validation.warnings
    if validation.missing_resources:
        result.reasons += [
            _("{gateway}.{resource}（环境 {stage}）不可编排：{reason}").format(
                gateway=item.gateway, resource=item.resource, stage=item.stage, reason=item.reason
            )
            for item in validation.missing_resources
        ]
        return
    if validation.errors:
        result.reasons += validation.errors
        return

    rendered = render_skill_body(declaration, provider)
    result.warnings += rendered.warnings

    if dry_run:
        result.status = SkillSyncStatusEnum.RELEASED.value if metadata else SkillSyncStatusEnum.CREATED.value
        result.reasons.append(_("dry-run，未写库"))
    else:
        saved = save_skill_version(
            declaration,
            rendered.body,
            skill_type=SkillTypeEnum.PLATFORM.value,
            gateway=None,
            operator=settings.GATEWAY_DEFAULT_CREATOR,
            overwrite_existing=overwrite_existing,
        )
        result.status = SkillSyncStatusEnum.CREATED.value if saved.created else SkillSyncStatusEnum.RELEASED.value
        result.metadata_id = saved.metadata.id
