from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jsonschema import Draft202012Validator

from apigateway.core.constants import BackendKindEnum

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class BackendConfigValidationError(ValueError):
    def __init__(self, message: str, path: str):
        super().__init__(f"{path}: {message}")
        self.message = message
        self.path = path


STANDARD_BACKEND_CONFIG_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["type", "timeout", "loadbalance", "hosts"],
    "properties": {
        "type": {"const": "node"},
        "timeout": {"type": "integer", "minimum": 1},
        "loadbalance": {"enum": ["roundrobin", "weighted-roundrobin", "chash", "ewma", "least_conn"]},
        "hash_on": {"enum": ["vars", "header", "cookie", "vars_combinations"]},
        "key": {"type": "string"},
        "hosts": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["scheme", "host"],
                "properties": {
                    "scheme": {"enum": ["http", "https", "grpc", "grpcs"]},
                    "host": {"type": "string"},
                    "weight": {"type": "integer", "minimum": 1},
                },
            },
        },
        "checks": {"type": ["object", "null"]},
    },
}

AI_BACKEND_CONFIG_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["timeout", "instances"],
    "properties": {
        "timeout": {"type": "integer", "minimum": 1},
        "instances": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "provider", "weight", "options"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "provider": {"enum": ["openai", "deepseek", "openai-compatible"]},
                    "weight": {"const": 1},
                    "auth": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "header": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            }
                        },
                    },
                    "options": {
                        "type": "object",
                        "additionalProperties": True,
                        "required": ["model"],
                        "properties": {"model": {"type": "string", "minLength": 1}},
                    },
                    "override": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["endpoint"],
                        "properties": {"endpoint": {"type": "string", "minLength": 1}},
                    },
                },
            },
        },
    },
}

Draft202012Validator.check_schema(STANDARD_BACKEND_CONFIG_SCHEMA)
Draft202012Validator.check_schema(AI_BACKEND_CONFIG_SCHEMA)

_VALIDATORS = {
    BackendKindEnum.STANDARD.value: Draft202012Validator(STANDARD_BACKEND_CONFIG_SCHEMA),
    BackendKindEnum.AI.value: Draft202012Validator(AI_BACKEND_CONFIG_SCHEMA),
}


def _format_json_path(path: Sequence[Any]) -> str:
    result = "$"
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


def validate_backend_config(kind: str, config: Mapping[str, Any]) -> None:
    try:
        validator = _VALIDATORS[kind]
    except KeyError:
        raise ValueError(f"unsupported backend kind: {kind}") from None

    error = next(iter(validator.iter_errors(config)), None)
    if error is not None:
        raise BackendConfigValidationError(error.message, _format_json_path(error.absolute_path))
