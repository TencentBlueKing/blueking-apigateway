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
import copy
import json
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from apigateway.biz.sdk.config import SDKLanguageConfig
from apigateway.biz.sdk.openapi import (
    build_sdk_openapi,
    calculate_input_fingerprint,
    dump_sdk_openapi,
    sanitize_descriptions_for_codegen,
)
from apigateway.biz.sdk.toolchain import SDKToolchainIdentity


def _language_config(package_version="1.2.3"):
    return SDKLanguageConfig(
        language="python",
        generator_name="python",
        project_name="bkapi-demo",
        package_name="bkapi_demo",
        package_version=package_version,
        additional_properties={
            "packageName": "bkapi_demo",
            "packageVersion": package_version,
            "projectName": "bkapi-demo",
            "buildSystem": "poetry",
        },
        native_distributor=None,
    )


def test_build_sdk_openapi_adds_server_and_api_key(mocker, settings):
    resource_version = SimpleNamespace(version="1.2.3", gateway=SimpleNamespace(name="demo"), data=[])
    settings.SDK_SERVER_URL_TEMPLATE = "https://{gateway_name}.example.com/{stage_name}"
    mocker.patch(
        "apigateway.biz.sdk.openapi.OpenAPIExportManager.get_resource_version_openapi",
        return_value={
            "openapi": "3.0.1",
            "info": {"title": "demo", "version": "1.2.3"},
            "servers": [{"url": "/"}],
            "paths": {},
        },
    )

    document = build_sdk_openapi(resource_version)

    assert document["servers"] == [
        {
            "url": "https://demo.example.com/{stage_name}",
            "variables": {"stage_name": {"default": "prod"}},
        }
    ]
    assert document["components"]["securitySchemes"]["BkApiAuthorization"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-Bkapi-Authorization",
    }
    assert document["security"] == [{"BkApiAuthorization": []}]


def test_dump_and_fingerprint_are_canonical_and_config_sensitive():
    document = {
        "openapi": "3.0.1",
        "info": {"version": "1.2.3", "title": "demo"},
        "paths": {},
    }
    first = dump_sdk_openapi(document)
    second = dump_sdk_openapi(dict(reversed(list(document.items()))))

    assert first == second
    assert json.loads(first) == document

    tool_versions = SDKToolchainIdentity(
        openapi_generator="7.23.0",
        python="3.14.1",
        java="17.0.15",
        maven="3.9.9",
        go="1.24.4",
        node="22.17.0",
        npm="11.4.2",
        dependency_lock_sha256="a" * 64,
    )
    assert calculate_input_fingerprint(document, _language_config(), tool_versions) == calculate_input_fingerprint(
        document, _language_config(), tool_versions
    )
    assert calculate_input_fingerprint(document, _language_config(), tool_versions) != calculate_input_fingerprint(
        document, _language_config("1.2.4"), tool_versions
    )


def test_fingerprint_owns_every_toolchain_field_and_ignores_dictionary_order():
    document = {"openapi": "3.0.1", "info": {"title": "demo", "version": "1.2.3"}, "paths": {}}
    identity = SDKToolchainIdentity(
        openapi_generator="7.23.0",
        python="3.14.1",
        java="17.0.15",
        maven="3.9.9",
        go="1.24.4",
        node="22.17.0",
        npm="11.4.2",
        dependency_lock_sha256="a" * 64,
    )
    baseline = calculate_input_fingerprint(document, _language_config(), identity)

    for field_name in asdict(identity):
        changed = replace(identity, **{field_name: asdict(identity)[field_name] + "-changed"})
        assert calculate_input_fingerprint(document, _language_config(), changed) != baseline

    reordered_document = dict(reversed(list(document.items())))
    assert calculate_input_fingerprint(reordered_document, _language_config(), identity) == baseline


