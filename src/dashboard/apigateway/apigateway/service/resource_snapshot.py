import datetime
import itertools
import json
import operator
from collections import defaultdict
from typing import Dict, List, Optional

from apigateway.apps.label.models import ResourceLabel
from apigateway.apps.openapi.models import OpenAPIResourceSchema, OpenAPIResourceSchemaVersion
from apigateway.core.constants import STAGE_VAR_PATTERN, ContextScopeTypeEnum, ProxyTypeEnum
from apigateway.core.models import Context, Proxy, Resource, ResourceVersion, Stage, StageResourceDisabled
from apigateway.schema.models import Schema
from apigateway.utils import time


def get_resource_id_to_proxy_snapshot(resource_ids: List[int]) -> Dict[int, Dict]:
    schemas = Schema.objects.filter_id_snapshot_map()
    return {
        proxy.resource_id: proxy.snapshot(as_dict=True, schemas=schemas)
        for proxy in Proxy.objects.filter(resource_id__in=resource_ids).prefetch_related("backend")
    }


def filter_disabled_stages_by_gateway(gateway):
    stage_ids = Stage.objects.get_ids(gateway.id)

    queryset = StageResourceDisabled.objects.filter(stage_id__in=stage_ids)
    queryset = queryset.values("stage_id", "stage__name", "resource_id")

    disabled = sorted(queryset, key=operator.itemgetter("resource_id"))

    disabled_groups = itertools.groupby(disabled, key=operator.itemgetter("resource_id"))
    resource_disabled = {}
    for resource_id, group in disabled_groups:
        resource_disabled[resource_id] = [
            {
                "id": stage["stage_id"],
                "name": stage["stage__name"],
            }
            for stage in group
        ]
    return resource_disabled


def get_resource_labels(resource_ids: List[int]) -> Dict[int, List]:
    queryset = ResourceLabel.objects.filter(resource_id__in=resource_ids).values(
        "api_label_id", "api_label__name", "resource_id"
    )

    resource_labels = defaultdict(list)
    for label in queryset:
        resource_labels[label["resource_id"]].append(
            {
                "id": label["api_label_id"],
                "name": label["api_label__name"],
            }
        )

    return resource_labels


def get_resource_labels_by_gateway(gateway_id: int) -> Dict[int, List]:
    resource_ids = list(Resource.objects.filter(gateway_id=gateway_id).values_list("id", flat=True))
    return get_resource_labels(resource_ids)


def get_resource_labels_by_ids(label_ids: List[int]) -> Dict[int, List]:
    queryset = ResourceLabel.objects.filter(api_label_id__in=label_ids).values(
        "api_label_id", "api_label__name", "resource_id"
    )

    resource_labels = defaultdict(list)
    for label in queryset:
        resource_labels[label["resource_id"]].append(
            {
                "id": label["api_label_id"],
                "name": label["api_label__name"],
            }
        )

    return resource_labels


def get_resource_use_stage_vars(resource: dict) -> dict:
    used_in_path = set()
    used_in_host = set()
    proxy_config = json.loads(resource["proxy"]["config"])
    proxy_path = proxy_config["path"]
    used_in_path.update(STAGE_VAR_PATTERN.findall(proxy_path))
    proxy_upstreams = proxy_config.get("upstreams")
    if proxy_upstreams:
        for host in proxy_upstreams["hosts"]:
            for match in STAGE_VAR_PATTERN.findall(host["host"]):
                used_in_host.add(match)
    return {
        "in_path": list(used_in_path),
        "in_host": list(used_in_host),
    }


def snapshot_resource(
    resource,
    as_dict=False,
    proxy_map=None,
    context_map=None,
    disabled_stage_map=None,
    api_label_map=None,
    plugin_map=None,
):
    data = {
        "id": resource.pk,
        "name": resource.name,
        "description": resource.description,
        "description_en": resource.description_en,
        "method": resource.method,
        "path": resource.path,
        "match_subpath": resource.match_subpath,
        "enable_websocket": resource.enable_websocket,
        "is_public": resource.is_public,
        "allow_apply_permission": resource.allow_apply_permission,
        "created_time": time.format(resource.created_time),
        "updated_time": time.format(resource.updated_time),
    }

    if proxy_map is None:
        data["proxy"] = Proxy.objects.get(resource_id=resource.id).snapshot(as_dict=True)
    else:
        data["proxy"] = proxy_map[resource.id]

    if data["proxy"]["type"] == ProxyTypeEnum.HTTP.value:
        data["stage_vars"] = get_resource_use_stage_vars(data)

    if context_map is None:
        contexts = Context.objects.filter(
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            scope_id=resource.pk,
        ).all()
        data["contexts"] = {c.type: c.snapshot(as_dict=True) for c in contexts}
    else:
        data["contexts"] = context_map[resource.pk]

    if disabled_stage_map is None:
        data["disabled_stages"] = list(
            StageResourceDisabled.objects.filter(resource=resource).values_list("stage__name", flat=True)
        )
    else:
        data["disabled_stages"] = disabled_stage_map.get(resource.pk, [])

    if api_label_map is None:
        data["api_labels"] = list(
            ResourceLabel.objects.filter(resource_id=resource.pk).values_list("api_label_id", flat=True)
        )
    else:
        data["api_labels"] = api_label_map.get(resource.pk, [])

    if plugin_map:
        data["plugins"] = plugin_map.get(resource.pk, [])

    if as_dict:
        return data

    return json.dumps(data)


def get_last_resource_updated_time(gateway_id: int) -> Optional[datetime.datetime]:
    return (
        Resource.objects.filter(gateway_id=gateway_id)
        .order_by("-updated_time")
        .values_list("updated_time", flat=True)
        .first()
    )


def make_resource_schema_version(resource_version: ResourceVersion):
    resource_ids = [resource["id"] for resource in resource_version.data if "id" in resource]
    resource_schemas = OpenAPIResourceSchema.objects.filter(resource_id__in=resource_ids)

    schema_list = [
        {
            "resource_id": resource_schema.resource.id,
            "schema": resource_schema.schema,
        }
        for resource_schema in resource_schemas
    ]
    if len(schema_list) > 0:
        OpenAPIResourceSchemaVersion.objects.create(
            resource_version=resource_version,
            schema=schema_list,
        )
