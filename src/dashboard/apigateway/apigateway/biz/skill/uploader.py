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
"""网关 Skill 上传：预检和提交共用一套校验，提交在校验通过后写库。

校验按顺序执行，前一步有 error 就停止：包结构和大小 -> 叠加表单值 -> 声明字段 -> 网关规则 -> 资源读取
-> 完整校验 -> 渲染 -> 入库大小 -> 版本号。版本号只在提交时、前面都没有 error 时检查。
两者的校验输入不同：预检没有表单，按包里的声明原样校验，包里的基本信息（display_name、display_name_en、
description、tags、version）不合规也是 error；提交时这些字段取表单值、覆盖包里的值后再校验，包里的原值不再校验。
name、changelog、orchestration 始终取包里的声明。
声明是来源：包里只导入 declaration.yaml，入库的正文是网关按声明和本网关当前发布的资源渲染的结果；
包里的 SKILL.md、references/ 等其他文件不读取，给一条 warning 列出。
"""

from dataclasses import dataclass, field
from typing import IO, TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from django.utils.translation import gettext as _

from apigateway.apps.skill.constants import SkillTypeEnum
from apigateway.apps.skill.models import SkillMetadata

from .archive import SkillArchiveError, SkillPackage, ValidationMessage, read_skill_package
from .constants import SKILL_DECLARATION_FILE_NAME, SKILL_FILE_NAME
from .declaration import (
    DeclarationFieldError,
    SkillDeclaration,
    SkillDeclarationError,
    load_declaration_yaml,
    normalize_tag_name,
    parse_declaration,
)
from .renderer import render_skill_body
from .resource_loader import ReleasedResourceProvider, ResourceProvider
from .skill import SkillHandler
from .validator import ValidationResult, validate_declaration
from .writer import SavedSkillVersion, save_skill_version

if TYPE_CHECKING:
    from apigateway.core.models import Gateway

# 不导入的文件在 warning 里最多列出的个数，其余只给总数
_IGNORED_FILES_DISPLAY_LIMIT = 10


class SkillPackageInvalidError(Exception):
    def __init__(self, errors: List[ValidationMessage], warnings: List[ValidationMessage]):
        super().__init__("; ".join(error.message for error in errors))
        self.errors = errors
        self.warnings = warnings


@dataclass
class SkillUploadForm:
    """上传、发布新版本时表单提交的值，覆盖声明里的同名字段；name、changelog 只取声明"""

    display_name: str
    display_name_en: Optional[str]
    description: str
    tags: List[str]
    version: str

    def as_declaration_fields(self) -> Dict[str, Any]:
        """覆盖到声明 dict 上的字段

        例如：display_name_en 为 None -> {"display_name": ..., "display_name_en": None, ..., "version": "1.2.0"}
        """
        return {
            "display_name": self.display_name,
            "display_name_en": self.display_name_en,
            "description": self.description,
            "tags": self.tags,
            "version": self.version,
        }


@dataclass
class SkillPackageCheckResult:
    """预检结果：errors 不为空时不能提交；package、existing_skill、basic_info_diffs 给页面预填和提示"""

    errors: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    package: Optional[Dict[str, Any]] = None
    existing_skill: Optional[Dict[str, Any]] = None
    basic_info_diffs: List[str] = field(default_factory=list)


@dataclass
class _Validation:
    errors: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    # 包里原样的声明（未叠加表单值），用于预检预填
    package_declaration: Optional[SkillDeclaration] = None
    declaration: Optional[SkillDeclaration] = None
    body: str = ""


