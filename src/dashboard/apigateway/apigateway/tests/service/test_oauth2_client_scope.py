import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.service.oauth2_client_scope import (
    get_oauth2_mcp_server_scope_gateways,
    get_oauth2_mcp_server_scope_map,
    get_oauth2_resource_scope_gateways,
    get_oauth2_resource_scope_map,
)


def _make_gateway(
    name,
    *,
    status=GatewayStatusEnum.ACTIVE.value,
    is_public=True,
    tenant_mode=TenantModeEnum.GLOBAL.value,
    tenant_id="",
    oauth2_app_enabled=True,
):
    return G(
        Gateway,
        name=name,
        status=status,
        is_public=is_public,
        tenant_mode=tenant_mode,
        tenant_id=tenant_id,
        oauth2_app_enabled=oauth2_app_enabled,
    )


def _make_released_resource(
    gateway,
    *,
    resource_id,
    name,
    released=True,
    is_public=True,
    public_enabled=False,
    personal_enabled=False,
    app_delegated_enabled=False,
    app_only_enabled=False,
):
    resource_version = G(ResourceVersion, gateway=gateway, version=f"1.0.{resource_id}", _data="[]")
    if released:
        stage = G(
            Stage,
            gateway=gateway,
            name=f"stage-{resource_version.id}",
            status=StageStatusEnum.ACTIVE.value,
        )
        G(Release, gateway=gateway, stage=stage, resource_version=resource_version)

    data = {
        "id": resource_id,
        "name": name,
        "method": "GET",
        "path": f"/{name}",
        "description": f"{name} description",
        "description_en": f"{name} description en",
        "is_public": is_public,
    }
    return G(
        ReleasedResource,
        gateway=gateway,
        resource_version_id=resource_version.id,
        resource_id=resource_id,
        resource_name=name,
        resource_method="GET",
        resource_path=f"/{name}",
        is_public=is_public,
        oauth2_public_client_enabled=public_enabled,
        oauth2_personal_client_enabled=personal_enabled,
        oauth2_app_delegated_enabled=app_delegated_enabled,
        oauth2_app_only_enabled=app_only_enabled,
        data=data,
    )


def _make_mcp_server(
    gateway,
    *,
    name,
    title="",
    stage_status=StageStatusEnum.ACTIVE.value,
    status=MCPServerStatusEnum.ACTIVE.value,
    is_public=True,
    public_enabled=False,
    personal_enabled=False,
):
    stage = G(Stage, gateway=gateway, name=f"stage-{name}", status=stage_status)
    return G(
        MCPServer,
        gateway=gateway,
        stage=stage,
        name=name,
        title=title,
        status=status,
        is_public=is_public,
        oauth2_public_client_enabled=public_enabled,
        oauth2_personal_client_enabled=personal_enabled,
    )


def test_resource_scope_uses_only_release_referenced_versions():
    gateway = _make_gateway("scope-release-gateway")
    referenced = _make_released_resource(
        gateway,
        resource_id=1,
        name="referenced_resource",
        personal_enabled=True,
    )
    _make_released_resource(
        gateway,
        resource_id=2,
        name="orphan_resource",
        released=False,
        personal_enabled=True,
    )

    gateways = list(get_oauth2_resource_scope_gateways(oauth_client_type="personal"))
    scope_map = get_oauth2_resource_scope_map(
        gateway_ids=[item.id for item in gateways],
        oauth_client_type="personal",
    )

    assert [(item.id, item.scope_count) for item in gateways] == [(gateway.id, 1)]
    assert [item["id"] for item in scope_map[gateway.id]] == [referenced.resource_id]


def test_resource_scope_requires_public_and_switch_in_same_snapshot():
    gateway = _make_gateway("scope-snapshot-gateway")
    _make_released_resource(
        gateway,
        resource_id=1,
        name="public_snapshot",
        is_public=True,
        personal_enabled=False,
    )
    _make_released_resource(
        gateway,
        resource_id=1,
        name="personal_snapshot",
        is_public=False,
        personal_enabled=True,
    )

    assert get_oauth2_resource_scope_gateways(oauth_client_type="personal").count() == 0


