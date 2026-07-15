from typing import Any

from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from apigateway.core.backend_config import AIBackendConfig, mask_header_value


def restore_masked_header_values(config: dict[str, Any], existing_config: dict[str, Any] | None) -> None:
    if not existing_config or not config.get("instances") or not existing_config.get("instances"):
        return

    headers = config["instances"][0].get("auth", {}).get("header", {})
    existing_headers = {
        key.casefold(): value
        for key, value in existing_config["instances"][0].get("auth", {}).get("header", {}).items()
    }
    for key, value in headers.items():
        existing_value = existing_headers.get(key.casefold())
        if existing_value is not None and value == mask_header_value(existing_value):
            headers[key] = existing_value


def validate_ai_backend_config(data: Any) -> dict[str, Any]:
    try:
        return AIBackendConfig.model_validate(data).to_config()
    except PydanticValidationError as err:
        errors: dict[str, list[str]] = {}
        for error in err.errors():
            location = error["loc"]
            field = str(location[0]) if location else "non_field_errors"
            errors.setdefault(field, []).append(error["msg"])
        raise serializers.ValidationError(errors) from err
