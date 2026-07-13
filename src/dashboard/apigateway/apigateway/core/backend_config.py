from copy import deepcopy
from typing import Any

from apigateway.core.backend_config_schema import BackendConfigValidationError, validate_backend_config
from apigateway.core.constants import BackendKindEnum
from apigateway.utils.crypto import get_crypto

MASKED_SECRET = "******"
ENCRYPTED_SECRET_PREFIX = "bk-apigw-encrypted$"


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
    if provider in {"openai", "deepseek"}:
        if not authorization:
            raise BackendConfigValidationError("Authorization header is required", "$.instances[0].auth.header")
        if "override" in instance:
            raise BackendConfigValidationError("override is not allowed", "$.instances[0].override")
    elif "override" not in instance:
        raise BackendConfigValidationError("override.endpoint is required", "$.instances[0].override")


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
        if value != MASKED_SECRET:
            merged_headers[key] = value
            continue

        existing = existing_by_normalized_key.get(key.casefold())
        if existing is None:
            raise BackendConfigValidationError(
                f"masked secret has no existing value: {key}", "$.instances[0].auth.header"
            )
        merged_headers[existing[0]] = existing[1]
    incoming_auth["header"] = merged_headers


def _encrypt_headers(config: dict[str, Any]) -> None:
    crypto = get_crypto()
    headers = _get_headers(config)
    for key, value in headers.items():
        if value.startswith(ENCRYPTED_SECRET_PREFIX):
            continue
        headers[key] = f"{ENCRYPTED_SECRET_PREFIX}{crypto.encrypt(value)}"


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
    _encrypt_headers(prepared)
    return prepared


def mask_backend_config(kind: str, config: dict[str, Any]) -> dict[str, Any]:
    masked = deepcopy(config)
    if kind != BackendKindEnum.AI.value:
        return masked

    for key in _get_headers(masked):
        _get_headers(masked)[key] = MASKED_SECRET
    return masked


def decrypt_ai_backend_config(config: dict[str, Any]) -> dict[str, Any]:
    decrypted = deepcopy(config)
    crypto = get_crypto()
    for key, value in _get_headers(decrypted).items():
        if not value.startswith(ENCRYPTED_SECRET_PREFIX):
            raise BackendConfigValidationError(
                f"header value is missing encrypted envelope: {key}", "$.instances[0].auth.header"
            )
        try:
            plaintext = crypto.decrypt(value.removeprefix(ENCRYPTED_SECRET_PREFIX))
        except Exception as err:
            raise BackendConfigValidationError(
                f"failed to decrypt header: {key}", "$.instances[0].auth.header"
            ) from err
        decrypted_value = plaintext.decode() if isinstance(plaintext, bytes) else plaintext
        _get_headers(decrypted)[key] = decrypted_value
    return decrypted
