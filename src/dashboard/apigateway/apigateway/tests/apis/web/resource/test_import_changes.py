#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
#
import json
from copy import deepcopy

import pytest
from ddf import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.openapi.models import OpenAPIResourceSchema
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginBindingSourceEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.core.constants import BackendKindEnum, GatewayKindEnum, ResourceKindEnum
from apigateway.core.models import Backend, Proxy


@pytest.fixture
def importable_resource(fake_resource):
    fake_resource.name = "get_users"
    fake_resource.method = "GET"
    fake_resource.path = "/users"
    fake_resource.match_subpath = False
    fake_resource.save()
    proxy = Proxy.objects.get(resource=fake_resource)
    proxy.config = {"method": "GET", "path": "/backend/users", "match_subpath": False, "timeout": 30}
    proxy.save()
    return fake_resource


def export_content(request_view, resource, file_type="json"):
    response = request_view(
        method="POST",
        view_name="resource.export",
        path_params={"gateway_id": resource.gateway_id},
        gateway=resource.gateway,
        data={"export_type": "all", "file_type": file_type},
    )
    assert response.status_code == 200
    return b"".join(response.streaming_content).decode(response.charset)


def check_content(request_view, resource, content, **options):
    return request_view(
        method="POST",
        view_name="resource.import.check",
        path_params={"gateway_id": resource.gateway_id},
        gateway=resource.gateway,
        data={"content": content, **options},
    )


@pytest.mark.parametrize("file_type", ["json", "yaml"])
def test_exported_resource_is_unchanged(request_view, importable_resource, file_type):
    resource = importable_resource
    initial_updated_time = resource.updated_time
    content = export_content(request_view, resource, file_type)
    response = check_content(request_view, resource, content, include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "unchanged"
    assert response.json()["data"][0]["id"] == resource.id
    resource.refresh_from_db()
    assert resource.updated_time == initial_updated_time


@pytest.mark.parametrize("options", [{}, {"include_change_type": False}])
def test_change_type_is_opt_in(request_view, importable_resource, options):
    content = export_content(request_view, importable_resource)
    response = check_content(request_view, importable_resource, content, **options)
    assert response.status_code == 200, response.json()
    assert "change_type" not in response.json()["data"][0]


def test_changed_description_is_update(request_view, importable_resource):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["description"] = "New description"
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"


def test_new_resource_is_add(request_view, importable_resource):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    operation = content["paths"].pop(resource.path)["get"]
    operation["operationId"] = "new_resource"
    content["paths"]["/new"] = {"get": operation}
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["id"] is None
    assert response.json()["data"][0]["change_type"] == "add"


@pytest.mark.parametrize(
    "field,value",
    [
        ("descriptionEn", "English description"),
        ("descriptionEn", ""),
        ("isPublic", False),
        ("allowApplyPermission", False),
        ("enableWebsocket", True),
    ],
)
def test_changed_resource_extension_is_update(request_view, importable_resource, field, value):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["x-bk-apigateway-resource"][field] = value
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"


@pytest.mark.parametrize(
    "field,value",
    [("userVerifiedRequired", False), ("appVerifiedRequired", False), ("oauth2PublicClientEnabled", True)],
)
def test_changed_authentication_is_update(request_view, importable_resource, field, value):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]["authConfig"][field] = value
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"


@pytest.mark.parametrize("field,value", [("path", "/another"), ("timeout", 0), ("method", "POST")])
def test_changed_backend_configuration_is_update(request_view, importable_resource, field, value):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]["backend"][field] = value
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"


def test_changed_backend_identity_is_update(request_view, importable_resource):
    resource = importable_resource
    G(Backend, gateway=resource.gateway, name="another_backend")
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]["backend"]["name"] = "another_backend"
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"


@pytest.mark.parametrize("change_labels", [False, True])
def test_labels_compare_as_a_set(request_view, importable_resource, change_labels):
    resource = importable_resource
    for name in ("first", "second"):
        label = G(APILabel, gateway=resource.gateway, name=name)
        G(ResourceLabel, resource=resource, api_label=label)
    content = json.loads(export_content(request_view, resource))
    operation = content["paths"][resource.path]["get"]
    operation["tags"].reverse()
    if change_labels:
        operation["tags"].append("third")
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == ("update" if change_labels else "unchanged")
    assert not APILabel.objects.filter(gateway=resource.gateway, name="third").exists()


