import logging
import socket
from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

from apigateway.common.security import is_forbidden_host
from apigateway.components.http import http_get
from apigateway.core.ai_backend import get_ai_backend_provider_config

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_SECONDS = 30


class AIBackendEndpointError(ValueError):
    pass


class AIBackendConnectivityError(Exception):
    pass


class AIBackendModelEndpointRequiredError(AIBackendConnectivityError):
    pass


def _derive_models_endpoint(completion_endpoint: str) -> str:
    parsed = urlsplit(completion_endpoint)
    suffix = "/chat/completions"
    if not parsed.path.endswith(suffix):
        raise AIBackendModelEndpointRequiredError("model endpoint cannot be derived")
    path = f"{parsed.path.removesuffix(suffix)}/models"
    return urlunsplit(parsed._replace(path=path, fragment=""))


def _get_endpoint_pair(config: dict) -> tuple[str, str, bool]:
    instance = config["instances"][0]
    provider_config = get_ai_backend_provider_config(instance["provider"])
    if provider_config is not None:
        return provider_config.endpoint, provider_config.model_endpoint, False
    completion = instance["override"]["endpoint"]
    if model_endpoint := instance.get("model_endpoint"):
        return completion, model_endpoint, False
    return completion, _derive_models_endpoint(completion), True


def get_ai_backend_model_ids(config: dict) -> list[str]:
    instance = config["instances"][0]
    provider = instance["provider"]
    completion_endpoint, model_endpoint, inferred = _get_endpoint_pair(config)
    _resolve_endpoint(completion_endpoint)
    _resolve_endpoint(model_endpoint)

    headers = {
        key: value
        for key, value in instance.get("auth", {}).get("header", {}).items()
        if key.casefold() not in {"host", "content-length"}
    }

    try:
        ok, response = http_get(
            model_endpoint,
            {},
            headers=headers,
            timeout=HTTP_TIMEOUT_SECONDS,
            verify=True,
            allow_redirects=False,
        )
        if not ok:
            raise ValueError("model provider returned a non-2xx response")

        data = response["data"]
        if not isinstance(data, list):
            raise TypeError("model data must be a list")

        models = [item["id"] for item in data if isinstance(item, dict) and isinstance(item.get("id"), str)]
        if len(models) != len(data):
            raise ValueError("model data item must contain a string id")
        return models
    except (KeyError, TypeError, ValueError) as err:
        logger.warning(
            "failed to test AI backend connectivity: provider=%s error_type=%s inferred=%s",
            provider,
            type(err).__name__,
            inferred,
        )
        error_type = AIBackendModelEndpointRequiredError if inferred else AIBackendConnectivityError
        raise error_type from err


def _resolve_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    hostname = parsed.hostname
    if hostname is None:
        raise AIBackendEndpointError("model provider hostname is required")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        addresses = [
            ip_address(item[4][0])
            for item in socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        ]
    except OSError, ValueError:
        raise AIBackendEndpointError("model provider host cannot be resolved safely") from None

    host_with_port = f"[{hostname}]:{port}" if ":" in hostname else f"{hostname}:{port}"
    if (
        not addresses
        or is_forbidden_host(hostname)
        or is_forbidden_host(host_with_port)
        or any(
            address.is_link_local
            or address.is_loopback
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
            or is_forbidden_host(str(address))
            for address in addresses
        )
    ):
        raise AIBackendEndpointError("model provider host resolves to a forbidden address")