def test_resource_scope_excludes_inactive_and_private_gateways():
    active_gateway = _make_gateway("active_gateway")
    inactive_gateway = _make_gateway("inactive_gateway", status=GatewayStatusEnum.INACTIVE.value)
    private_gateway = _make_gateway("private_gateway", is_public=False)
    for resource_id, gateway in enumerate([active_gateway, inactive_gateway, private_gateway], start=1):
        _make_released_resource(
            gateway,
            resource_id=resource_id,
            name=f"resource_{resource_id}",
            public_enabled=True,
        )

    names = list(get_oauth2_resource_scope_gateways(oauth_client_type="public").values_list("name", flat=True))

    assert names == ["active_gateway"]


def test_resource_scope_deduplicates_and_uses_latest_qualifying_snapshot():
    gateway = _make_gateway("scope-deduplicate-gateway")
    _make_released_resource(
        gateway,
        resource_id=1,
        name="old_name",
        personal_enabled=True,
    )
    latest = _make_released_resource(
        gateway,
        resource_id=1,
        name="new_name",
        personal_enabled=True,
    )

    gateways = list(get_oauth2_resource_scope_gateways(oauth_client_type="personal"))
    scope_map = get_oauth2_resource_scope_map(gateway_ids=[gateway.id], oauth_client_type="personal")

    assert gateways[0].scope_count == 1
    assert scope_map[gateway.id] == [
        {
            "id": latest.resource_id,
            "name": "new_name",
            "description": "new_name description",
            "description_en": "new_name description en",
        }
    ]


def test_resource_scope_filters_gateway_and_resource_names_with_and_semantics():
    matching_gateway = _make_gateway("blue_gateway")
    other_gateway = _make_gateway("red_gateway")
    _make_released_resource(
        matching_gateway,
        resource_id=1,
        name="get_user",
        public_enabled=True,
    )
    _make_released_resource(
        matching_gateway,
        resource_id=2,
        name="get_order",
        public_enabled=True,
    )
    _make_released_resource(
        other_gateway,
        resource_id=3,
        name="get_user",
        public_enabled=True,
    )

    gateways = list(
        get_oauth2_resource_scope_gateways(
            oauth_client_type="public",
            gateway_name="blue",
            resource_name="user",
        )
    )
    scope_map = get_oauth2_resource_scope_map(
        gateway_ids=[item.id for item in gateways],
        oauth_client_type="public",
        resource_name="user",
    )

    assert [(item.name, item.scope_count) for item in gateways] == [("blue_gateway", 1)]
    assert [item["name"] for item in scope_map[matching_gateway.id]] == ["get_user"]


def test_resource_scope_applies_global_and_current_tenant_visibility():
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
        _make_released_resource(
            gateway,
            resource_id=resource_id,
            name=f"resource_{resource_id}",
            public_enabled=True,
        )

    names = set(
        get_oauth2_resource_scope_gateways(
            oauth_client_type="public",
            tenant_id="tenant-a",
        ).values_list("name", flat=True)
    )

    assert names == {"global_gateway", "tenant_a_gateway"}


@pytest.mark.parametrize(
    ("oauth_client_type", "expected_names"),
    [
        ("app_delegated", ["delegated_resource"]),
        ("app_only", ["app_only_resource"]),
        ("public", ["public_resource"]),
    ],
)
def test_resource_scope_app_client_types_use_app_channel_columns(oauth_client_type, expected_names):
    gateway = _make_gateway("scope-app-channel-gateway")
    _make_released_resource(gateway, resource_id=1, name="delegated_resource", app_delegated_enabled=True)
    _make_released_resource(gateway, resource_id=2, name="app_only_resource", app_only_enabled=True)
    _make_released_resource(gateway, resource_id=3, name="public_resource", public_enabled=True)
    _make_released_resource(
        gateway, resource_id=4, name="private_delegated", is_public=False, app_delegated_enabled=True
    )

    gateways = list(get_oauth2_resource_scope_gateways(oauth_client_type=oauth_client_type))
    scope_map = get_oauth2_resource_scope_map(
        gateway_ids=[item.id for item in gateways],
        oauth_client_type=oauth_client_type,
    )

    assert [(item.id, item.scope_count) for item in gateways] == [(gateway.id, len(expected_names))]
    assert [item["name"] for item in scope_map[gateway.id]] == expected_names


