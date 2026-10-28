"""Normalize gateway display names and check each field independently.

Prechecks provide validation errors; each column's unique index enforces uniqueness.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

GATEWAY_DISPLAY_NAME_MAX_LENGTH = 64
GATEWAY_DISPLAY_NAME_EN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9 -]*")


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
    """两个展示字段各自查重，不检查跨字段、英文回退或与 name 的重名。

    gateways 覆盖全部租户、状态和类别，仅排除当前网关；权限检查由调用方完成。
    e.g. A.display_name="Shared"、B.display_name_en="Shared" 可以共存；
    但 A.display_name="Shared"、B.display_name="shared" 不允许。
    name 仅用于默认展示名为空时的回填，不参与查重。
    """
    display_name, display_name_en = normalize_gateway_names(name, display_name, display_name_en)
    errors = {}
    for field, value in (("display_name", display_name), ("display_name_en", display_name_en)):
        # NULL 英文名可共存；直接查询同字段，由 MySQL 的 _ci 排序规则忽略大小写。
        if value is not None and gateways.filter(**{f"{field}__iexact": value}).exists():
            errors[field] = ValidationError(_("This display name is already in use."), code="unique")
    if errors:
        raise ValidationError(errors)
    return display_name, display_name_en
