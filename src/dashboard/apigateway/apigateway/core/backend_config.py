from copy import deepcopy
from typing import Any

from apigateway.core.backend_config_schema import BackendConfigValidationError, validate_backend_config
from apigateway.core.constants import AI_BACKEND_BUILTIN_PROVIDERS, BackendKindEnum
from apigateway.utils.crypto import get_crypto


def _get_headers(config: dict[str, Any]) -> dict[str, str]:
    return config["instances"][0].get("auth", {}).get("header", {})


def _validate_unique_headers(headers: dict[str, str]) -> None:
    normalized: set[str] = set()
    for key in headers:
        normalized_key = key.casefold()
        if normalized_key in normalized:
            raise BackendConfigValidationError(f"duplicate header: {key}", "$.instances[0].auth.header")
        normalized.add(normalized_key)


def _validate_provider(instance: dict[str, Any]) -> None:
    provider = instance["provider"]
    headers = instance.get("auth", {}).get("header", {})
    authorization = next((value for key, value in headers.items() if key.casefold() == "authorization"), "")
    if provider in AI_BACKEND_BUILTIN_PROVIDERS:
        if not authorization:
            raise BackendConfigValidationError("Authorization header is required", "$.instances[0].auth.header")
        if "override" in instance:
            raise BackendConfigValidationError("override is not allowed", "$.instances[0].override")
    elif "override" not in instance:
        raise BackendConfigValidationError("override.endpoint is required", "$.instances[0].override")


def _decrypt_secret(value: str, key: str) -> str:
    try:
        plaintext = get_crypto().decrypt(value)
    except Exception as err:
        raise BackendConfigValidationError(f"failed to decrypt header: {key}", "$.instances[0].auth.header") from err
    return plaintext.decode() if isinstance(plaintext, bytes) else plaintext


def _mask_secret(value: str) -> str:
    if len(value) < 4:
        return "****"
    return f"{value[:2]}****{value[-2:]}"


def _is_masked_secret(value: str) -> bool:
    return value == "****" or (len(value) == 8 and value[2:6] == "****")


def _merge_headers(config: dict[str, Any], existing_config: dict[str, Any] | None) -> None:
    instance = config["instances"][0]
    incoming_auth = instance.get("auth")
    header_was_provided = incoming_auth is not None and "header" in incoming_auth
    existing_headers = _get_headers(existing_config) if existing_config else {}

    if not header_was_provided:
        if existing_headers:
            instance.setdefault("auth", {})["header"] = deepcopy(existing_headers)
        return

    incoming_headers = incoming_auth["header"]
    _validate_unique_headers(incoming_headers)
    existing_by_normalized_key = {key.casefold(): (key, value) for key, value in existing_headers.items()}
    merged_headers = {}
    for key, value in incoming_headers.items():
        existing = existing_by_normalized_key.get(key.casefold())
        if existing is None:
            merged_headers[key] = value
            continue

        existing_key, existing_value = existing
        if value == existing_value:
            merged_headers[existing_key] = existing_value
            continue

        try:
            existing_plaintext = _decrypt_secret(existing_value, existing_key)
        except BackendConfigValidationError:
            if _is_masked_secret(value):
                raise
            merged_headers[key] = value
            continue

        if value == existing_plaintext or value == _mask_secret(existing_plaintext):
            merged_headers[existing_key] = existing_value
            continue
        if _is_masked_secret(value):
            raise BackendConfigValidationError(
                f"masked header does not match existing secret: {key}", "$.instances[0].auth.header"
            )

        merged_headers[key] = value
    incoming_auth["header"] = merged_headers


def _encrypt_headers(config: dict[str, Any], existing_config: dict[str, Any] | None) -> None:
    crypto = get_crypto()
    existing_headers = _get_headers(existing_config) if existing_config else {}
    existing_values = {key.casefold(): value for key, value in existing_headers.items()}
    headers = _get_headers(config)
    for key, value in headers.items():
        if existing_values.get(key.casefold()) == value:
            continue
        headers[key] = crypto.encrypt(value)


def prepare_backend_config(
    kind: str, config: dict[str, Any], existing_config: dict[str, Any] | None = None
) -> dict[str, Any]:
    prepared = deepcopy(config)
    validate_backend_config(kind, prepared)
    if kind == BackendKindEnum.STANDARD.value:
        return prepared

    _merge_headers(prepared, existing_config)
    _validate_unique_headers(_get_headers(prepared))
    _validate_provider(prepared["instances"][0])
    _encrypt_headers(prepared, existing_config)
    return prepared


def has_backend_config_changed(kind: str, config: dict[str, Any], existing_config: dict[str, Any]) -> bool:
    if kind == BackendKindEnum.STANDARD.value:
        return config != existing_config

    comparison_config = deepcopy(config)
    _merge_headers(comparison_config, existing_config)
    return comparison_config != existing_config


def mask_backend_config(kind: str, config: dict[str, Any]) -> dict[str, Any]:
    if kind != BackendKindEnum.AI.value:
        return deepcopy(config)

    masked = deepcopy(config)
    headers = _get_headers(masked)
    for key, value in headers.items():
        try:
            headers[key] = _mask_secret(_decrypt_secret(value, key))
        except BackendConfigValidationError:
            headers[key] = "****"
    return masked


def decrypt_ai_backend_config(config: dict[str, Any]) -> dict[str, Any]:
    decrypted = deepcopy(config)
    for key, value in _get_headers(decrypted).items():
        _get_headers(decrypted)[key] = _decrypt_secret(value, key)
    return decrypted
