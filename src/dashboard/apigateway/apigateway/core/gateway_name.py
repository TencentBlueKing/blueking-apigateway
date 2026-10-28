"""Gateway display-name normalization and global, case-insensitive checks.

Column indexes guarantee column uniqueness. Cross-field checks intentionally do
not serialize writers and therefore do not guarantee uniqueness under races.
"""

import re
from enum import StrEnum

from django.core.exceptions import ValidationError
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
    display_name = (display_name or "").strip() or name
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
    """Validate a final candidate against an unfiltered queryset excluding self.

    Return normalized raw display fields. Callers own permission checks and must
    pass all gateways, regardless of tenant, status, kind or visibility.
    """
    display_name, display_name_en = normalize_gateway_names(name, display_name, display_name_en)
    default = display_name.strip().casefold()
    english = (display_name_en if display_name_en is not None else display_name).strip().casefold()
    technical = name.strip().casefold()
    english_field = "display_name_en" if display_name_en is not None else "display_name"
    errors = {}
    for other_name, other_display, other_en in gateways.values_list(
        "name", "display_name", "display_name_en"
    ).iterator():
        other_technical = other_name.strip().casefold()
        other_default = other_display.strip().casefold()
        other_english = other_en.strip().casefold() if other_en is not None else other_default
        if default == other_default:
            errors["display_name"] = ValidationError(
                _("This display name is already in use."), code=GatewayNameConflictCode.UNIQUE
            )
        if english == other_english:
            errors[english_field] = ValidationError(
                _("This English display name or its fallback is already in use."),
                code=GatewayNameConflictCode.EFFECTIVE_EN_CONFLICT,
            )
        for field, value in (("display_name", default), (english_field, english)):
            if value == other_technical:
                errors[field] = ValidationError(
                    _("This display name conflicts with a gateway's technical name."),
                    code=GatewayNameConflictCode.TECHNICAL_NAME_CONFLICT,
                )
        if technical in (other_default, other_english):
            errors["name"] = ValidationError(
                _("This technical name conflicts with a gateway's display name."),
                code=GatewayNameConflictCode.DISPLAY_NAME_CONFLICT,
            )
    if errors:
        raise ValidationError(errors)
    return display_name, display_name_en
