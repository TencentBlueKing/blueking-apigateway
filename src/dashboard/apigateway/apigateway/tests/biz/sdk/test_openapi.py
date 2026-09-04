import json
from dataclasses import asdict, replace
from types import MappingProxyType, SimpleNamespace

from apigateway.biz.sdk.config import SDKLanguageConfig
from apigateway.biz.sdk.openapi import build_sdk_openapi, calculate_input_fingerprint, dump_sdk_openapi
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
    settings.SDK_GENERATION["server_url_template"] = "https://{gateway_name}.example.com/{stage_name}"
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

    tool_versions = MappingProxyType({"openapi-generator": "7.23.0"})
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
    settings.SDK_GENERATION["server_url_template"] = "https://{gateway_name}.example.com/{stage_name}"
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