def check_skill_package(
    gateway: Gateway,
    fileobj: IO[bytes],
    skill_name: Optional[str] = None,
    provider: Optional[ResourceProvider] = None,
) -> SkillPackageCheckResult:
    """上传预检：只校验、不写库；skill_name 为更新侧滑的 Skill 的 name，包里的 name 和它不一致时报 error

    不叠加表单值，包里的基本信息也须合法；不检查版本号，只在 existing_skill 里返回已有的最高版本，供页面提示。

    例如：包里是 1.2.0、本网关已有这个 Skill、线上 1.1.0 -> errors 为空，
        existing_skill 为 {"skill_id": "g_demo_release-check", "current_version": "1.1.0", ...}
    """
    validation = _validate(gateway, fileobj, form=None, skill_name=skill_name, provider=provider)
    result = SkillPackageCheckResult(errors=validation.errors, warnings=validation.warnings)

    declaration = validation.package_declaration
    if declaration is None:
        return result
    result.package = _package_info(declaration)
    metadata = (
        SkillMetadata.objects.filter(type=SkillTypeEnum.GATEWAY.value, gateway=gateway, name=declaration.name)
        .select_related("gateway", "current_version")
        .prefetch_related("tags")
        .first()
    )
    if metadata is not None:
        result.existing_skill = {
            "skill_id": metadata.code,
            "current_version": metadata.current_version.version,
            "latest_version": SkillHandler.get_latest_version(metadata),
            "status": metadata.status,
        }
        result.basic_info_diffs = _basic_info_diffs(declaration, metadata)
    return result


def publish_gateway_skill(
    gateway: Gateway,
    fileobj: IO[bytes],
    form: SkillUploadForm,
    operator: str,
    overwrite: bool = False,
    skill_name: Optional[str] = None,
    provider: Optional[ResourceProvider] = None,
) -> SavedSkillVersion:
    """上传或发布新版本：校验通过后写库并设为线上版本；本网关没有包里的 name 就新建

    基本信息和版本号取表单，包里的原值不校验；changelog 只取包里声明的 date、content。
    包有 error 时抛 SkillPackageInvalidError，不检查版本号；版本号在写库时、锁住这条 Skill 后判断，
    已存在且没带 overwrite 抛 SkillVersionExistsError，不大于最高版本抛 SkillVersionNotNewerError，
    同名 Skill 已归档抛 SkillArchivedError。

    例如：表单 display_name 改成「发布核对」、version 1.2.0 -> 入库的展示名和版本号取表单，
        正文为网关渲染结果，一级标题是「发布核对」
    """
    validation = _validate(gateway, fileobj, form=form, skill_name=skill_name, provider=provider)
    if validation.errors:
        raise SkillPackageInvalidError(validation.errors, validation.warnings)
    return save_skill_version(
        validation.declaration,  # type: ignore[arg-type]
        validation.body,
        skill_type=SkillTypeEnum.GATEWAY.value,
        gateway=gateway,
        operator=operator,
        overwrite_existing=overwrite,
    )


def _validate(
    gateway: Gateway,
    fileobj: IO[bytes],
    form: Optional[SkillUploadForm],
    skill_name: Optional[str],
    provider: Optional[ResourceProvider],
) -> _Validation:
    """按顺序执行版本号以外的校验，前一步有 error 就停止；全部通过时 declaration、body 为要入库的声明和正文

    例如：包结构不合规 -> 只有包结构的 error；资源未发布 -> 包、声明都通过，error 列出资源和原因
    """
    result = _Validation()
    loaded = _load_package(result, fileobj, skill_name)
    if loaded is None:
        return result
    package, data = loaded
    declaration_file = package.path_of(SKILL_DECLARATION_FILE_NAME)
    skill_file = package.path_of(SKILL_FILE_NAME)

    # 发布时用表单值覆盖声明，再校验声明字段
    overridden: Tuple[str, ...] = ()
    if form is not None:
        form_fields = form.as_declaration_fields()
        data = {**data, **form_fields}
        overridden = tuple(form_fields)
    try:
        declaration = parse_declaration(data)
    except SkillDeclarationError as err:
        result.errors += [_to_message(item, declaration_file, overridden) for item in err.items]
        return result

    # 只能调用当前网关，且所有步骤用同一个环境
    result.errors += _check_gateway_rules(declaration, gateway, declaration_file)
    if result.errors:
        return result

    # 按当前发布的资源定义校验编排
    provider = provider or ReleasedResourceProvider()
    validation = validate_declaration(declaration, provider)
    result.warnings += [ValidationMessage(declaration_file, None, text) for text in validation.warnings]
    result.errors += _validation_errors(validation, declaration_file)
    if result.errors:
        return result

    # 按声明渲染 SKILL.md 正文
    rendered = render_skill_body(declaration, provider)
    result.warnings += [ValidationMessage(skill_file, None, text) for text in rendered.warnings]

    result.declaration = declaration
    result.body = rendered.body
    return result


