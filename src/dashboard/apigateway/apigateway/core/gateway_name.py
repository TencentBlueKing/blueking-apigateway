"""Validate each gateway display-name field independently."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

GATEWAY_DISPLAY_NAME_MAX_LENGTH = 64
GATEWAY_DISPLAY_NAME_EN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9 -]*")


def _validate_length(field, value):
    if len(value) > GATEWAY_DISPLAY_NAME_MAX_LENGTH:
        raise ValidationError(
            {
                field: ValidationError(
                    _("Ensure this value has at most %(max_length)s characters."),
                    code="max_length",
                    params={"max_length": GATEWAY_DISPLAY_NAME_MAX_LENGTH},
                )
            }
        )


def validate_display_name(value, *, name, gateways=None):
    """处理 display_name；为空时使用 name，只查询 display_name 是否重名。

    gateways 不传时只处理格式，供 GatewaySaver 保存前使用。
    查重时由调用方传入全部网关并排除自身。
    """
    value = (value or "").strip() or (name or "").strip()
    if not value:
        raise ValidationError({"display_name": ValidationError(_("This display name cannot be empty."), code="blank")})
    _validate_length("display_name", value)
    if gateways is not None and gateways.filter(display_name__iexact=value).exists():
        raise ValidationError(
            {"display_name": ValidationError(_("This display name is already in use."), code="unique")}
        )
    return value


def validate_display_name_en(value, *, gateways=None):
    """处理 display_name_en；为空时返回 None，只查询 display_name_en 是否重名。"""
    value = (value or "").strip() or None
    if value is None:
        return None
    if not GATEWAY_DISPLAY_NAME_EN_PATTERN.fullmatch(value):
        raise ValidationError(
            {
                "display_name_en": ValidationError(
                    _("Use an English letter first, followed by letters, digits, spaces or hyphens."),
                    code="invalid",
                )
            }
        )
    _validate_length("display_name_en", value)
    if gateways is not None and gateways.filter(display_name_en__iexact=value).exists():
        raise ValidationError(
            {"display_name_en": ValidationError(_("This display name is already in use."), code="unique")}
        )
    return value