@pytest.mark.parametrize("oauth_client_type", ["app_delegated", "app_only"])
def test_resource_scope_app_client_types_require_gateway_switch(oauth_client_type):
    enabled_gateway = _make_gateway("app_channel_enabled_gateway")
    disabled_gateway = _make_gateway("app_channel_disabled_gateway", oauth2_app_enabled=False)
    for resource_id, gateway in enumerate([enabled_gateway, disabled_gateway], start=1):
        _make_released_resource(
            gateway,
            resource_id=resource_id,
            name=f"resource_{resource_id}",
            app_delegated_enabled=True,
            app_only_enabled=True,
        )

    gateways = list(get_oauth2_resource_scope_gateways(oauth_client_type=oauth_client_type))
    scope_map = get_oauth2_resource_scope_map(
        gateway_ids=[enabled_gateway.id, disabled_gateway.id],
        oauth_client_type=oauth_client_type,
    )

    assert [item.name for item in gateways] == ["app_channel_enabled_gateway"]
    assert [item["name"] for item in scope_map[enabled_gateway.id]] == ["resource_1"]
    assert scope_map[disabled_gateway.id] == []


def test_resource_scope_unions_app_channels_across_stages():
    # 同一资源在两个环境发布了不同认证配置：scope 取各环境的并集，实际能否调用由目标环境的路由决定
    gateway = _make_gateway("scope-cross-stage-gateway")
    _make_released_resource(gateway, resource_id=1, name="cross_stage_resource", app_delegated_enabled=True)
    _make_released_resource(gateway, resource_id=1, name="cross_stage_resource", app_only_enabled=True)

    for oauth_client_type in ["app_delegated", "app_only"]:
        gateways = list(get_oauth2_resource_scope_gateways(oauth_client_type=oauth_client_type))
        scope_map = get_oauth2_resource_scope_map(gateway_ids=[gateway.id], oauth_client_type=oauth_client_type)

        assert [(item.id, item.scope_count) for item in gateways] == [(gateway.id, 1)]
        assert [item["name"] for item in scope_map[gateway.id]] == ["cross_stage_resource"]


def test_resource_scope_public_and_personal_ignore_gateway_switch():
    gateway = _make_gateway("app_channel_off_public_gateway", oauth2_app_enabled=False)
    _make_released_resource(gateway, resource_id=1, name="public_resource", public_enabled=True)

    assert [item.name for item in get_oauth2_resource_scope_gateways(oauth_client_type="public")] == [
        "app_channel_off_public_gateway"
    ]


def test_mcp_scope_app_delegated_returns_all_visible_servers_regardless_of_switches():
    gateway = _make_gateway("mcp_app_delegated_gateway", oauth2_app_enabled=False)
    _make_mcp_server(gateway, name="plain_mcp")
    _make_mcp_server(gateway, name="public_mcp", public_enabled=True)
    _make_mcp_server(gateway, name="private_mcp", is_public=False)
    _make_mcp_server(gateway, name="inactive_mcp", status=MCPServerStatusEnum.INACTIVE.value)

    gateways = list(get_oauth2_mcp_server_scope_gateways(oauth_client_type="app_delegated"))
    scope_map = get_oauth2_mcp_server_scope_map(
        gateway_ids=[item.id for item in gateways],
        oauth_client_type="app_delegated",
    )

    assert [(item.name, item.scope_count) for item in gateways] == [("mcp_app_delegated_gateway", 2)]
    assert [item["name"] for item in scope_map[gateway.id]] == ["plain_mcp", "public_mcp"]


def test_mcp_scope_filters_gateway_stage_mcp_visibility_and_client_type():
    valid_gateway = _make_gateway("valid_mcp_gateway")
    _make_mcp_server(valid_gateway, name="valid_mcp", public_enabled=True)
    _make_mcp_server(valid_gateway, name="private_mcp", is_public=False, public_enabled=True)
    _make_mcp_server(
        valid_gateway,
        name="inactive_mcp",
        status=MCPServerStatusEnum.INACTIVE.value,
        public_enabled=True,
    )
    _make_mcp_server(valid_gateway, name="disabled_mcp", public_enabled=False)
    _make_mcp_server(
        valid_gateway,
        name="inactive_stage_mcp",
        stage_status=StageStatusEnum.INACTIVE.value,
        public_enabled=True,
    )

    inactive_gateway = _make_gateway("inactive_mcp_gateway", status=GatewayStatusEnum.INACTIVE.value)
    _make_mcp_server(inactive_gateway, name="inactive_gateway_mcp", public_enabled=True)
    private_gateway = _make_gateway("private_mcp_gateway", is_public=False)
    _make_mcp_server(private_gateway, name="private_gateway_mcp", public_enabled=True)

    gateways = list(get_oauth2_mcp_server_scope_gateways(oauth_client_type="public"))
    scope_map = get_oauth2_mcp_server_scope_map(
        gateway_ids=[item.id for item in gateways],
        oauth_client_type="public",
    )

    assert [(item.name, item.scope_count) for item in gateways] == [("valid_mcp_gateway", 1)]
    assert [item["name"] for item in scope_map[valid_gateway.id]] == ["valid_mcp"]


