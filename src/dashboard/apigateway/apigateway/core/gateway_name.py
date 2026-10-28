"""Gateway display-name normalization and global, case-insensitive checks.

Column indexes guarantee column uniqueness. Cross-field checks intentionally do
not serialize writers and therefore do not guarantee uniqueness under races.
"""

import re
from enum import StrEnum

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

NAMING_FIELDS = frozenset({"name", "display_name", "display_name_en"})
GATEWAY_DISPLAY_NAME_MAX_LENGTH = 64
GATEWAY_DISPLAY_NAME_EN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9 -]*")


class GatewayNameConflictCode(StrEnum):
    UNIQUE = "unique"
    EFFECTIVE_EN_CONFLICT = "effective_en_conflict"
    TECHNICAL_NAME_CONFLICT = "technical_name_conflict"
    DISPLAY_NAME_CONFLICT = "display_name_conflict"


def normalize_gateway_names(name, display_name, display_name_en):
    display_name = (display_name or "").strip() or (name or "").strip()
    display_name_en = (display_name_en or "").strip() or None
    errors = {}
    if not display_name:
        errors["display_name"] = ValidationError(_("This display name cannot be empty."), code="blank")
    for field, value in (("display_name", display_name), ("display_name_en", display_name_en)):
        if value is not None and len(value) > GATEWAY_DISPLAY_NAME_MAX_LENGTH:
            errors[field] = ValidationError(
                _("Ensure this value has at most %(max_length)s characters."),
                code="max_length",
                params={"max_length": GATEWAY_DISPLAY_NAME_MAX_LENGTH},
            )
    if display_name_en is not None and not GATEWAY_DISPLAY_NAME_EN_PATTERN.fullmatch(display_name_en):
        errors["display_name_en"] = ValidationError(
            _("Use an English letter first, followed by letters, digits, spaces or hyphens."), code="invalid"
        )
    if errors:
        raise ValidationError(errors)
    return display_name, display_name_en


def validate_gateway_names(*, name, display_name, display_name_en, gateways):
    """检查默认名、英文最终展示名，以及它们与其他网关 name 的双向冲突。

    gateways 必须覆盖所有租户、状态和类别，仅排除当前网关；权限检查由调用方完成。
    返回去除首尾空白后的原始展示名，lower() 只用于比较，不改变保存的大小写。
    """
    display_name, display_name_en = normalize_gateway_names(name, display_name, display_name_en)
    display_name_lower = display_name.lower()
    # 英文页比较最终展示值：e.g. display_name="资产平台", display_name_en=None 时回退到“资产平台”。
    effective_display_name_en_lower = (display_name_en if display_name_en is not None else display_name).lower()
    name_lower = name.lower()
    # 回退值冲突时应报在 display_name 上，而不是让用户修改尚未配置的 display_name_en。
    english_error_field = "display_name_en" if display_name_en is not None else "display_name"

    # 先由 SQL 筛选可能冲突的网关，避免把全部网关名称读入 Python。
    # 展示名已在写入时 strip；MySQL 的 iexact 使用项目约定的大小写不敏感排序规则，
    # 不对列套 LOWER()/TRIM()，以便利用现有索引。下面的条件按 OR 合并。
    matches = Q()
    for field, values in (
        # 当前展示名不能冒用其他网关的 name，e.g. display_name="bk-cmdb" 与其他 name="bk-cmdb" 冲突。
        ("name", {display_name_lower, effective_display_name_en_lower}),
        # 其他默认名既用于默认页，也可能是英文页的回退值，还不能与当前 name 重名。
        ("display_name", {name_lower, display_name_lower, effective_display_name_en_lower}),
        # 其他英文名只需匹配当前 name 或英文最终展示名；单纯与当前默认名重叠是允许的。
        ("display_name_en", {name_lower, effective_display_name_en_lower}),
    ):
        for value in sorted(values):
            matches |= Q(**{f"{field}__iexact": value})
    candidates = gateways.filter(matches)
    errors = {}

    # SQL 命中不一定代表冲突，还要判断语言和回退关系。
    # e.g. 已有网关 display_name="Asset Hub", display_name_en="Inventory"；
    # 当前网关 display_name="新平台", display_name_en="Asset Hub"。
    # SQL 会命中已有默认名，但默认页和英文页各自都不重名，因此允许保存。
    for other_name, other_display_name, other_display_name_en in candidates.values_list(
        "name", "display_name", "display_name_en"
    ).iterator():
        other_name_lower = other_name.lower()
        other_display_name_lower = other_display_name.lower()
        other_effective_display_name_en_lower = (
            other_display_name_en.lower() if other_display_name_en is not None else other_display_name_lower
        )
        # 同一语言页面的最终展示名必须唯一，包括英文名未配置时的回退。
        if display_name_lower == other_display_name_lower:
            errors["display_name"] = ValidationError(
                _("This display name is already in use."), code=GatewayNameConflictCode.UNIQUE
            )
        if effective_display_name_en_lower == other_effective_display_name_en_lower:
            errors[english_error_field] = ValidationError(
                _("This English display name or its fallback is already in use."),
                code=GatewayNameConflictCode.EFFECTIVE_EN_CONFLICT,
            )
        # 展示名与 name 双向互斥：既不能用别人的 name 展示，也不能注册别人已使用的展示名作为 name。
        for field, value in (
            ("display_name", display_name_lower),
            (english_error_field, effective_display_name_en_lower),
        ):
            if value == other_name_lower:
                errors[field] = ValidationError(
                    _("This display name conflicts with a gateway's technical name."),
                    code=GatewayNameConflictCode.TECHNICAL_NAME_CONFLICT,
                )
        if name_lower in (other_display_name_lower, other_effective_display_name_en_lower):
            errors["name"] = ValidationError(
                _("This technical name conflicts with a gateway's display name."),
                code=GatewayNameConflictCode.DISPLAY_NAME_CONFLICT,
            )
    if errors:
        raise ValidationError(errors)
    return display_name, display_name_en
