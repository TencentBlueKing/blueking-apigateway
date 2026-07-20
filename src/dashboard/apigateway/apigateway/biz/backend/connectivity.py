import json
import logging
import socket
import time
from ipaddress import ip_address
from urllib.parse import urlsplit

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter

from apigateway.common.security import is_forbidden_host
from apigateway.core.constants import AIBackendProviderEnum

logger = logging.getLogger(__name__)

AI_PROVIDER_MODELS_ENDPOINTS = {
    AIBackendProviderEnum.OPENAI.value: "https://api.openai.com/v1/models",
    AIBackendProviderEnum.DEEPSEEK.value: "https://api.deepseek.com/models",
}
CONNECT_TIMEOUT_SECONDS = 10.0
MAX_TOTAL_TIMEOUT_SECONDS = 30.0
MIN_TOTAL_TIMEOUT_SECONDS = 1.0
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_MODELS = 1000
RESPONSE_CHUNK_SIZE = 64 * 1024


class AIBackendEndpointError(ValueError):
    pass


class AIBackendConnectivityError(Exception):
    pass


class _PinnedAddressAdapter(HTTPAdapter):
    def __init__(self, address: str, hostname: str, host_header: str):
        self._address = address
        self._hostname = hostname
        self._host_header = host_header
        super().__init__()

    def build_connection_pool_key_attributes(self, request, verify, cert=None):
        host_params, pool_kwargs = super().build_connection_pool_key_attributes(request, verify, cert)
        host_params["host"] = self._address
        if urlsplit(request.url).scheme == "https":
            pool_kwargs["assert_hostname"] = self._hostname
            pool_kwargs["server_hostname"] = self._hostname
        return host_params, pool_kwargs

    def add_headers(self, request, **kwargs):
        request.headers["Host"] = self._host_header


def get_ai_backend_model_ids(config: dict) -> list[str]:
    instance = config["instances"][0]
    provider = instance["provider"]
    endpoint = AI_PROVIDER_MODELS_ENDPOINTS.get(provider)
    resolved_address = None
    if endpoint is None:
        endpoint = config["model_endpoint"]
        resolved_address = _resolve_endpoint(endpoint)

    headers = {
        key: value
        for key, value in instance.get("auth", {}).get("header", {}).items()
        if key.casefold() not in {"host", "content-length"}
    }
    total_timeout = max(min(config["timeout"] / 1000, MAX_TOTAL_TIMEOUT_SECONDS), MIN_TOTAL_TIMEOUT_SECONDS)
    connect_timeout = min(CONNECT_TIMEOUT_SECONDS, total_timeout / 2)
    timeout = (connect_timeout, total_timeout - connect_timeout)
    deadline = time.monotonic() + total_timeout

    adapter = None
    adapter_scheme = None
    if resolved_address is not None:
        parsed = urlsplit(endpoint)
        if parsed.hostname is None:
            raise AIBackendEndpointError("model provider hostname is required")
        adapter = _PinnedAddressAdapter(resolved_address, parsed.hostname, parsed.netloc)
        adapter_scheme = parsed.scheme

    session = requests.Session()
    session.trust_env = False
    if adapter is not None:
        session.mount(f"{adapter_scheme}://", adapter)

    response = None
    try:
        response = session.get(
            endpoint,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )
        if not 200 <= response.status_code < 300:
            raise ValueError("model provider returned a non-2xx response")

        data = json.loads(_read_response(response, deadline))["data"]
        if not isinstance(data, list):
            raise TypeError("model data must be a list")
        if len(data) > MAX_MODELS:
            raise ValueError("model data contains too many items")

        models = [item["id"] for item in data if isinstance(item, dict) and isinstance(item.get("id"), str)]
        if len(models) != len(data):
            raise ValueError("model data item must contain a string id")
        return models
    except (KeyError, TypeError, ValueError, requests.RequestException) as err:
        sanitized_error = AIBackendConnectivityError(type(err).__name__)
        logger.warning(
            "failed to test AI backend connectivity: provider=%s error_type=%s",
            provider,
            type(err).__name__,
            exc_info=(AIBackendConnectivityError, sanitized_error, err.__traceback__),
        )
        raise AIBackendConnectivityError from err
    finally:
        if response is not None:
            response.close()
        session.close()


def _resolve_endpoint(endpoint: str) -> str:
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

    forbidden_hosts = {str(host).casefold() for host in settings.FORBIDDEN_HOSTS}
    if (
        not addresses
        or hostname.casefold() in forbidden_hosts
        or is_forbidden_host(f"{hostname}:{port}")
        or any(
            address.is_link_local
            or address.is_loopback
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
            or str(address).casefold() in forbidden_hosts
            for address in addresses
        )
    ):
        raise AIBackendEndpointError("model provider host resolves to a forbidden address")

    return str(addresses[0])


def _read_response(response, deadline: float) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length is not None and int(content_length) > MAX_RESPONSE_BYTES:
        raise ValueError("model provider response is too large")

    content = bytearray()
    for chunk in response.iter_content(chunk_size=RESPONSE_CHUNK_SIZE):
        if time.monotonic() > deadline:
            raise ValueError("model provider response exceeded the deadline")
        content.extend(chunk)
        if len(content) > MAX_RESPONSE_BYTES:
            raise ValueError("model provider response is too large")
    return bytes(content)
