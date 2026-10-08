# -*- coding: utf-8 -*-
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
import json
from unittest.mock import Mock

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.core.models import Release, ResourceVersion
from apigateway.utils.time import NeverExpiresTime

pytestmark = pytest.mark.django_db


@pytest.fixture(params=[False, True], ids=["user-first", "application-first"])
def mixed_servers(request, fake_gateway, fake_stage, settings):
    """Two servers share a release but select tools with different authentication requirements."""
    settings.BK_API_URL_TMPL = "http://example.com/{api_name}"
    rv = G(ResourceVersion, gateway=fake_gateway)
    rv.data = [
        {
            "id": index,
            "name": name,
            "description": name,
            "method": "GET",
            "path": f"/{name}/",
            "match_subpath": False,
            "is_public": True,
            "allow_apply_permission": True,
            "api_labels": [],
            "contexts": {"resource_auth": {"config": json.dumps({"auth_verified_required": requires_user})}},
        }
        for index, (name, requires_user) in enumerate([("user_tool", True), ("app_tool", False)], start=1)
    ]
    rv.save()
    G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)
    names = ["user", "application"]
    if request.param:
        names.reverse()
    servers = {}
    for name in names:
        server = G(
            MCPServer,
            name=f"{name}-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=1,
            is_public=True,
            protocol_type="sse",
            oauth2_public_client_enabled=False,
            _resource_names="user_tool" if name == "user" else "app_tool",
        )
        G(MCPServerAppPermission, mcp_server=server, bk_app_code="test-app", expires=NeverExpiresTime.time)
        G(
            MCPServerAppPermissionApply,
            mcp_server=server,
            bk_app_code="test-app",
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
        )
        servers[name] = server
    return servers


@pytest.mark.parametrize(
    "view_name",
    [
        "mcp_server.list_create",
        "mcp_marketplace.server.list",
        "openapi.v2.open.user.mcp_server.list",
        "openapi.v2.inner.mcp_server.permission.list",
        "openapi.v2.inner.mcp_server.permission.app-permissions",
        "openapi.v2.inner.mcp_server.permission.apply-records",
    ],
)
@pytest.mark.parametrize("public_client", [False, True])
def test_list_urls_use_each_servers_tools(request_view, fake_gateway, mixed_servers, view_name, public_client):
    if public_client:
        MCPServer.objects.filter(pk__in=[server.id for server in mixed_servers.values()]).update(
            oauth2_public_client_enabled=True
        )
    path_params = {"gateway_id": fake_gateway.id} if view_name == "mcp_server.list_create" else None
    resp = request_view(
        method="GET",
        view_name=view_name,
        path_params=path_params,
        gateway=fake_gateway,
        app=Mock(app_code="test-app"),
        data={"target_app_code": "test-app", "is_public": True},
    )
    assert resp.status_code == 200, resp.json()
    data = resp.json()["data"]
    rows = data["results"] if isinstance(data, dict) else data
    servers = [row.get("mcp_server", row) for row in rows]
    by_name = {server["name"]: server for server in servers}
    base_url = "http://example.com/bk-apigateway/prod/api/v2/mcp-servers"
    assert by_name["user-server"]["url"] == f"{base_url}/user-server/sse/"
    app_suffix = "sse/" if public_client else "application/sse/"
    assert by_name["application-server"]["url"] == f"{base_url}/application-server/{app_suffix}"
    if view_name == "openapi.v2.open.user.mcp_server.list":
        assert by_name["user-server"]["least_privilege"] == "application_and_user"
        assert by_name["user-server"]["application_url"] == ""
        assert by_name["application-server"]["least_privilege"] == "application"
        assert by_name["application-server"]["application_url"] == f"{base_url}/application-server/application/sse/"


@pytest.mark.parametrize(
    "view_name",
    ["mcp_server.list_create", "mcp_marketplace.server.list", "openapi.v2.open.user.mcp_server.list"],
)
def test_list_urls_do_not_depend_on_page_size(request_view, fake_gateway, mixed_servers, view_name):
    path_params = {"gateway_id": fake_gateway.id} if view_name == "mcp_server.list_create" else None
    results = []
    for limit, offset in [(2, 0), (1, 0), (1, 1)]:
        resp = request_view(
            method="GET",
            view_name=view_name,
            path_params=path_params,
            gateway=fake_gateway,
            app=Mock(app_code="test-app"),
            data={"limit": limit, "offset": offset, "is_public": True},
        )
        assert resp.status_code == 200, resp.json()
        results.append({row["id"]: row["url"] for row in resp.json()["data"]["results"]})
    assert len(results[0]) == 2
    assert len(results[1]) == len(results[2]) == 1
    assert results[1].keys().isdisjoint(results[2])
    assert results[0] == results[1] | results[2]


@pytest.mark.parametrize(
    "view_name",
    ["mcp_server.retrieve_update_destroy", "mcp_marketplace.server.retrieve"],
)
def test_detail_preserves_application_url(request_view, fake_gateway, mixed_servers, view_name):
    server = mixed_servers["application"]
    path_params = {"mcp_server_id": server.id}
    if view_name == "mcp_server.retrieve_update_destroy":
        path_params["gateway_id"] = fake_gateway.id
    resp = request_view(method="GET", view_name=view_name, path_params=path_params, gateway=fake_gateway)
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["url"] == (
        "http://example.com/bk-apigateway/prod/api/v2/mcp-servers/application-server/application/sse/"
    )