def test_mcp_scope_deduplicates_gateways_and_counts_all_matching_servers():
    gateway = _make_gateway("mcp-deduplicate-gateway")
    _make_mcp_server(gateway, name="first_mcp", public_enabled=True)
    _make_mcp_server(gateway, name="second_mcp", public_enabled=True)

    gateways = list(get_oauth2_mcp_server_scope_gateways(oauth_client_type="public"))

    assert [(item.id, item.scope_count) for item in gateways] == [(gateway.id, 2)]


def test_mcp_scope_applies_global_and_current_tenant_visibility():
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
    for gateway in [global_gateway, tenant_a_gateway, tenant_b_gateway]:
        _make_mcp_server(gateway, name=f"{gateway.name}_mcp", public_enabled=True)

    names = set(
        get_oauth2_mcp_server_scope_gateways(
            oauth_client_type="public",
            tenant_id="tenant-a",
        ).values_list("name", flat=True)
    )

    assert names == {"global_gateway", "tenant_a_gateway"}


def test_mcp_scope_title_falls_back_to_name_and_name_filters_have_and_semantics():
    gateway = _make_gateway("blue_mcp_gateway")
    user_mcp = _make_mcp_server(gateway, name="user_tools", personal_enabled=True)
    _make_mcp_server(gateway, name="order_tools", title="Order tools", personal_enabled=True)

    gateways = list(
        get_oauth2_mcp_server_scope_gateways(
            oauth_client_type="personal",
            gateway_name="blue",
            mcp_server_name="user",
        )
    )
    scope_map = get_oauth2_mcp_server_scope_map(
        gateway_ids=[item.id for item in gateways],
        oauth_client_type="personal",
        mcp_server_name="user",
    )

    assert gateways[0].scope_count == 1
    assert scope_map[gateway.id] == [{"id": user_mcp.id, "name": "user_tools", "title": "user_tools"}]


def test_resource_scope_map_returns_empty_without_gateways():
    assert (
        get_oauth2_resource_scope_map(
            gateway_ids=[],
            oauth_client_type="public",
            resource_name="user",
        )
        == {}
    )


def test_mcp_scope_map_returns_empty_without_gateways():
    assert (
        get_oauth2_mcp_server_scope_map(
            gateway_ids=[],
            oauth_client_type="public",
            mcp_server_name="tools",
        )
        == {}
    )


def test_resource_scope_page_uses_four_queries(django_assert_num_queries):
    gateway = _make_gateway("resource-query-budget-gateway")
    _make_released_resource(
        gateway,
        resource_id=1,
        name="query_budget_resource",
        public_enabled=True,
    )

    with django_assert_num_queries(4):
        gateways = get_oauth2_resource_scope_gateways(oauth_client_type="public")
        assert gateways.count() == 1
        page = list(gateways[:20])
        scope_map = get_oauth2_resource_scope_map(
            gateway_ids=[item.id for item in page],
            oauth_client_type="public",
        )
        assert len(scope_map[page[0].id]) == 1


def test_resource_app_scope_page_uses_four_queries(django_assert_num_queries):
    gateway = _make_gateway("resource-app-query-budget-gateway")
    _make_released_resource(gateway, resource_id=1, name="query_budget_resource", app_only_enabled=True)

    with django_assert_num_queries(4):
        gateways = get_oauth2_resource_scope_gateways(oauth_client_type="app_only")
        assert gateways.count() == 1
        page = list(gateways[:20])
        scope_map = get_oauth2_resource_scope_map(
            gateway_ids=[item.id for item in page],
            oauth_client_type="app_only",
        )
        assert len(scope_map[page[0].id]) == 1


def test_mcp_scope_page_uses_four_queries(django_assert_num_queries):
    gateway = _make_gateway("mcp-query-budget-gateway")
    _make_mcp_server(gateway, name="query_budget_mcp", public_enabled=True)

    with django_assert_num_queries(4):
        gateways = get_oauth2_mcp_server_scope_gateways(oauth_client_type="public")
        assert gateways.count() == 1
        page = list(gateways[:20])
        scope_map = get_oauth2_mcp_server_scope_map(
            gateway_ids=[item.id for item in page],
            oauth_client_type="public",
        )
        assert len(scope_map[page[0].id]) == 1
