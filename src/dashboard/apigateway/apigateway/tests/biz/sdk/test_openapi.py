import json
from types import MappingProxyType, SimpleNamespace

from apigateway.biz.sdk.config import SDKLanguageConfig
from apigateway.biz.sdk.openapi import build_sdk_openapi, calculate_input_fingerprint, dump_sdk_openapi


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
