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

import json
from copy import deepcopy
from typing import Any, Dict, List

from apigateway.apps.openapi.models import OpenAPIResourceSchema
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginBindingSourceEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.apps.support.constants import OpenAPIFormatEnum
from apigateway.biz.resource import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.core.models import Gateway, Proxy
from apigateway.service.contexts import ResourceAuthContext
from apigateway.service.resource import get_resource_id_to_labels
from apigateway.service.resource_version import OpenAPIExportManager
from apigateway.utils.yaml import yaml_loads

from .constants import ResourceImportChangeTypeEnum


def classify_resource_import_changes(gateway: Gateway, resources: List[ResourceData]) -> None:
    """Add change_type to metadata; only existing resources need configuration reads.

    Comparison covers imported configuration, excluding Markdown documents and
    operational metadata. Missing plugins retain user-created bindings, matching
    PluginSynchronizer. Legacy migrations conservatively count as updates.
    """
    existing_resources = []
    for resource_data in resources:
        if resource_data.resource is None:
            resource_data.metadata["change_type"] = ResourceImportChangeTypeEnum.ADD.value
        else:
            existing_resources.append(resource_data)
    if not existing_resources:
        return

    resource_ids = [data.resource.id for data in existing_resources if data.resource]
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

    for resource_data in existing_resources:
        resource = resource_data.resource
        assert resource
        proxy = proxies.get(resource.id)
        current_plugins = {
            binding.config.type.code: binding.config.config for binding in bindings.get(resource.id, [])
        }
        imported_plugins = {
            binding.config.type.code: binding.config.config
            for binding in bindings.get(resource.id, [])
            if binding.source != PluginBindingSourceEnum.YAML_IMPORT.value
        }
        imported_plugins.update(
            {
                plugin.type: yaml_loads(plugin.yaml.encode().decode("unicode_escape"))
                for plugin in resource_data.plugin_configs or []
            }
        )
        unchanged = (
            proxy is not None
            and resource_data.basic_data
            == {name: getattr(resource, name) for name in ResourceData.basic_field_names()}
            and resource_data.auth_config.model_dump()
            == ResourceAuthConfig.model_validate(auth_configs[resource.id]).model_dump()
            and resource_data.backend is not None
            and resource_data.backend.id == proxy.backend_id
            and _backend_config_unchanged(resource_data.backend_config, proxy.config)
            and set(resource_data.metadata.get("labels", []))
            == {label["name"] for label in labels.get(resource.id, [])}
            and _configuration_equal(imported_plugins, current_plugins)
            and _configuration_equal(
                _normalize_schema(resource_data, resource_data.openapi_schema),
                _normalize_schema(resource_data, schemas.get(resource.id, {})),
            )
        )
        resource_data.metadata["change_type"] = (
            ResourceImportChangeTypeEnum.UNCHANGED.value if unchanged else ResourceImportChangeTypeEnum.UPDATE.value
        )


def _backend_config_unchanged(imported: ResourceBackendConfig | None, current: Dict[str, Any]) -> bool:
    if imported is None:
        return current == {}
    if imported.legacy_upstreams or imported.legacy_transform_headers:
        return False
    return imported.model_dump() == ResourceBackendConfig.model_validate(current).model_dump()


def _normalize_schema(resource: ResourceData, schema: Dict[str, Any]) -> dict:
    # Use the exporter's defaults on both sides so original exports compare equal,
    # including resources without a stored schema and Swagger 2.0 conversions.
    content = OpenAPIExportManager(include_bk_apigateway_resource=False).export_openapi(
        [
            {
                "name": resource.name,
                "description": resource.description,
                "method": resource.method,
                "path": resource.path,
                "openapi_schema": deepcopy(schema),
            }
        ],
        file_type=OpenAPIFormatEnum.JSON.value,
    )
    # The document's root version is selected from the first exported resource;
    # mixed-version exports must not make unchanged operation content differ.
    return {"paths": json.loads(content)["paths"], "none_schema": schema.get("none_schema", False)}


def _configuration_equal(source: Any, target: Any) -> bool:
    # JSON booleans and numbers are distinct even though Python True == 1.
    if isinstance(source, bool) or isinstance(target, bool):
        return type(source) is type(target) and source == target
    if isinstance(source, dict) and isinstance(target, dict):
        return source.keys() == target.keys() and all(
            _configuration_equal(value, target[key]) for key, value in source.items()
        )
    if isinstance(source, list) and isinstance(target, list):
        return len(source) == len(target) and all(
            _configuration_equal(left, right) for left, right in zip(source, target)
        )
    return source == target
