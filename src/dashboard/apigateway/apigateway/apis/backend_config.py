from typing import Any

from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from apigateway.core.backend_config import AIBackendConfig


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