@pytest.mark.parametrize("version", ["OpenAPIV2.0", "OpenAPIV3.0", "OpenAPIV3.1"])
@pytest.mark.parametrize("change_schema", [False, True])
def test_schema_round_trip_and_changes(request_view, importable_resource, version, change_schema):
    resource = importable_resource
    schema = {
        "version": version,
        "parameters": [{"name": "name", "in": "query", "schema": {"type": "string"}}],
        "none_schema": False,
    }
    stored = G(OpenAPIResourceSchema, resource=resource, schema=deepcopy(schema))
    content = json.loads(export_content(request_view, resource))
    if change_schema:
        content["paths"][resource.path]["get"]["parameters"][0]["schema"]["type"] = "integer"
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == ("update" if change_schema else "unchanged")
    stored.refresh_from_db()
    assert stored.schema == schema


@pytest.fixture
def resource_plugin(importable_resource):
    resource = importable_resource
    plugin_type = G(PluginType, code="test-import-plugin")
    config = G(PluginConfig, gateway=resource.gateway, type=plugin_type, yaml="enabled: true\ncount: 1\n")
    return G(
        PluginBinding,
        gateway=resource.gateway,
        scope_type=PluginBindingScopeEnum.RESOURCE.value,
        scope_id=resource.id,
        config=config,
        source=PluginBindingSourceEnum.YAML_IMPORT.value,
    )


@pytest.mark.parametrize("change_config", [False, True])
def test_plugin_configuration_compares_parsed_yaml(request_view, importable_resource, resource_plugin, change_config):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    plugins = content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]["pluginConfigs"]
    plugins[0]["yaml"] = '{"count": 1, "enabled": false}' if change_config else '{"count": 1, "enabled": true}'
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == ("update" if change_config else "unchanged")
    resource_plugin.config.refresh_from_db()
    assert resource_plugin.config.yaml == "enabled: true\ncount: 1\n"


@pytest.mark.parametrize(
    "source", [PluginBindingSourceEnum.YAML_IMPORT.value, PluginBindingSourceEnum.USER_CREATE.value]
)
@pytest.mark.parametrize("plugin_configs", [None, []])
def test_missing_plugins_follow_import_retention_rules(
    request_view, importable_resource, resource_plugin, source, plugin_configs
):
    resource = importable_resource
    resource_plugin.source = source
    resource_plugin.save()
    content = json.loads(export_content(request_view, resource))
    extension = content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]
    if plugin_configs is None:
        extension.pop("pluginConfigs")
    else:
        extension["pluginConfigs"] = plugin_configs
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    expected = "update" if source == PluginBindingSourceEnum.YAML_IMPORT.value else "unchanged"
    assert response.json()["data"][0]["change_type"] == expected
    assert PluginBinding.objects.filter(id=resource_plugin.id).exists()


def test_invalid_change_type_option_is_rejected(request_view, importable_resource):
    content = export_content(request_view, importable_resource)
    response = check_content(request_view, importable_resource, content, include_change_type="invalid")
    assert response.status_code == 400


@pytest.mark.parametrize("empty_proxy_config", [True, False])
def test_ai_resource_compares_empty_backend_config(request_view, importable_resource, empty_proxy_config):
    resource = importable_resource
    resource.gateway.kind = GatewayKindEnum.AI.value
    resource.gateway.save()
    backend = G(Backend, gateway=resource.gateway, name="ai_backend", kind=BackendKindEnum.AI.value)
    resource.kind = ResourceKindEnum.AI.value
    resource.method = "POST"
    resource.save()
    proxy = Proxy.objects.get(resource=resource)
    proxy.backend = backend
    if empty_proxy_config:
        proxy._config = "{}"
    proxy.save()
    content = export_content(request_view, resource)
    response = check_content(request_view, resource, content, include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == ("unchanged" if empty_proxy_config else "update")


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("transformHeaders", {}, "update"),
        ("transformHeaders", {"set": {"x-token": "test"}, "delete": ["x-old"]}, "update"),
        ("transformHeaders", None, "unchanged"),
        ("upstreams", {"loadbalance": "roundrobin", "hosts": [{"host": "https://example.com"}]}, "update"),
        ("upstreams", {}, "unchanged"),
        ("upstreams", None, "unchanged"),
    ],
)
def test_legacy_backend_migrations_are_updates(request_view, importable_resource, field, value, expected):
    resource = importable_resource
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]["backend"][field] = value
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == expected