def test_build_sdk_openapi_keeps_public_and_private_resources_without_secrets(mocker, settings):
    resource_version = SimpleNamespace(version="1.2.3", gateway=SimpleNamespace(name="demo"), data=[])
    settings.SDK_SERVER_URL_TEMPLATE = "https://{gateway_name}.example.com/{stage_name}"
    settings.BKREPO_PASSWORD = "must-not-leak"
    mocker.patch(
        "apigateway.biz.sdk.openapi.OpenAPIExportManager.get_resource_version_openapi",
        return_value={
            "openapi": "3.0.1",
            "info": {"title": "demo", "version": "1.2.3"},
            "paths": {
                "/public": {"get": {"operationId": "public_resource", "responses": {"200": {"description": "OK"}}}},
                "/private": {"post": {"operationId": "private_resource", "responses": {"200": {"description": "OK"}}}},
            },
        },
    )

    document = build_sdk_openapi(resource_version)
    encoded = dump_sdk_openapi(document)

    assert set(document["paths"]) == {"/public", "/private"}
    assert "must-not-leak" not in encoded
    assert "Cookie" not in encoded


@pytest.mark.parametrize("parameter_level", ["path", "operation"])
def test_sdk_openapi_adds_only_missing_path_parameters(mocker, parameter_level):
    explicit = {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
    query = {"name": "child", "in": "query", "schema": {"type": "integer"}}
    operation = {"operationId": "get_child", "parameters": [query], "responses": {"200": {"description": "OK"}}}
    path_item = {"get": operation, "summary": "Children"}
    if parameter_level == "path":
        path_item["parameters"] = [explicit]
    else:
        operation["parameters"].append(explicit)
    exported = {
        "openapi": "3.0.1",
        "info": {"title": "demo", "version": "1.2.3"},
        "paths": {"/users/{id}/children/{child}": path_item},
    }
    original = copy.deepcopy(exported)
    mocker.patch("apigateway.biz.sdk.openapi.OpenAPIExportManager.get_resource_version_openapi", return_value=exported)
    resource_version = SimpleNamespace(version="1.2.3", gateway=SimpleNamespace(name="demo"))

    document = build_sdk_openapi(resource_version)

    result = document["paths"]["/users/{id}/children/{child}"]
    parameters = result.get("parameters", []) + result["get"]["parameters"]
    assert [p for p in parameters if p.get("in") == "path"] == [
        explicit,
        {"name": "child", "in": "path", "required": True, "description": "", "schema": {"type": "string"}},
    ]
    assert query in result["get"]["parameters"]
    assert exported == original


def test_sdk_openapi_without_schema_survives_deleted_backend(mocker):
    resource = {
        "id": 1,
        "name": "get_user",
        "description": "Get user",
        "path": "/users/{id}",
        "method": "GET",
        "contexts": {"resource_auth": {"config": "{}"}},
        "proxy": {"backend_id": 42, "config": "{}"},
    }
    original = copy.deepcopy(resource)
    resource_version = SimpleNamespace(
        id=2, version="1.2.3", gateway=SimpleNamespace(id=3, name="demo"), data=[resource]
    )
    mocker.patch("apigateway.service.resource_version.openapi_export.get_backend_id_to_instance", return_value={})
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_gateway_resource_id_to_labels", return_value={}
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_resource_id_to_schema_by_resource_version",
        return_value={},
    )

    document = build_sdk_openapi(resource_version)

    operation = document["paths"]["/users/{id}"]["get"]
    assert operation["parameters"] == [
        {"name": "id", "in": "path", "required": True, "description": "", "schema": {"type": "string"}},
    ]
    assert "x-bk-apigateway-resource" not in operation
    assert resource == original


