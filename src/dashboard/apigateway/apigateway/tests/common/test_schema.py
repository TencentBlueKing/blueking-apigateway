#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import importlib

import pytest
import yaml
from django.test import override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse, set_urlconf
from drf_spectacular.validation import validate_schema

import apigateway.urls
from apigateway.apis.v2.inner import serializers, views


class TestUrls:
    def test_inner_monitor_apis_own_pagination_parameters_once(self):
        assert "offset" not in serializers.AppAlarmRecordListInputSLZ().fields
        assert "limit" not in serializers.AppAlarmRecordListInputSLZ().fields
        assert views.AppRequestLogListApi.pagination_class is None

    def test_schema_generation_succeeds_with_explicit_query_parameters(self, caplog, client):
        try:
            with override_settings(DEBUG=True):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                response = client.get("/backend/docs/auto/swagger.json")

                assert response.status_code == 200
                schema = response.json()
                assert schema["openapi"].startswith("3.")
                assert "swagger" not in schema
                alarm_record_parameters = schema["paths"]["/api/v2/inner/apps/{app_code}/monitor/alarm-records/"][
                    "get"
                ]["parameters"]
                alarm_record_parameter_names = [parameter["name"] for parameter in alarm_record_parameters]
                assert set(alarm_record_parameter_names) == {
                    "app_code",
                    "status",
                    "gateway_name",
                    "resource_name",
                    "time_start",
                    "time_end",
                    "offset",
                    "limit",
                }
                assert len(alarm_record_parameter_names) == len(set(alarm_record_parameter_names))

                released_resource_parameters = schema["paths"][
                    "/api/v2/inner/gateways/{gateway_name}/released-resources/"
                ]["get"]["parameters"]
                released_resource_parameter_names = [parameter["name"] for parameter in released_resource_parameters]
                assert released_resource_parameter_names.count("limit") == 1
                assert released_resource_parameter_names.count("offset") == 1
                assert len(released_resource_parameter_names) == len(set(released_resource_parameter_names))

                workbench_parameters = schema["paths"]["/me/workbench/permissions/gateway/applied/"]["get"][
                    "parameters"
                ]
                workbench_parameter_names = [parameter["name"] for parameter in workbench_parameters]
                assert set(workbench_parameter_names) == {
                    "limit",
                    "offset",
                    "bk_app_code",
                    "applied_by",
                    "gateway_id",
                    "grant_dimension",
                    "time_start",
                    "time_end",
                    "keyword",
                    "status",
                }
                assert len(workbench_parameter_names) == len(set(workbench_parameter_names))
                assert "GatewayPublicKeyRetrieveApi.get_serializer raised exception" not in caplog.text
                assert "ResourceVersionGetLatestApi.get_serializer raised exception" not in caplog.text
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)

    def test_schema_json_url_uses_non_compat_format(self):
        try:
            with override_settings(DEBUG=True):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                assert reverse("schema-json", kwargs={"format": "json"}) == "/backend/docs/auto/swagger.json"
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)

    def test_urls_disabled_when_debug_is_false(self):
        try:
            with override_settings(DEBUG=False):
                clear_url_caches()
                importlib.reload(apigateway.urls)
                set_urlconf(None)

                with pytest.raises(NoReverseMatch):
                    reverse("schema-swagger-ui")
        finally:
            importlib.reload(apigateway.urls)
            clear_url_caches()
            set_urlconf(None)


@pytest.fixture
def documentation_urls():
    try:
        with override_settings(DEBUG=True):
            clear_url_caches()
            importlib.reload(apigateway.urls)
            set_urlconf(None)
            yield
    finally:
        importlib.reload(apigateway.urls)
        clear_url_caches()
        set_urlconf(None)


