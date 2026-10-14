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
from copy import deepcopy

import pytest
from ddf import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.plugin.constants import PluginBindingScopeEnum, PluginBindingSourceEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.biz.openapi import classify_resource_import_changes
from apigateway.biz.resource import ResourceAuthConfig, ResourceBackendConfig, ResourceData, ResourceHandler
from apigateway.core.models import Proxy, Resource


def test_new_resource_is_add_without_comparison_queries(fake_gateway, fake_resource_data, django_assert_num_queries):
    assert fake_resource_data.resource is None
    with django_assert_num_queries(0):
        changes = classify_resource_import_changes(fake_gateway, [fake_resource_data])
    assert changes == {fake_resource_data.name: "add"}


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize(
    "field,value",
    [
        ("legacy_upstreams", {}),
        ("legacy_upstreams", {"loadbalance": "roundrobin", "hosts": [{"host": "https://example.com"}]}),
        ("legacy_transform_headers", {}),
        ("legacy_transform_headers", {"set": {"x-token": "test"}, "delete": ["x-old"]}),
    ],
)
def test_legacy_config_skips_comparison(
    fake_gateway, fake_resource, fake_resource_data, django_assert_num_queries, existing, field, value
):
    if existing:
        fake_resource_data.resource = fake_resource
    assert fake_resource_data.backend_config is not None
    setattr(fake_resource_data.backend_config, field, value)

    with django_assert_num_queries(0):
        changes = classify_resource_import_changes(fake_gateway, [fake_resource_data])

    assert changes == {fake_resource_data.name: "update" if existing else "add"}


@pytest.mark.parametrize("existing", [False, True])
def test_classification_does_not_modify_import_data(fake_gateway, fake_resource, fake_resource_data, existing):
    if existing:
        fake_resource_data.resource = fake_resource
    original = deepcopy(fake_resource_data.model_dump())
    classify_resource_import_changes(fake_gateway, [fake_resource_data])
    assert fake_resource_data.model_dump() == original


@pytest.mark.parametrize("resource_count", [1, 10])
def test_existing_resources_use_bounded_comparison_queries(
    fake_gateway, fake_backend, django_assert_num_queries, resource_count
):
    resources = []
    plugin_type = G(PluginType, code="test-import-plugin")
    for index in range(resource_count):
        resource = G(Resource, gateway=fake_gateway, name=f"resource_{index}", method="GET", path=f"/resource/{index}")
        ResourceHandler.save_auth_config(
            resource.id,
            {
                "skip_auth_verification": False,
                "auth_verified_required": True,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
        )
        backend_config = ResourceBackendConfig(method="GET", path=f"/backend/{index}", timeout=30)
        G(Proxy, resource=resource, backend=fake_backend, _config=backend_config.model_dump_json(), type="http")
        label = G(APILabel, gateway=fake_gateway, name=f"label_{index}")
        G(ResourceLabel, resource=resource, api_label=label)
        plugin = G(PluginConfig, gateway=fake_gateway, type=plugin_type, yaml="enabled: true\n")
        G(
            PluginBinding,
            gateway=fake_gateway,
            scope_type=PluginBindingScopeEnum.RESOURCE.value,
            scope_id=resource.id,
            config=plugin,
            source=PluginBindingSourceEnum.USER_CREATE.value,
        )
        resources.append(
            ResourceData(
                **{name: getattr(resource, name) for name in ResourceData.basic_field_names()},
                resource=resource,
                auth_config=ResourceAuthConfig(),
                backend=fake_backend,
                backend_config=backend_config,
                metadata={"labels": [label.name]},
            )
        )

    with django_assert_num_queries(8):
        changes = classify_resource_import_changes(fake_gateway, resources)
    assert changes == {resource.name: "unchanged" for resource in resources}