@pytest.mark.parametrize(
    "stored_version,imported_version,expected_version",
    [("OpenAPIV3.0", "3.1.0", "OpenAPIV3.1"), ("OpenAPIV3.1", "3.0.1", "OpenAPIV3.0")],
)
def test_schema_version_only_change_is_excluded(
    request_view, importable_resource, stored_version, imported_version, expected_version
):
    resource = importable_resource
    stored = G(
        OpenAPIResourceSchema,
        resource=resource,
        schema={
            "version": stored_version,
            "parameters": [{"name": "name", "in": "query", "schema": {"type": "string"}}],
        },
    )
    content = json.loads(export_content(request_view, resource))
    content["openapi"] = imported_version
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "unchanged"
    assert response.json()["data"][0]["openapi_schema"]["version"] == expected_version
    stored.refresh_from_db()
    assert stored.schema["version"] == stored_version


@pytest.mark.parametrize(
    "first_version,second_version",
    [(None, "OpenAPIV3.1"), ("OpenAPIV3.0", "OpenAPIV3.1"), ("OpenAPIV3.1", "OpenAPIV3.0"), ("OpenAPIV3.1", None)],
)
def test_mixed_schema_versions_round_trip_is_unchanged(
    request_view, importable_resource, fake_resource1, first_version, second_version
):
    fake_resource1.name = "other_resource"
    fake_resource1.path = "/other"
    fake_resource1.save()
    for resource, version in ((importable_resource, first_version), (fake_resource1, second_version)):
        if version:
            G(
                OpenAPIResourceSchema,
                resource=resource,
                schema={
                    "version": version,
                    "parameters": [{"name": "name", "in": "query", "schema": {"type": "string"}}],
                },
            )
    content = export_content(request_view, importable_resource)
    response = check_content(request_view, importable_resource, content, include_change_type=True)
    assert response.status_code == 200, response.json()
    assert {item["id"]: item["change_type"] for item in response.json()["data"]} == {
        importable_resource.id: "unchanged",
        fake_resource1.id: "unchanged",
    }


@pytest.mark.parametrize("boolean_value", [True, False])
def test_plugin_boolean_to_number_is_update(request_view, importable_resource, resource_plugin, boolean_value):
    resource = importable_resource
    resource_plugin.config.yaml = json.dumps({"flags": {"enabled": boolean_value}})
    resource_plugin.config.save()
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["x-bk-apigateway-resource"]["pluginConfigs"][0]["yaml"] = json.dumps(
        {"flags": {"enabled": int(boolean_value)}}
    )
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"


@pytest.mark.parametrize("boolean_value", [True, False])
def test_schema_example_boolean_to_number_is_update(request_view, importable_resource, boolean_value):
    resource = importable_resource
    G(
        OpenAPIResourceSchema,
        resource=resource,
        schema={
            "version": "OpenAPIV3.0",
            "responses": {
                "200": {
                    "description": "example",
                    "content": {"application/json": {"example": {"code": boolean_value}}},
                }
            },
        },
    )
    content = json.loads(export_content(request_view, resource))
    content["paths"][resource.path]["get"]["responses"]["200"]["content"]["application/json"]["example"]["code"] = int(
        boolean_value
    )
    response = check_content(request_view, resource, json.dumps(content), include_change_type=True)
    assert response.status_code == 200, response.json()
    assert response.json()["data"][0]["change_type"] == "update"