class TestSanitizeDescriptionsForCodegen:
    """Verify that user-controlled descriptive text is stripped from the
    OpenAPI copy sent to code generators, while data-model fields and
    structural values are preserved."""

    @staticmethod
    def _minimal_doc(**paths_kwargs):
        doc = {
            "openapi": "3.0.1",
            "info": {"title": "demo", "version": "1.0.0", "description": "kept"},
            "paths": {},
        }
        doc["paths"].update(paths_kwargs)
        return doc

    def test_operation_descriptions_cleared(self):
        doc = self._minimal_doc(
            **{
                "/users": {
                    "get": {
                        "operationId": "list_users",
                        "summary": "List users",
                        "description": "Returns all users",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        )
        sanitize_descriptions_for_codegen(doc)

        op = doc["paths"]["/users"]["get"]
        assert op["summary"] == ""
        assert op["description"] == ""
        assert op["operationId"] == "list_users"
        assert doc["paths"]["/users"]["get"]["responses"]["200"]["description"] == ""

    def test_info_block_preserved(self):
        doc = self._minimal_doc()
        sanitize_descriptions_for_codegen(doc)
        assert doc["info"]["title"] == "demo"
        assert doc["info"]["description"] == "kept"

    def test_parameter_description_cleared(self):
        doc = self._minimal_doc(
            **{
                "/users/{id}": {
                    "get": {
                        "operationId": "get_user",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "description": "User ID",
                                "schema": {"type": "integer", "description": "int id"},
                            }
                        ],
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        )
        sanitize_descriptions_for_codegen(doc)

        param = doc["paths"]["/users/{id}"]["get"]["parameters"][0]
        assert param["name"] == "id"
        assert param["description"] == ""
        assert param["schema"]["description"] == ""
        assert param["schema"]["type"] == "integer"

    def test_request_body_description_cleared(self):
        doc = self._minimal_doc(
            **{
                "/users": {
                    "post": {
                        "operationId": "create_user",
                        "requestBody": {
                            "description": "User payload",
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "description": "User schema",
                                        "properties": {
                                            "name": {"type": "string", "description": "User name"},
                                            "description": {"type": "string", "description": "Bio"},
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            }
        )
        sanitize_descriptions_for_codegen(doc)

        rb = doc["paths"]["/users"]["post"]["requestBody"]
        assert rb["description"] == ""
        assert rb["required"] is True

        schema = rb["content"]["application/json"]["schema"]
        assert schema["description"] == ""
        assert schema["type"] == "object"

        # properties children: their description IS cleared (they are schema objects)
        assert schema["properties"]["name"]["description"] == ""
        assert schema["properties"]["name"]["type"] == "string"
        # the property *named* "description" must still exist as a property key
        assert "description" in schema["properties"]
        assert schema["properties"]["description"]["type"] == "string"

    def test_example_default_enum_preserved(self):
        doc = self._minimal_doc(
            **{
                "/items": {
                    "get": {
                        "operationId": "list_items",
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "description": "Filter by status",
                                "schema": {
                                    "type": "string",
                                    "description": "Status enum",
                                    "enum": ["active", "inactive"],
                                    "default": "active",
                                    "example": "active",
                                },
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Items list",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "array"},
                                        "example": [{"id": 1, "description": "First item", "summary": "Item one"}],
                                    }
                                },
                            }
                        },
                    }
                }
            }
        )
        sanitize_descriptions_for_codegen(doc)

        param_schema = doc["paths"]["/items"]["get"]["parameters"][0]["schema"]
        assert param_schema["enum"] == ["active", "inactive"]
        assert param_schema["default"] == "active"
        assert param_schema["example"] == "active"
        assert param_schema["description"] == ""

        example = doc["paths"]["/items"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
        assert example == [{"id": 1, "description": "First item", "summary": "Item one"}]

    def test_components_schemas_cleaned(self):
        doc = self._minimal_doc()
        doc["components"] = {
            "schemas": {
                "User": {
                    "type": "object",
                    "description": "A user",
                    "properties": {
                        "name": {"type": "string", "description": "User name"},
                        "role": {
                            "type": "string",
                            "description": "User role",
                            "enum": ["admin", "user"],
                            "default": "user",
                        },
                    },
                }
            },
            "securitySchemes": {
                "BkApiAuthorization": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Bkapi-Authorization",
                    "description": "BK auth header",
                }
            },
        }
        sanitize_descriptions_for_codegen(doc)

        user = doc["components"]["schemas"]["User"]
        assert user["description"] == ""
        assert user["type"] == "object"
        assert user["properties"]["name"]["description"] == ""
        assert user["properties"]["role"]["enum"] == ["admin", "user"]
        assert user["properties"]["role"]["default"] == "user"
        assert user["properties"]["role"]["description"] == ""

        # securitySchemes is explicitly skipped
        assert doc["components"]["securitySchemes"]["BkApiAuthorization"]["description"] == "BK auth header"

    def test_go_comment_injection_payload_neutralized(self):
        """Reproduce the Go comment-breakout attack vector:
        A description containing `*/` followed by `func init()` would escape
        a Go block comment and inject executable code.  After sanitization the
        description must be empty."""
        payload = '*/\n\nfunc init() { panic("injected") }\n\n/*'
        doc = self._minimal_doc(
            **{
                "/evil": {
                    "get": {
                        "operationId": "evil_op",
                        "description": payload,
                        "summary": payload,
                        "parameters": [
                            {"name": "q", "in": "query", "description": payload, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": payload}},
                    }
                }
            }
        )
        sanitize_descriptions_for_codegen(doc)

        op = doc["paths"]["/evil"]["get"]
        assert op["description"] == ""
        assert op["summary"] == ""
        assert op["parameters"][0]["description"] == ""
        assert op["responses"]["200"]["description"] == ""

    def test_js_comment_injection_payload_neutralized(self):
        """Reproduce the JS/TS comment-breakout vector (CVE-2026-23947 style)."""
        payload = '*/ }; require("child_process").execSync("id"); const a = { /*'
        doc = self._minimal_doc()
        doc["components"] = {
            "schemas": {
                "Evil": {
                    "type": "string",
                    "description": payload,
                    "enum": ["pwned"],
                }
            }
        }
        sanitize_descriptions_for_codegen(doc)

        assert doc["components"]["schemas"]["Evil"]["description"] == ""
        assert doc["components"]["schemas"]["Evil"]["enum"] == ["pwned"]

    def test_path_item_level_description_cleared(self):
        doc = self._minimal_doc(
            **{
                "/users": {
                    "summary": "Users resource",
                    "description": "Operations on users",
                    "get": {
                        "operationId": "list_users",
                        "responses": {"200": {"description": "OK"}},
                    },
                    "parameters": [{"name": "X-Request-Id", "in": "header", "description": "Correlation ID"}],
                }
            }
        )
        sanitize_descriptions_for_codegen(doc)

        pi = doc["paths"]["/users"]
        assert pi["summary"] == ""
        assert pi["description"] == ""
        assert pi["parameters"][0]["description"] == ""
        assert pi["parameters"][0]["name"] == "X-Request-Id"

    def test_build_sdk_openapi_integrates_sanitization(self, mocker, settings):
        """End-to-end: build_sdk_openapi must return a document with empty
        descriptions (except info block)."""
        resource_version = SimpleNamespace(version="1.2.3", gateway=SimpleNamespace(name="demo"), data=[])
        settings.SDK_SERVER_URL_TEMPLATE = "https://{gateway_name}.example.com/{stage_name}"
        mocker.patch(
            "apigateway.biz.sdk.openapi.OpenAPIExportManager.get_resource_version_openapi",
            return_value={
                "openapi": "3.0.1",
                "info": {"title": "demo", "version": "1.2.3", "description": "SDK for demo"},
                "servers": [{"url": "/"}],
                "paths": {
                    "/users": {
                        "get": {
                            "operationId": "list_users",
                            "description": "DANGEROUS */ func init() { panic(1) } /*",
                            "summary": "List all users",
                            "responses": {"200": {"description": "Success"}},
                        }
                    }
                },
            },
        )

        document = build_sdk_openapi(resource_version)

        op = document["paths"]["/users"]["get"]
        assert op["description"] == ""
        assert op["summary"] == ""
        assert op["operationId"] == "list_users"
        assert "DANGEROUS" not in json.dumps(document["paths"])
        # info is preserved (gateway-controlled, sanitize skips info block)
        assert document["info"]["description"] == "SDK for demo"
        assert document["info"]["title"] == "demo"