def resolve_schema(document, schema):
    if "$ref" in schema:
        return document["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]]
    return schema


def test_oas3_response_and_upload_contracts(client, documentation_urls):
    response = client.get("/backend/docs/auto/swagger.json")
    assert response.status_code == 200
    document = response.json()
    validate_schema(document)
    assert document["servers"] == [{"url": "/backend"}]
    operation = document["paths"]["/gateways/{gateway_id}/resources/"]["get"]
    envelope = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert set(envelope["properties"]) == {"data"}
    page = resolve_schema(document, envelope["properties"]["data"])
    assert set(page["properties"]) == {"count", "results"}
    assert page["properties"]["results"]["type"] == "array"

    legacy = document["paths"]["/api/v1/apis/"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert set(legacy["properties"]) == {"result", "code", "message", "data"}
    assert legacy["properties"]["data"]["type"] == "array"

    upload = document["paths"]["/gateways/{gateway_id}/docs/archive/parse/"]["post"]["requestBody"]
    fields = resolve_schema(document, upload["content"]["multipart/form-data"]["schema"])["properties"]
    assert fields["file"]["type"] == "string"
    assert fields["file"]["format"] == "binary"
    download = document["paths"]["/gateways/{gateway_id}/resource-versions/{id}/export/"]["post"]
    assert set(download["responses"]["200"]["content"]) == {"application/octet-stream"}
    assert "content" not in document["paths"]["/gateways/{gateway_id}/resources/{id}/"]["delete"]["responses"]["204"]


def test_yaml_and_offline_documentation_viewers(client, documentation_urls):
    response = client.get("/backend/docs/auto/swagger.yaml")
    assert response.status_code == 200
    assert yaml.safe_load(response.content)["openapi"].startswith("3.")
    for url in ("/backend/docs/auto/swagger/", "/backend/docs/auto/redoc/"):
        response = client.get(url)
        assert response.status_code == 200
        assert b"/backend/static/drf_spectacular_sidecar/" in response.content
        assert b"/backend/docs/auto/swagger.json" in response.content
        assert b"cdn.jsdelivr.net" not in response.content


@pytest.mark.parametrize(
    "path, method, fields",
    [
        (
            "/api/v2/open/.well-known/oauth-protected-resource",
            "get",
            {"resource", "authorization_servers", "bearer_methods_supported"},
        ),
        ("/api/v2/inner/itsm/callback/", "post", {"result", "message"}),
        ("/api/v2/inner/monitor/alarm-types/{alarm_type}/callback/", "post", {"code", "result", "message", "data"}),
    ],
)
def test_raw_json_responses_are_not_wrapped(client, documentation_urls, path, method, fields):
    document = client.get("/backend/docs/auto/swagger.json").json()
    schema = document["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]
    assert set(schema["properties"]) == fields


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/apis/{gateway_name}/released/stages/{stage_name}/resources/",
        "/api/v1/apis/{gateway_name}/resource_versions/",
        "/api/v1/apis/permissions/apply-records/",
        "/api/v1/esb/systems/permissions/apply-records/",
    ],
)
def test_legacy_pagination_uses_boolean_navigation(client, documentation_urls, path):
    document = client.get("/backend/docs/auto/swagger.json").json()
    envelope = document["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    page = resolve_schema(document, envelope["properties"]["data"])
    assert set(page["properties"]) == {"count", "results", "has_next", "has_previous"}
    assert page["properties"]["has_next"]["type"] == "boolean"
    assert page["properties"]["has_previous"]["type"] == "boolean"


def test_legacy_alarm_callback_accepts_json_object(client, documentation_urls):
    document = client.get("/backend/docs/auto/swagger.json").json()
    operation = document["paths"]["/api/v1/apis/monitor/alarm-types/{alarm_type}/callback/"]["post"]
    content = operation["requestBody"]["content"]
    assert set(content) == {"application/json"}
    assert content["application/json"]["schema"] == {"type": "object", "additionalProperties": True}


@pytest.mark.parametrize(
    "path, filters",
    [
        ("/gateways/{gateway_id}/permissions/app-permission-apply/", {"bk_app_code", "applied_by", "grant_dimension"}),
        (
            "/gateways/{gateway_id}/permissions/app-permission-records/",
            {"bk_app_code", "grant_dimension", "time_start", "time_end"},
        ),
        (
            "/me/workbench/permissions/gateway/pending/",
            {"bk_app_code", "applied_by", "gateway_id", "grant_dimension", "keyword", "time_start", "time_end"},
        ),
        (
            "/me/workbench/permissions/gateway/handled/",
            {
                "bk_app_code",
                "applied_by",
                "gateway_id",
                "grant_dimension",
                "keyword",
                "status",
                "time_start",
                "time_end",
            },
        ),
        (
            "/me/workbench/permissions/mcp/pending/",
            {"bk_app_code", "applied_by", "gateway_id", "mcp_server_id", "keyword", "time_start", "time_end"},
        ),
        (
            "/me/workbench/permissions/mcp/handled/",
            {
                "bk_app_code",
                "applied_by",
                "gateway_id",
                "mcp_server_id",
                "keyword",
                "status",
                "time_start",
                "time_end",
            },
        ),
    ],
)
def test_permission_filters_are_documented_without_request_context(client, documentation_urls, path, filters):
    document = client.get("/backend/docs/auto/swagger.json").json()
    parameters = document["paths"][path]["get"]["parameters"]
    names = [parameter["name"] for parameter in parameters if parameter["in"] == "query"]
    assert set(names) == filters | {"limit", "offset"}
    assert len(names) == len(set(names))


@pytest.mark.parametrize(
    "path, fields",
    [
        ("/esb/components/batch/", {"ids"}),
        (
            "/gateways/{gateway_id}/permissions/app-permissions/batch/",
            {"gateway_dimension_ids", "resource_dimension_ids"},
        ),
        ("/gateways/{gateway_id}/resource-versions/batch/", {"ids"}),
        ("/gateways/{gateway_id}/resources/batch/", {"ids"}),
    ],
)
def test_delete_json_request_bodies_are_preserved(client, documentation_urls, path, fields):
    document = client.get("/backend/docs/auto/swagger.json").json()
    operation = document["paths"][path]["delete"]
    assert operation["requestBody"]["required"] is True
    schema = resolve_schema(document, operation["requestBody"]["content"]["application/json"]["schema"])
    assert set(schema["properties"]) == fields
    assert all(schema["properties"][field]["type"] == "array" for field in fields)


def test_gateway_permission_delete_uses_query_ids(client, documentation_urls):
    document = client.get("/backend/docs/auto/swagger.json").json()
    operation = document["paths"]["/gateways/{gateway_id}/permissions/app-gateway-permissions/delete/"]["delete"]
    assert "requestBody" not in operation
    ids = next(parameter for parameter in operation["parameters"] if parameter["name"] == "ids")
    assert ids["in"] == "query"
    assert ids["schema"]["type"] == "array"


@pytest.mark.parametrize(
    "path, method",
    [
        ("/api/v2/inner/monitor/alarm-types/{alarm_type}/callback/", "post"),
        ("/gateways/{gateway_id}/stages/{id}/backends/{backend_id}/", "put"),
        ("/gateways/{gateway_id}/stages/{id}/backends/{backend_id}/", "patch"),
    ],
)
def test_dynamic_json_request_bodies_are_preserved(client, documentation_urls, path, method):
    document = client.get("/backend/docs/auto/swagger.json").json()
    body = document["paths"][path][method]["requestBody"]
    assert body["content"]["application/json"]["schema"] == {"type": "object", "additionalProperties": True}


@pytest.mark.parametrize(
    "path, required",
    [
        ("/api/v2/inner/gateways/{gateway_name}/status/", {"status"}),
        ("/gateways/{gateway_id}/status/", {"status"}),
        ("/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/status/", {"status"}),
        (
            "/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/{id}/status/",
            {"status"},
        ),
        ("/gateways/{gateway_id}/stages/{id}/status/", {"status"}),
        ("/gateways/{gateway_id}/resources/batch/", {"ids", "is_public", "allow_apply_permission"}),
        ("/gateways/{gateway_id}/resources/{resource_id}/labels/", {"label_ids"}),
        ("/gateways/{gateway_id}/stages/{id}/", {"description"}),
        ("/gateways/{gateway_id}/backends/{id}/", {"name", "configs"}),
        ("/gateways/{gateway_id}/labels/{id}/", {"name"}),
        (
            "/gateways/{gateway_id}/monitors/alarm/strategies/{id}/",
            {"name", "alarm_type", "alarm_subtype", "gateway_label_ids", "config"},
        ),
        ("/gateways/{gateway_id}/resources/{id}/", {"name", "method", "path", "auth_config", "backend"}),
        ("/gateways/{gateway_id}/resources/{resource_id}/docs/{id}/", {"language"}),
        ("/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/user-custom-doc/", {"content"}),
    ],
)
def test_patch_handlers_that_validate_full_payload_keep_required_fields(client, documentation_urls, path, required):
    document = client.get("/backend/docs/auto/swagger.json").json()
    body = document["paths"][path]["patch"]["requestBody"]
    schema = resolve_schema(document, body["content"]["application/json"]["schema"])
    assert set(schema["required"]) == required
    assert body["required"] is True


@pytest.mark.parametrize("path", ["/gateways/{gateway_id}/", "/gateways/{gateway_id}/mcp-servers/{mcp_server_id}/"])
def test_patch_handlers_that_support_partial_payload_keep_optional_fields(client, documentation_urls, path):
    document = client.get("/backend/docs/auto/swagger.json").json()
    body = document["paths"][path]["patch"]["requestBody"]
    schema = resolve_schema(document, body["content"]["application/json"]["schema"])
    assert not schema.get("required")
    assert not body.get("required")
