"""Normalize gateway display names without querying the database."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

GATEWAY_DISPLAY_NAME_MAX_LENGTH = 64
GATEWAY_DISPLAY_NAME_EN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9 -]*")


def _validate_length(value):
    if len(value) > GATEWAY_DISPLAY_NAME_MAX_LENGTH:
        raise ValidationError(
            _("Ensure this value has at most %(max_length)s characters."),
            code="max_length",
            params={"max_length": GATEWAY_DISPLAY_NAME_MAX_LENGTH},
        )


def normalize_display_name(value, *, name):
    """去除首尾空白；为空时使用 name，如 None → bk-cmdb。"""
    value = (value or "").strip() or name.strip()
    if not value:
        raise ValidationError(_("This display name cannot be empty."), code="blank")
    _validate_length(value)
    return value


def normalize_display_name_en(value):
    """去除首尾空白；为空时返回 None，非空时校验英文名格式。"""
    value = (value or "").strip() or None
    if value is None:
        return None
    if not GATEWAY_DISPLAY_NAME_EN_PATTERN.fullmatch(value):
        raise ValidationError(
            _("Use an English letter first, followed by letters, digits, spaces or hyphens."),
            code="invalid",
        )
    _validate_length(value)
    return value
