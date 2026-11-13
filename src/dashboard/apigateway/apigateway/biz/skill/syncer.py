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
from typing import Dict, List, Optional

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
    gateway_names: Optional[Dict[str, str]] = None,
) -> List[SkillSyncResult]:
    """逐条处理目录下的声明文件；name 按文件名（不含扩展名，与声明的 name 相同）只处理一条

    gateway_names：声明中的网关名 -> 当前版本的网关名，不在其中的网关名保持不变

    例如：sync_platform_skills 命令部署时调用，目录下 5 个声明返回 5 条结果；
    name="job-plan-run-and-log" 时只处理 job-plan-run-and-log.yaml
    """
    paths = sorted(Path(declarations_dir).glob(DECLARATION_FILE_PATTERN))
    if name:
        paths = [path for path in paths if path.stem == name]

    provider = ReleasedResourceProvider()
    return [sync_platform_skill(path, provider, dry_run, gateway_names) for path in paths]


def sync_platform_skill(
    path: Path,
    provider: ResourceProvider,
    dry_run: bool = False,
    gateway_names: Optional[Dict[str, str]] = None,
) -> SkillSyncResult:
    """注入一个声明文件并返回结果；任何异常都只记进本条结果，不影响其他声明，也不让部署失败

    例如：声明引用的资源在环境里未发布 -> status 为 skipped，reasons 写明哪个资源不可编排、原因是什么
    """
    result = SkillSyncResult(name=path.stem, status=SkillSyncStatusEnum.SKIPPED.value)
    try:
        _sync(path, provider, dry_run, gateway_names or {}, result)
    except Exception as err:  # pylint: disable=broad-except
        logger.exception("sync platform skill %s failed", path)
        result.reasons.append(f"{type(err).__name__}: {err}")
        return result
    if result.status == SkillSyncStatusEnum.SKIPPED.value:
        # 版本已存在但不是当前版本时带 metadata_id，记为信息；其余跳过记为警告
        level = logging.INFO if result.metadata_id else logging.WARNING
        logger.log(level, "skip platform skill %s: %s", result.name, "; ".join(result.reasons))
    return result


def _localize_gateway_names(declaration: SkillDeclaration, names: Dict[str, str]) -> None:
    """内外版名字不同的网关，换成当前版本的网关名；就地修改 steps[].uses 和 tags

    例如：names 为 {"bk-job": "jobv3-cloud"} 时，uses "bk-job/execute_job_plan@prod" 改为
    "jobv3-cloud/execute_job_plan@prod"，标签 "bk-job" 改为 "jobv3-cloud"
    """
    for step in declaration.orchestration.steps:
        gateway, rest = step.uses.split("/", 1)
        step.uses = f"{names.get(gateway, gateway)}/{rest}"
    declaration.tags = [names.get(tag, tag) for tag in declaration.tags]


def _sync(
    path: Path,
    provider: ResourceProvider,
    dry_run: bool,
    gateway_names: Dict[str, str],
    result: SkillSyncResult,
) -> None:
    """解析、校验、渲染并写入一条声明，把状态和原因写进 result；任一步不通过时停在这一步

    例如：
        版本与当前版本相同 -> 覆盖当前版本，status 为 released
        版本已存在但不是当前版本 -> status 为 skipped，result.metadata_id 有值
        dry_run 为真 -> 只校验和渲染，reasons 为「dry-run，未写库」
    """
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
    _localize_gateway_names(declaration, gateway_names)

    metadata = SkillMetadata.objects.filter(
        type=SkillTypeEnum.PLATFORM.value, gateway__isnull=True, name=declaration.name
    ).first()
    overwrite_existing = False
    if metadata:
        current = metadata.current_version
        # 与当前版本号一致时继续往下走，写库时覆盖这一版
        if current is not None and current.version == declaration.version:
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
