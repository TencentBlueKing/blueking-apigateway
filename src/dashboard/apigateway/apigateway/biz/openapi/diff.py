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
"""Compare validated resource imports with editable configuration without saving them."""

from copy import deepcopy
from typing import Any, Dict, List

from apigateway.apps.openapi.models import OpenAPIResourceSchema
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginBindingSourceEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.biz.resource import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.biz.resource_version import ResourceConfigurationDiffer
from apigateway.core.models import Gateway, Proxy
from apigateway.service.contexts import ResourceAuthContext
from apigateway.service.resource import get_resource_id_to_labels
from apigateway.service.resource_version import OpenAPIExportManager
from apigateway.utils.yaml import yaml_loads

from .constants import ResourceImportChangeTypeEnum


def classify_resource_import_changes(gateway: Gateway, resources: List[ResourceData]) -> Dict[str, str]:
    """Return change types by validated unique resource name without modifying imports.

    Comparison covers imported configuration, excluding Markdown documents and
    operational metadata, including Schema version metadata. Consumers that skip
    imports must handle Schema version changes separately. Legacy configuration
    on existing resources is always an update and skips comparison reads.
    Missing plugins retain user-created bindings, matching PluginSynchronizer.
    """
    change_types = {}
    existing_resources = []
    for resource_data in resources:
        backend_config = resource_data.backend_config
        if resource_data.resource is None:
            change_types[resource_data.name] = ResourceImportChangeTypeEnum.ADD.value
        elif backend_config is not None and (
            backend_config.legacy_upstreams is not None or backend_config.legacy_transform_headers is not None
        ):
            change_types[resource_data.name] = ResourceImportChangeTypeEnum.UPDATE.value
        else:
            existing_resources.append((resource_data, resource_data.resource))
    if not existing_resources:
        return change_types

    resource_ids = [resource.id for _, resource in existing_resources]
    proxies = {proxy.resource_id: proxy for proxy in Proxy.objects.filter(resource_id__in=resource_ids)}
    auth_configs = ResourceAuthContext().get_resource_id_to_auth_config(resource_ids)
    labels = get_resource_id_to_labels(resource_ids)
    schemas = dict(
        OpenAPIResourceSchema.objects.filter(resource_id__in=resource_ids).values_list("resource_id", "schema")
    )
    bindings = PluginBinding.objects.query_scope_id_to_bindings(
        gateway_id=gateway.id,
        scope_type=PluginBindingScopeEnum.RESOURCE,
        scope_ids=resource_ids,
    )

    for resource_data, resource in existing_resources:
        proxy = proxies.get(resource.id)
        backend_config = resource_data.backend_config
        if proxy is None:
            change_types[resource_data.name] = ResourceImportChangeTypeEnum.UPDATE.value
            continue
        current_plugins = {
            binding.config.type.code: binding.config.config for binding in bindings.get(resource.id, [])
        }
        imported_plugins = {
            binding.config.type.code: current_plugins[binding.config.type.code]
            for binding in bindings.get(resource.id, [])
            if binding.source != PluginBindingSourceEnum.YAML_IMPORT.value
        }
        imported_plugins.update(
            {
                plugin.type: yaml_loads(plugin.yaml.encode().decode("unicode_escape"))
                for plugin in resource_data.plugin_configs or []
            }
        )
        current = ResourceConfigurationDiffer.model_validate(
            {
                **{name: getattr(resource, name) for name in ResourceData.basic_field_names()},
                "auth_config": ResourceAuthConfig.model_validate(auth_configs[resource.id]).model_dump(),
                "backend_id": proxy.backend_id,
                "backend_config": (
                    ResourceBackendConfig.model_validate(proxy.config).model_dump()
                    if backend_config is not None
                    else proxy.config
                ),
                "labels": {label["name"] for label in labels.get(resource.id, [])},
                "plugins": current_plugins,
                "openapi_schema": _normalize_schema(resource_data, schemas.get(resource.id, {})),
            }
        )
        imported = ResourceConfigurationDiffer.model_validate(
            {
                **resource_data.basic_data,
                "auth_config": resource_data.auth_config.model_dump(),
                "backend_id": resource_data.backend.id if resource_data.backend else None,
                "backend_config": backend_config.model_dump() if backend_config is not None else {},
                "labels": set(resource_data.metadata.get("labels", [])),
                "plugins": imported_plugins,
                "openapi_schema": _normalize_schema(resource_data, resource_data.openapi_schema),
            }
        )
        source_diff, target_diff = current.diff(imported)
        change_types[resource_data.name] = (
            ResourceImportChangeTypeEnum.UPDATE.value
            if source_diff or target_diff
            else ResourceImportChangeTypeEnum.UNCHANGED.value
        )
    return change_types


def _normalize_schema(resource: ResourceData, schema: Dict[str, Any]) -> dict:
    # Use the exporter's defaults on both sides so original exports compare equal,
    # including resources without a stored schema and Swagger 2.0 conversions.
    content = OpenAPIExportManager(include_bk_apigateway_resource=False).get_openapi_content(
        [
            {
                "name": resource.name,
                "description": resource.description,
                "method": resource.method,
                "path": resource.path,
                "openapi_schema": deepcopy(schema),
            }
        ],
    )
    # The document's root version is selected from the first exported resource;
    # mixed-version exports must not make unchanged operation content differ.
    return {"paths": content["paths"], "none_schema": schema.get("none_schema", False)}
