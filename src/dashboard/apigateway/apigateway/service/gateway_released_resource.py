"""Queries for resources referenced by a gateway's current releases."""

from django.db.models import Exists, OuterRef, QuerySet, Subquery

from apigateway.core.models import Release, ReleasedResource


def get_gateway_released_resources(
    *,
    gateway_id: int,
    resource_names: list[str] | None = None,
) -> QuerySet[ReleasedResource]:
    current_release = Release.objects.filter(
        gateway_id=gateway_id,
        resource_version_id=OuterRef("resource_version_id"),
    )
    eligible = ReleasedResource.objects.filter(
        Exists(current_release),
        gateway_id=gateway_id,
    )
    if resource_names:
        eligible = eligible.filter(resource_name__in=resource_names)

    latest_snapshot_id = (
        eligible.filter(resource_id=OuterRef("resource_id")).order_by("-resource_version_id", "-id").values("id")[:1]
    )
    return (
        eligible.filter(id=Subquery(latest_snapshot_id))
        .only("resource_id", "resource_name", "data")
        .order_by("resource_name", "resource_id")
    )