def _load_package(
    result: _Validation, fileobj: IO[bytes], skill_name: Optional[str]
) -> Optional[Tuple[SkillPackage, Dict[str, Any]]]:
    """读包、解析声明 YAML，并检查目录名；有 error 时写进 result 并返回 None

    包里有不导入的文件时加一条 warning，最多列出 _IGNORED_FILES_DISPLAY_LIMIT 个；
    包里的声明能单独通过字段校验时写入 result.package_declaration，供预检返回包信息。

    例如：合规的包 -> (包, 声明 dict)；目录名与声明的 name 不同 -> None，带一条 error；
    包里另有 SKILL.md -> 多一条 warning「只导入 declaration.yaml，以下文件不导入：release-check/SKILL.md」
    """
    try:
        package = read_skill_package(fileobj)
    except SkillArchiveError as err:
        result.errors = err.errors
        return None
    declaration_file = package.path_of(SKILL_DECLARATION_FILE_NAME)
    if package.ignored:
        files = "、".join(package.path_of(path) for path in package.ignored[:_IGNORED_FILES_DISPLAY_LIMIT])
        if len(package.ignored) > _IGNORED_FILES_DISPLAY_LIMIT:
            files = _("{files} 等 {count} 个文件").format(files=files, count=len(package.ignored))
        result.warnings.append(
            ValidationMessage(None, None, _("只导入 declaration.yaml，以下文件不导入：{files}").format(files=files))
        )

    try:
        data = load_declaration_yaml(package.declaration)
    except SkillDeclarationError as err:
        result.errors += [_to_message(item, declaration_file) for item in err.items]
        return None
    try:
        result.package_declaration = parse_declaration(data)
    except SkillDeclarationError:
        pass

    # 目录名等于声明的 name；更新时还要等于当前 Skill 的 name
    result.errors += _check_names(package, data, skill_name, declaration_file)
    if result.errors:
        return None
    return package, data


def _validation_errors(validation: ValidationResult, declaration_file: str) -> List[ValidationMessage]:
    """声明和资源交叉校验的 error：有资源不可编排时只报这些资源，否则报校验返回的其余 error

    例如：引用的资源未发布 -> 一条「…不可编排：…；请先发布该资源或补充请求参数和响应定义」；全部通过 -> []
    """
    if validation.missing_resources:
        return [
            ValidationMessage(
                declaration_file,
                None,
                _(
                    "{gateway}.{resource}（环境 {stage}）不可编排：{reason}；请先发布该资源或补充请求参数和响应定义"
                ).format(gateway=item.gateway, resource=item.resource, stage=item.stage, reason=item.reason),
            )
            for item in validation.missing_resources
        ]
    return [ValidationMessage(declaration_file, None, text) for text in validation.errors]


def _check_names(
    package: SkillPackage, data: Dict[str, Any], skill_name: Optional[str], declaration_file: str
) -> List[ValidationMessage]:
    """顶层目录名等于声明的 name；更新侧滑传了 skill_name 时声明的 name 还要等于它

    例如：目录 release-check、声明 name release-check -> []；
    更新 g_demo_release-check 却传了 name 为 other 的包 -> 一条 error
    """
    name = data.get("name")
    errors = []
    if name != package.root:
        errors.append(
            ValidationMessage(
                declaration_file,
                "name",
                _("顶层目录名 {root} 与声明的 name {name} 不一致").format(root=package.root, name=name),
            )
        )
    if skill_name is not None and name != skill_name:
        errors.append(
            ValidationMessage(
                declaration_file,
                "name",
                _("包里的 name {name} 与要更新的 Skill {skill_name} 不一致").format(name=name, skill_name=skill_name),
            )
        )
    return errors


