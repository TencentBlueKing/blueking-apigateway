"""Shared naming validation and transport errors for gateway write APIs."""

import re
from contextlib import contextmanager

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apigateway.core.gateway_name import validate_gateway_names
from apigateway.core.models import Gateway


def validate_sync_gateway_names(data, instance=None):
    # Do not turn an omitted default name into an explicit update.
    current = Gateway.objects.values("name", "display_name").get(pk=instance.pk) if instance is not None else {}
    current_default = current.get("display_name")
    default, english = validate_gateway_names(
        name=current.get("name", data["name"]),
        display_name=data.get("display_name", current_default),
        display_name_en=data.get("display_name_en"),
        gateways=Gateway.objects.exclude(pk=instance.pk if instance is not None else None),
    )
    if "display_name" in data:
        data["display_name"] = default
    if "display_name_en" in data:
        data["display_name_en"] = english


def validate_web_gateway_names(data, instance=None):
    """Web writes modify the default field and preserve the stored English field."""
    if instance is not None and "display_name" not in data:
        return
    current = Gateway.objects.values("name", "display_name_en").get(pk=instance.pk) if instance is not None else {}
    default, _ = validate_gateway_names(
        name=current.get("name", data.get("name")),
        display_name=data.get("display_name"),
        display_name_en=current.get("display_name_en"),
        gateways=Gateway.objects.exclude(pk=instance.pk if instance is not None else None),
    )
    data["display_name"] = default


def _display_name_unique_field(exc):
    message = str(exc)
    for field in ("display_name", "display_name_en"):
        if message == f"UNIQUE constraint failed: core_api.{field}":
            return field
    cause = exc.__cause__ or exc
    if not cause.args or cause.args[0] != 1062 or len(cause.args) < 2:
        return None
    match = re.search(r"for key ['`]([^'`]+)['`]$", str(cause.args[1]))
    if not match:
        return None
    key = match[1]
    if key in ("core_api.display_name", "core_api.display_name_en"):
        return key.removeprefix("core_api.")
    key = key.removeprefix("core_api.")
    match = re.fullmatch(r"core_api_(display_name_en|display_name)_[0-9a-f]{8}_uniq", key)
    return match[1] if match else None


@contextmanager
def gateway_name_validation_errors():
    try:
        yield
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message_dict) from exc
    except IntegrityError as exc:
        field = _display_name_unique_field(exc)
        if field is None:
            raise
        raise serializers.ValidationError({field: _("This display name is already in use.")}) from exc
