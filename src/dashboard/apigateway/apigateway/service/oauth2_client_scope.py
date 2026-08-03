"""Queries for OAuth2 personal/public client scope selection."""

from typing import Any, Sequence

from django.db.models import Count, Exists, OuterRef, QuerySet, Subquery

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource

OAUTH2_CLIENT_TYPE_FIELD_MAP = {
    "public": "oauth2_public_client_enabled",
    "personal": "oauth2_personal_client_enabled",
}
OAUTH2_CLIENT_TYPES = tuple(OAUTH2_CLIENT_TYPE_FIELD_MAP)


def _get_oauth2_released_resources(
    oauth_client_type: str,
    resource_name: str = "",
) -> QuerySet[ReleasedResource]:
    field_name = OAUTH2_CLIENT_TYPE_FIELD_MAP[oauth_client_type]
    current_release = Release.objects.filter(
        gateway_id=OuterRef("gateway_id"),
        resource_version_id=OuterRef("resource_version_id"),
    )
    queryset = ReleasedResource.objects.filter(
        Exists(current_release),
        is_public=True,
        **{field_name: True},
    )
    if resource_name:
        queryset = queryset.filter(resource_name__contains=resource_name)
    return queryset


def _get_oauth2_mcp_servers(
    oauth_client_type: str,
    mcp_server_name: str = "",
) -> QuerySet[MCPServer]:
    field_name = OAUTH2_CLIENT_TYPE_FIELD_MAP[oauth_client_type]
    queryset = MCPServer.objects.filter(
        gateway__status=GatewayStatusEnum.ACTIVE.value,
        gateway__is_public=True,
        stage__status=StageStatusEnum.ACTIVE.value,
        status=MCPServerStatusEnum.ACTIVE.value,
        is_public=True,
        **{field_name: True},
    )
    if mcp_server_name:
        queryset = queryset.filter(name__contains=mcp_server_name)
    return queryset


def get_oauth2_resource_scope_gateways(
    *,
    oauth_client_type: str,
    tenant_id: str | None = None,
    gateway_name: str = "",
    resource_name: str = "",
) -> QuerySet[Gateway]:
    queryset = Gateway.objects.filter(
        status=GatewayStatusEnum.ACTIVE.value,
        is_public=True,
    )
    if tenant_id:
        queryset = gateway_filter_by_app_tenant_id(queryset, tenant_id)
    if gateway_name:
        queryset = queryset.filter(name__contains=gateway_name)

    eligible_for_gateway = _get_oauth2_released_resources(oauth_client_type, resource_name).filter(
        gateway_id=OuterRef("pk")
    )
    scope_count = (
        eligible_for_gateway.values("gateway_id").annotate(value=Count("resource_id", distinct=True)).values("value")
    )
    return (
        queryset.filter(Exists(eligible_for_gateway))
        .annotate(scope_count=Subquery(scope_count))
        .order_by("name", "id")
    )


def get_oauth2_resource_scope_map(
    *,
    gateway_ids: Sequence[int],
    oauth_client_type: str,
    resource_name: str = "",
) -> dict[int, list[dict[str, Any]]]:
    if not gateway_ids:
        return {}

    rows = (
        _get_oauth2_released_resources(oauth_client_type, resource_name)
        .filter(gateway_id__in=gateway_ids)
        .values("gateway_id", "resource_id", "resource_version_id", "resource_name", "data")
        .order_by("gateway_id", "resource_id", "-resource_version_id")
    )
    selected: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        selected.setdefault((row["gateway_id"], row["resource_id"]), row)

    result: dict[int, list[dict[str, Any]]] = {gateway_id: [] for gateway_id in gateway_ids}
    for row in selected.values():
        data = row["data"] or {}
        result[row["gateway_id"]].append(
            {
                "id": row["resource_id"],
                "name": row["resource_name"],
                "description": data.get("description", ""),
                "description_en": data.get("description_en"),
            }
        )
    for resources in result.values():
        resources.sort(key=lambda item: (item["name"], item["id"]))
    return result


def get_oauth2_mcp_server_scope_gateways(
    *,
    oauth_client_type: str,
    tenant_id: str | None = None,
    gateway_name: str = "",
    mcp_server_name: str = "",
) -> QuerySet[Gateway]:
    queryset = Gateway.objects.filter(
        status=GatewayStatusEnum.ACTIVE.value,
        is_public=True,
    )
    if tenant_id:
        queryset = gateway_filter_by_app_tenant_id(queryset, tenant_id)
    if gateway_name:
        queryset = queryset.filter(name__contains=gateway_name)

    eligible_for_gateway = _get_oauth2_mcp_servers(oauth_client_type, mcp_server_name).filter(
        gateway_id=OuterRef("pk")
    )
    scope_count = eligible_for_gateway.values("gateway_id").annotate(value=Count("id", distinct=True)).values("value")
    return (
        queryset.filter(Exists(eligible_for_gateway))
        .annotate(scope_count=Subquery(scope_count))
        .order_by("name", "id")
    )


def get_oauth2_mcp_server_scope_map(
    *,
    gateway_ids: Sequence[int],
    oauth_client_type: str,
    mcp_server_name: str = "",
) -> dict[int, list[dict[str, Any]]]:
    if not gateway_ids:
        return {}

    rows = (
        _get_oauth2_mcp_servers(oauth_client_type, mcp_server_name)
        .filter(gateway_id__in=gateway_ids)
        .values("gateway_id", "id", "name", "title")
        .order_by("gateway_id", "name", "id")
    )
    result: dict[int, list[dict[str, Any]]] = {gateway_id: [] for gateway_id in gateway_ids}
    for row in rows:
        result[row["gateway_id"]].append(
            {
                "id": row["id"],
                "name": row["name"],
                "title": row["title"] or row["name"],
            }
        )
    return result
