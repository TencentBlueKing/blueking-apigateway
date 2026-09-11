#
# TencentBlueKing is pleased to support the open source community by making
# BlueKing - APIGateway available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
"""Build the canonical OpenAPI document consumed by SDK generators.

Security: user-controlled text (description, summary, examples, …) is stripped
from the copy that reaches OpenAPI Generator so that code-generation templates
cannot turn it into executable code.  The original resource data and the API
documentation rendered for the gateway site are unaffected.

See also: CVE-2025-31115 (oapi-codegen Go comment injection),
CVE-2026-23947 (Orval JS comment breakout), CVE-2026-59860 (Kiota C# XML
doc-comment breakout).  OpenAPI Generator 7.23 Go templates use
``unescapedNotes`` which is vulnerable to the same class of attack.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import MutableMapping, MutableSequence
from typing import TYPE_CHECKING, Any

from django.conf import settings
from jsonschema_path import SchemaPath
from openapi_spec_validator.shortcuts import get_validator_cls

from apigateway.core.constants import HTTP_METHOD_CHOICES
from apigateway.service.resource_version import OpenAPIExportManager
from apigateway.utils.openapi import extract_openapi_parameters_from_path
from apigateway.utils.openapi_refs import UNSAFE_OPENAPI_REF_MESSAGE, validate_openapi_refs

if TYPE_CHECKING:
    from apigateway.biz.sdk.config import SDKLanguageConfig
    from apigateway.biz.sdk.toolchain import SDKToolchainIdentity
    from apigateway.core.models import ResourceVersion

# ---------------------------------------------------------------------------
# Keys whose *values* are free-form text that OpenAPI Generator may embed in
# generated code (comments, docstrings, annotations).  These are cleared on
# spec-level objects only — NOT inside ``properties`` / ``example`` / ``enum``
# / ``default`` where they are legitimate data-model field names or values.
# ---------------------------------------------------------------------------
_DESCRIPTIVE_KEYS = frozenset({"description", "summary", "title"})

# OpenAPI structural containers whose children are spec objects (not data).
_OBJECT_MAP_KEYS = frozenset(
    {
        "paths",
        "schemas",
        "responses",
        "parameters",
        "requestBodies",
        "headers",
        "links",
        "callbacks",
        "pathItems",
        "properties",
    }
)

# Keys whose values are opaque data that must NEVER be descended into.
_OPAQUE_KEYS = frozenset(
    {
        "example",
        "examples",
        "default",
        "enum",
        "const",
        "x-enum-varnames",
        "x-enumDescriptions",
        "externalDocs",
    }
)


def _clear_descriptive_keys(obj: MutableMapping[str, Any]) -> None:
    for key in _DESCRIPTIVE_KEYS:
        if key in obj:
            obj[key] = ""


def _sanitize_child(value: Any) -> None:
    if isinstance(value, MutableMapping):
        _sanitize_spec_object(value)
    elif isinstance(value, MutableSequence):
        for item in value:
            if isinstance(item, MutableMapping):
                _sanitize_spec_object(item)


def _sanitize_spec_object(obj: Any) -> None:
    """Recursively clear descriptive text from an OpenAPI spec object tree.

    Rules
    -----
    * ``description``, ``summary`` and ``title`` are set to ``""`` on every
      spec-level mapping (operation, parameter, schema, media-type, …).
    * Keys that represent *data values* are left untouched:
      ``example``, ``examples``, ``default``, ``enum``, ``const``,
      ``x-enum-varnames``, ``x-enumDescriptions``, ``externalDocs``.
    * ``properties`` is a name → schema map: the container itself is NOT
      cleared (property names may legitimately be ``description`` etc.),
      but each child schema IS recursed.
    * Sequences are iterated; non-mapping / non-sequence leaves are ignored.
    """
    if isinstance(obj, MutableSequence):
        _sanitize_child(obj)
        return
    if not isinstance(obj, MutableMapping):
        return

    _clear_descriptive_keys(obj)
    for key, value in obj.items():
        if key in _OPAQUE_KEYS:
            continue
        # ``properties`` is {propertyName: schemaObject}. Recurse into each
        # child schema without blanking the user-defined property names.
        if key == "properties" and isinstance(value, MutableMapping):
            for prop_schema in value.values():
                _sanitize_spec_object(prop_schema)
            continue
        _sanitize_child(value)


def _sanitize_path_item(path_item: MutableMapping[str, Any]) -> None:
    _sanitize_child(path_item.get("parameters"))
    for key, value in path_item.items():
        if key in ("parameters", *_DESCRIPTIVE_KEYS):
            continue
        if isinstance(value, MutableMapping):
            _sanitize_spec_object(value)
    _clear_descriptive_keys(path_item)


def _sanitize_components(components: MutableMapping[str, Any]) -> None:
    for section_key, section in components.items():
        if section_key == "securitySchemes" or not isinstance(section, MutableMapping):
            continue
        for obj in section.values():
            if isinstance(obj, MutableMapping):
                _sanitize_spec_object(obj)


def _reject_remote_ref(_uri: str) -> None:
    raise ValueError(UNSAFE_OPENAPI_REF_MESSAGE)


_SAFE_REF_HANDLERS = {
    "http": _reject_remote_ref,
    "https": _reject_remote_ref,
    "file": _reject_remote_ref,
}


def _validate_sdk_document(document: dict[str, Any]) -> None:
    """Validate the SDK spec without retrieving remote or file $ref targets."""
    validate_openapi_refs(document)
    validator_cls = get_validator_cls(document)
    spec_path = SchemaPath.from_dict(document, handlers=_SAFE_REF_HANDLERS)
    validator_cls(spec_path).validate()


def sanitize_descriptions_for_codegen(document: dict[str, Any]) -> None:
    """Strip free-form descriptive text from an OpenAPI document **in place**.

    This prevents code-generation templates from embedding user-controlled text
    into executable positions (Go ``init()`` via comment breakout, JS/TS
    comment-block escape, etc.).

    The ``info`` block is left as-is because ``build_sdk_openapi`` already
    overwrites ``info.title`` and ``info.description`` with gateway-controlled
    values.
    """
    paths = document.get("paths")
    if isinstance(paths, MutableMapping):
        for path_item in paths.values():
            if isinstance(path_item, MutableMapping):
                _sanitize_path_item(path_item)

    components = document.get("components")
    if isinstance(components, MutableMapping):
        _sanitize_components(components)


def build_sdk_openapi(resource_version: ResourceVersion) -> dict[str, Any]:
    exporter = OpenAPIExportManager(
        api_version=resource_version.version,
        include_bk_apigateway_resource=False,
        title=resource_version.gateway.name,
        description=f"SDK for {resource_version.gateway.name}",
    )
    document = copy.deepcopy(exporter.get_resource_version_openapi(resource_version))
    for path, path_item in document["paths"].items():
        inferred_parameters = extract_openapi_parameters_from_path(path)
        for method, _ in HTTP_METHOD_CHOICES:
            operation = path_item.get(method.lower())
            if operation is None:
                continue
            parameters = operation.get("parameters", [])
            declared_names = {
                parameter.get("name")
                for parameter in [*path_item.get("parameters", []), *parameters]
                if parameter.get("in") == "path"
            }
            missing = [parameter for parameter in inferred_parameters if parameter["name"] not in declared_names]
            if missing:
                operation["parameters"] = [*parameters, *missing]
    server_url = settings.SDK_SERVER_URL_TEMPLATE.replace("{gateway_name}", resource_version.gateway.name)
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

    sanitize_descriptions_for_codegen(document)

    _validate_sdk_document(document)
    return document


def dump_sdk_openapi(document: dict[str, Any]) -> str:
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode()) > settings.SDK_MAX_OPENAPI_BYTES:
        raise ValueError("SDK OpenAPI document exceeds the configured size limit")
    return encoded


def calculate_input_fingerprint(
    document: dict[str, Any],
    language_config: SDKLanguageConfig,
    tool_versions: SDKToolchainIdentity,
) -> str:
    payload = {
        "openapi": document,
        "language_config": language_config.build_fingerprint_payload(),
        "tool_versions": tool_versions.as_dict(),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
