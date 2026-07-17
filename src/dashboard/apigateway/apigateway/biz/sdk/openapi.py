"""Build the canonical OpenAPI document consumed by SDK generators."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import TYPE_CHECKING, Any

from django.conf import settings
from openapi_spec_validator import validate

from apigateway.service.resource_version import OpenAPIExportManager

if TYPE_CHECKING:
    from collections.abc import Mapping

    from apigateway.biz.sdk.config import SDKLanguageConfig
    from apigateway.core.models import ResourceVersion


def build_sdk_openapi(resource_version: ResourceVersion) -> dict[str, Any]:
    exporter = OpenAPIExportManager(
        api_version=resource_version.version,
        include_bk_apigateway_resource=False,
        title=resource_version.gateway.name,
        description=f"SDK for {resource_version.gateway.name}",
    )
    document = copy.deepcopy(exporter.get_resource_version_openapi(resource_version))
    server_url = settings.SDK_GENERATION["server_url_template"].replace(
        "{gateway_name}", resource_version.gateway.name
    )
    document["servers"] = [
        {
            "url": server_url,
            "variables": {"stage_name": {"default": "prod"}},
        }
    ]
    components = document.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["BkApiAuthorization"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-Bkapi-Authorization",
    }
    document["security"] = [{"BkApiAuthorization": []}]
    validate(document)
    return document


def dump_sdk_openapi(document: dict[str, Any]) -> str:
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode()) > settings.SDK_GENERATION["max_openapi_bytes"]:
        raise ValueError("SDK OpenAPI document exceeds the configured size limit")
    return encoded


def calculate_input_fingerprint(
    document: dict[str, Any],
    language_config: SDKLanguageConfig,
    tool_versions: Mapping[str, str],
) -> str:
    payload = {
        "openapi": document,
        "language_config": language_config.build_fingerprint_payload(),
        "tool_versions": dict(tool_versions),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
