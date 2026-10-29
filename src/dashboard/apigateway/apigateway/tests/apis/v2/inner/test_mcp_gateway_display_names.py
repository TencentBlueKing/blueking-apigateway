from unittest.mock import MagicMock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.translation import override
from django_dynamic_fixture import G

from apigateway.apps.mcp_server.models import MCPServer


@pytest.mark.parametrize("keyword,expected_count", [("matching-mcp", 1), ("Gateway Display", 0)])
def test_mcp_permission_keyword_uses_existing_mcp_fields(
    request_view, fake_gateway, fake_stage, keyword, expected_count
):
    fake_gateway.display_name = "Gateway Display"
    fake_gateway.save(update_fields=["display_name"])
    G(MCPServer, gateway=fake_gateway, stage=fake_stage, name="matching-mcp", is_public=True, status=1)
    response = request_view(
        method="GET",
        view_name="openapi.v2.inner.mcp_server.permission.list",
        data={"target_app_code": "test", "keyword": keyword},
        app=MagicMock(app_code="test"),
    )
    assert response.status_code == 200, response.json()
    assert len(response.json()["data"]) == expected_count


@pytest.fixture
def display_server(fake_gateway, fake_stage, mocker):
    fake_gateway.display_name = "默认名"
    fake_gateway.display_name_en = "English"
    fake_gateway.save(update_fields=["display_name", "display_name_en"])
    fake_stage.status = 1
    fake_stage.save(update_fields=["status"])
    mocker.patch("apigateway.biz.mcp_server.mcp_server.render_to_string", return_value="guideline")
    mocker.patch("apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels", return_value=([], {}))
    return G(
        MCPServer,
        gateway=fake_gateway,
        stage=fake_stage,
        name="display-server",
        is_public=True,
        status=1,
        _resource_names="",
    )


GATEWAY_ROUTES = [
    "mcp_marketplace.server.list",
    "mcp_marketplace.server.retrieve",
    "openapi.v2.open.mcp_server.list",
    "openapi.v2.open.user.mcp_server.list",
    "openapi.v2.inner.mcp_server.list",
    "openapi.v2.inner.mcp_server.lookup",
]


@pytest.mark.parametrize("view_name", GATEWAY_ROUTES)
@pytest.mark.parametrize(
    "language,english,expected", [("zh-cn", "English", "默认名"), ("en", "English", "English"), ("en", None, "默认名")]
)
def test_existing_mcp_gateway_projections_are_localized(
    request_view, display_server, view_name, language, english, expected
):
    gateway = display_server.gateway
    gateway.display_name_en = english
    gateway.save(update_fields=["display_name_en"])
    params = {"mcp_server_id": display_server.pk} if view_name.endswith("retrieve") else {}
    data = {"ids": str(display_server.pk)} if view_name.endswith("lookup") else {}
    with override(language):
        response = request_view(
            method="GET", view_name=view_name, path_params=params, data=data, app=MagicMock(app_code="test")
        )
    assert response.status_code == 200, response.json()
    result = response.json()["data"]
    if isinstance(result, dict) and "results" in result:
        result = result["results"]
    if isinstance(result, list):
        result = next(item for item in result if item["id"] == display_server.pk)
    assert result["gateway"]["id"] == gateway.pk
    assert result["gateway"]["name"] == gateway.name
    assert result["gateway"]["display_name"] == expected


@pytest.mark.parametrize("view_name", ["openapi.v2.inner.mcp_server.list", "openapi.v2.inner.mcp_server.lookup"])
@pytest.mark.parametrize("fields", ["id,name", "id,gateway"])
def test_inner_mcp_selected_fields_preserved(request_view, display_server, view_name, fields):
    data = {"fields": fields}
    if view_name.endswith("lookup"):
        data["ids"] = str(display_server.pk)
    with override("en"):
        response = request_view(method="GET", view_name=view_name, data=data, app=MagicMock(app_code="test"))
    assert response.status_code == 200, response.json()
    rows = response.json()["data"]
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 1
    assert set(rows[0]) == set(fields.split(","))
    if "gateway" in rows[0]:
        assert rows[0]["gateway"]["display_name"] == "English"


@pytest.mark.parametrize("fields", [None, "id,name,title,description,categories"])
def test_batch_query_keeps_existing_mcp_only_projection(request_view, display_server, fields):
    data = {"ids": [display_server.pk]}
    if fields is not None:
        data["fields"] = fields
    response = request_view(
        method="POST", view_name="openapi.v2.open.mcp_server.batch_query", data=data, app=MagicMock(app_code="test")
    )
    assert response.status_code == 200, response.json()
    row = response.json()["data"][0]
    assert set(row) == set((fields or "id,name").split(","))
    assert "gateway" not in row


@pytest.mark.parametrize(
    "view_name",
    ["openapi.v2.open.mcp_server.retrieve", "mcp_server.list_create", "mcp_server.retrieve_update_destroy"],
)
def test_existing_mcp_only_dtos_do_not_gain_gateway_structure(request_view, display_server, view_name):
    params = {}
    if view_name != "openapi.v2.open.mcp_server.retrieve":
        params["gateway_id"] = display_server.gateway_id
    if view_name.endswith(("retrieve", "retrieve_update_destroy")):
        params["mcp_server_id"] = display_server.pk
    response = request_view(method="GET", view_name=view_name, path_params=params, app=MagicMock(app_code="test"))
    assert response.status_code == 200, response.json()
    result = response.json()["data"]
    if "results" in result:
        result = result["results"][0]
    assert result["id"] == display_server.pk
    assert "gateway" not in result
    assert "gateway_display_name" not in result


@pytest.mark.parametrize(
    "view_name",
    [
        "mcp_marketplace.server.list",
        "openapi.v2.open.mcp_server.list",
        "openapi.v2.open.user.mcp_server.list",
        "openapi.v2.inner.mcp_server.list",
        "openapi.v2.inner.mcp_server.lookup",
    ],
)
def test_mcp_gateway_projection_does_not_add_per_row_queries(request_view, display_server, view_name):
    data = {"ids": str(display_server.pk)} if view_name.endswith("lookup") else {}

    def fetch():
        return request_view(method="GET", view_name=view_name, data=data, app=MagicMock(app_code="test"))

    with override("en"), CaptureQueriesContext(connection) as first:
        response = fetch()
    assert response.status_code == 200, response.json()
    ids = [display_server.pk]
    for index in range(4):
        server = G(
            MCPServer,
            gateway=display_server.gateway,
            stage=display_server.stage,
            name=f"extra-server-{index}",
            is_public=True,
            status=1,
            _resource_names="",
        )
        ids.append(server.pk)
    if view_name.endswith("lookup"):
        data["ids"] = ",".join(map(str, ids))
    with override("en"), CaptureQueriesContext(connection) as larger:
        response = fetch()
    assert response.status_code == 200, response.json()
    rows = response.json()["data"]
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 5
    assert all(row["gateway"]["display_name"] == "English" for row in rows)
    assert len(larger) == len(first)
