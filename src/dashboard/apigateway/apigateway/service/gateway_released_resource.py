"""Queries for resources referenced by a gateway's current releases."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Release, ReleasedResource

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_gateway_released_resources(
    *,
    gateway_id: int,
    resource_names: list[str] | None = None,
) -> QuerySet[ReleasedResource]:
    resource_version_ids = list(
        Release.objects.filter(
            gateway_id=gateway_id,
            stage__status=StageStatusEnum.ACTIVE.value,
        )
        .values_list("resource_version_id", flat=True)
        .distinct()
    )
    eligible = ReleasedResource.objects.filter(
        gateway_id=gateway_id,
        resource_version_id__in=resource_version_ids,
    )
    if resource_names:
        eligible = eligible.filter(resource_name__in=resource_names)

    # A gateway normally has only one released resource version, so no deduplication is needed.
    # SELECT id, resource_id, resource_name, data
    # FROM core_released_resource
    # WHERE api_id = %(gateway_id)s
    #   AND resource_version_id IN (%(resource_version_ids)s)
    #   /* AND resource_name IN (%(resource_names)s) */
    # ORDER BY resource_name, resource_id;
    if len(resource_version_ids) > 1:
        # Fetch only integer identifiers for at most a few released versions, then keep the first (latest) snapshot
        # of each resource in Python. This avoids a correlated subquery without loading the resource data JSON.
        # SELECT resource_id, id
        # FROM core_released_resource
        # WHERE api_id = %(gateway_id)s
        #   AND resource_version_id IN (%(resource_version_ids)s)
        #   /* AND resource_name IN (%(resource_names)s) */
        # ORDER BY resource_version_id DESC, id DESC;
        latest_snapshot_ids: dict[int, int] = {}
        candidates = eligible.order_by("-resource_version_id", "-id").values_list("resource_id", "id")
        for resource_id, snapshot_id in candidates:
            latest_snapshot_ids.setdefault(resource_id, snapshot_id)

        # SELECT id, resource_id, resource_name, data
        # FROM core_released_resource
        # WHERE api_id = %(gateway_id)s
        #   AND resource_version_id IN (%(resource_version_ids)s)
        #   /* AND resource_name IN (%(resource_names)s) */
        #   AND id IN (%(latest_snapshot_ids)s)
        # ORDER BY resource_name, resource_id;
        eligible = eligible.filter(id__in=list(latest_snapshot_ids.values()))

    return eligible.only("resource_id", "resource_name", "data").order_by("resource_name", "resource_id")