def _to_message(error: DeclarationFieldError, file: str, overridden: Tuple[str, ...] = ()) -> ValidationMessage:
    """声明的一条错误 -> ValidationMessage；顶层字段被表单覆盖时 file 为空，错误归到表单字段

    例如：
        loc ("version",)，overridden 含 version -> ValidationMessage(None, "version", ...)
        loc ("orchestration", "steps", 0, "id") -> ValidationMessage("demo/declaration.yaml", "orchestration.steps[0].id", ...)
        YAML 解析失败，loc 为空 -> ValidationMessage("demo/declaration.yaml", None, "YAML 解析失败：...")
    """
    top_level = error.loc[0] if error.loc else None
    return ValidationMessage(None if top_level in overridden else file, error.field, error.message)


def _check_gateway_rules(declaration: SkillDeclaration, gateway: Gateway, file: str) -> List[ValidationMessage]:
    """网关 Skill 只能调用当前网关的接口，所有步骤用同一个环境

    例如：当前网关 demo，步骤用 demo/a@prod、demo/b@prod -> []；
    有一步用 bk-sops/x@prod -> 一条 error；一步 prod、一步 test -> 一条 error
    """
    errors = []
    for index, step in enumerate(declaration.orchestration.steps):
        if step.gateway != gateway.name:
            errors.append(
                ValidationMessage(
                    file,
                    f"orchestration.steps[{index}].uses",
                    _("只能调用当前网关 {gateway} 的接口：{uses}").format(gateway=gateway.name, uses=step.uses),
                )
            )
    stages = sorted({step.stage for step in declaration.orchestration.steps})
    if len(stages) > 1:
        errors.append(
            ValidationMessage(
                file,
                "orchestration.steps",
                _("所有步骤应使用同一个环境：{stages}").format(stages=", ".join(stages)),
            )
        )
    return errors


def _package_info(declaration: SkillDeclaration) -> Dict[str, Any]:
    """包里的基本信息、版本、changelog、环境和接口，给预检预填

    例如：两步都调 demo 的 prod -> {"name": ..., "stage": "prod", "apis": [{"gateway_name": "demo", ...}, ...]}
    """
    steps = declaration.orchestration.steps
    apis: List[Dict[str, str]] = []
    for step in steps:
        api = {"gateway_name": step.gateway, "resource_name": step.resource}
        if api not in apis:
            apis.append(api)
    return {
        "name": declaration.name,
        "display_name": declaration.display_name,
        "display_name_en": declaration.display_name_en,
        "description": declaration.description,
        "tags": declaration.tags,
        "version": declaration.version,
        "changelog": declaration.changelog_data(),
        "stage": steps[0].stage if steps else None,
        "apis": apis,
    }


def _basic_info_diffs(declaration: SkillDeclaration, metadata: SkillMetadata) -> List[str]:
    """包里和线上不同的基本信息字段；标签按规范化后的集合比较

    例如：包里描述改了、标签多了一个 -> ["description", "tags"]；英文名都没填 -> 不算差异
    """
    current = {
        "display_name": metadata.display_name,
        "display_name_en": metadata.display_name_en or None,
        "description": metadata.description,
        "tags": sorted(tag.name for tag in metadata.tags.all()),
    }
    uploaded = {
        "display_name": declaration.display_name,
        "display_name_en": declaration.display_name_en or None,
        "description": declaration.description,
        "tags": sorted(normalize_tag_name(tag) for tag in declaration.tags),
    }
    return [key for key in current if current[key] != uploaded[key]]
