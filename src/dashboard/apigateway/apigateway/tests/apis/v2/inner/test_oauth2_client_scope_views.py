from unittest import mock

import pytest
from ddf import G
from django.utils import translation

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage

MCP_SCOPE_VIEW = "openapi.v2.inner.oauth2.mcp_server_scopes.list"
RESOURCE_SCOPE_VIEW = "openapi.v2.inner.oauth2.resource_scopes.list"


def _make_gateway(
    name,
    *,
    is_official=False,
    tenant_mode=TenantModeEnum.GLOBAL.value,
    tenant_id="",
):
    return G(
        Gateway,
        name=name,
        status=GatewayStatusEnum.ACTIVE.value,
        is_public=True,
        is_official=is_official,
        tenant_mode=tenant_mode,
        tenant_id=tenant_id,
    )


def _make_resource(gateway, *, resource_id, name, public_enabled=True):
    resource_version = G(ResourceVersion, gateway=gateway, version=f"1.0.{resource_id}", _data="[]")
    stage = G(
        Stage,
        gateway=gateway,
        name=f"stage-{resource_version.id}",
        status=StageStatusEnum.ACTIVE.value,
    )
    G(Release, gateway=gateway, stage=stage, resource_version=resource_version)
    return G(
        ReleasedResource,
        gateway=gateway,
        resource_version_id=resource_version.id,
        resource_id=resource_id,
        resource_name=name,
        resource_method="GET",
        resource_path=f"/{name}",
        is_public=True,
        oauth2_public_client_enabled=public_enabled,
        data={
            "id": resource_id,
            "name": name,
            "description": f"{name} 中文描述",
            "description_en": f"{name} English description",
        },
    )


def _make_mcp_server(gateway, *, name, title=""):
    stage = G(Stage, gateway=gateway, name=f"stage-{name}", status=StageStatusEnum.ACTIVE.value)
    return G(
        MCPServer,
        gateway=gateway,
        stage=stage,
        name=name,
        title=title,
        status=MCPServerStatusEnum.ACTIVE.value,
        is_public=True,
        oauth2_public_client_enabled=True,
    )


@pytest.mark.parametrize("view_name", [MCP_SCOPE_VIEW, RESOURCE_SCOPE_VIEW])
@pytest.mark.parametrize("oauth_client_type", [None, "service"])
def test_scope_list_rejects_missing_or_unknown_client_type(request_view, view_name, oauth_client_type):
    data = {} if oauth_client_type is None else {"oauth_client_type": oauth_client_type}

    response = request_view(
        method="GET",
        view_name=view_name,
        app=mock.MagicMock(app_code="test"),
        data=data,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "query",
    [
        {"limit": 0},
        {"limit": 21},
        {"limit": "invalid"},
        {"offset": -1},
        {"offset": "invalid"},
    ],
)
def test_resource_scope_list_rejects_invalid_pagination(request_view, query):
    response = request_view(
        method="GET",
        view_name=RESOURCE_SCOPE_VIEW,
        app=mock.MagicMock(app_code="test"),
        data={"oauth_client_type": "public", **query},
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "view_name, query",
    [
        (MCP_SCOPE_VIEW, {"gateway_name": "g" * 65}),
        (MCP_SCOPE_VIEW, {"mcp_server_name": "m" * 65}),
        (RESOURCE_SCOPE_VIEW, {"gateway_name": "g" * 65}),
        (RESOURCE_SCOPE_VIEW, {"resource_name": "r" * 257}),
    ],
)
def test_scope_list_rejects_overlong_name_filters(request_view, view_name, query):
    response = request_view(
        method="GET",
        view_name=view_name,
        app=mock.MagicMock(app_code="test"),
        data={"oauth_client_type": "public", **query},
    )

    assert response.status_code == 400


def test_mcp_scope_list_returns_gateway_group_and_title_fallback(request_view):
    gateway = _make_gateway("official_mcp_gateway", is_official=True)
    mcp_server = _make_mcp_server(gateway, name="user_tools")

    response = request_view(
        method="GET",
        view_name=MCP_SCOPE_VIEW,
        app=mock.MagicMock(app_code="test"),
        data={"oauth_client_type": "public", "gateway_name": "official", "mcp_server_name": "user"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "count": 1,
            "results": [
                {
                    "id": gateway.id,
                    "name": "official_mcp_gateway",
                    "is_official": True,
                    "mcp_server_count": 1,
                    "mcp_servers": [
                        {"id": mcp_server.id, "name": "user_tools", "title": "user_tools"},
                    ],
                }
            ],
        }
    }


def test_resource_scope_list_paginates_gateways_and_translates_description(request_view):
    first_gateway = _make_gateway("a_gateway")
    second_gateway = _make_gateway("b_gateway", is_official=True)
    _make_resource(first_gateway, resource_id=1, name="first_resource")
    second_resource = _make_resource(second_gateway, resource_id=2, name="second_resource")

    with translation.override("en"):
        response = request_view(
            method="GET",
            view_name=RESOURCE_SCOPE_VIEW,
            app=mock.MagicMock(app_code="test"),
            data={"oauth_client_type": "public", "limit": 1, "offset": 1},
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "count": 2,
            "results": [
                {
                    "id": second_gateway.id,
                    "name": "b_gateway",
                    "is_official": True,
                    "resource_count": 1,
                    "resources": [
                        {
                            "id": second_resource.resource_id,
                            "name": "second_resource",
                            "description": "second_resource English description",
                        }
                    ],
                }
            ],
        }
    }


def test_resource_scope_list_applies_tenant_header_visibility(request_view, settings):
    settings.ENABLE_MULTI_TENANT_MODE = True
    global_gateway = _make_gateway("global_gateway")
    tenant_a_gateway = _make_gateway(
        "tenant_a_gateway",
        tenant_mode=TenantModeEnum.SINGLE.value,
        tenant_id="tenant-a",
    )
    tenant_b_gateway = _make_gateway(
        "tenant_b_gateway",
        tenant_mode=TenantModeEnum.SINGLE.value,
        tenant_id="tenant-b",
    )
    for resource_id, gateway in enumerate([global_gateway, tenant_a_gateway, tenant_b_gateway], start=1):
        _make_resource(gateway, resource_id=resource_id, name=f"resource_{resource_id}")

    response = request_view(
        method="GET",
        view_name=RESOURCE_SCOPE_VIEW,
        app=mock.MagicMock(app_code="test"),
        data={"oauth_client_type": "public"},
        HTTP_X_BK_TENANT_ID="tenant-a",
    )

    assert response.status_code == 200
    assert response.json()["data"]["count"] == 2
    assert [item["name"] for item in response.json()["data"]["results"]] == [
        "global_gateway",
        "tenant_a_gateway",
    ]

    missing_tenant_response = request_view(
        method="GET",
        view_name=RESOURCE_SCOPE_VIEW,
        app=mock.MagicMock(app_code="test"),
        data={"oauth_client_type": "public"},
    )
    assert missing_tenant_response.status_code == 400
