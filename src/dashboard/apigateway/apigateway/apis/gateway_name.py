"""Web/Sync 输入语义及 HTTP 错误转换；core 负责展示名规则，service 负责 AI 技术名前缀。"""

import logging
from contextlib import contextmanager

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import serializers

from apigateway.common.error_codes import error_codes
from apigateway.core.gateway_name import validate_display_name, validate_display_name_en
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


def validate_sync_gateway_names(data, instance=None):
    gateways = Gateway.objects.exclude(pk=instance.pk if instance is not None else None)
    values = {}
    errors = {}
    for field in ("display_name", "display_name_en"):
        if field not in data and (instance is not None or field == "display_name_en"):
            continue
        try:
            if field == "display_name":
                value = validate_display_name(
                    data.get(field),
                    name=instance.name if instance is not None else data["name"],
                    gateways=gateways,
                )
            else:
                value = validate_display_name_en(data[field], gateways=gateways)
            if field in data:
                values[field] = value
        except DjangoValidationError as exc:
            errors.update(exc.error_dict)
    if errors:
        raise DjangoValidationError(errors)
    data.update(values)


def validate_web_gateway_names(data, instance=None):
    if instance is None or "display_name" in data:
        data["display_name"] = validate_display_name(
            data.get("display_name"),
            name=instance.name if instance is not None else data["name"],
            gateways=Gateway.objects.exclude(pk=instance.pk if instance is not None else None),
        )


@contextmanager
def gateway_name_validation_errors():
    try:
        yield
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message_dict) from exc
    except IntegrityError as exc:
        logger.exception("Failed to save gateway information")
        raise error_codes.UNKNOWN from exc
