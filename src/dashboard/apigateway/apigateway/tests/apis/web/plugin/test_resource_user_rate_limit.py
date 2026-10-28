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
from pathlib import Path

import pytest
from django.core.management import call_command
from django_dynamic_fixture import G

from apigateway.apps.data_plane.constants import DataPlaneApisixVersionEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.controller.convertor import RouteConvertor
from apigateway.controller.release_data import ReleaseData
from apigateway.core.constants import ResourceVersionSchemaEnum
from apigateway.core.models import Release, ResourceVersion
from apigateway.service.plugin import PluginConfigYamlValidator
from apigateway.utils.yaml import yaml_dumps, yaml_loads

pytestmark = pytest.mark.django_db

PLUGIN_CODE = "bk-resource-user-rate-limit"


@pytest.fixture
def resource_user_rate_limit_type():
    call_command("loaddata", Path(__file__).parents[4] / "fixtures/plugins.yaml", verbosity=0)
    return PluginType.objects.get(code=PLUGIN_CODE)


@pytest.mark.parametrize("scope_type", ["stage", "resource"])
def test_catalog_scope(request_view, fake_gateway, fake_resource, resource_user_rate_limit_type, scope_type):
    response = request_view(
        "GET",
        "plugins.types",
        gateway=fake_gateway,
        path_params={"gateway_id": fake_gateway.id},
        data={"scope_type": scope_type, "scope_id": fake_resource.id},
    )
    assert response.status_code == 200
    codes = [item["code"] for item in response.json()["data"]["results"]]
    assert codes.count(PLUGIN_CODE) == (1 if scope_type == "resource" else 0)
    assert resource_user_rate_limit_type.priority == 17654


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"rates": {}},
        {"rates": {"alice": [{"period": 60, "tokens": 10}]}},
        {"rates": {"__default": []}},
        {
            "rates": {
                "__default": [{"period": 60, "tokens": 100}],
                "alice": [{"period": 1, "tokens": 10}, {"period": 60, "tokens": 300}],
                "bob": [],
            },
            "allow_degradation": False,
            "show_limit_quota_header": False,
        },
    ],
)
def test_accept_native_config(resource_user_rate_limit_type, config):
    PluginConfigYamlValidator().validate(PLUGIN_CODE, yaml_dumps(config), resource_user_rate_limit_type.schema.schema)


@pytest.mark.parametrize("identity", ["__default", "alice"])
@pytest.mark.parametrize(
    "rate",
    [
        {"period": 60},
        {"tokens": 10},
        {"period": 0, "tokens": 10},
        {"period": -1, "tokens": 10},
        {"period": 1.5, "tokens": 10},
        {"period": "60", "tokens": 10},
        {"period": 60, "tokens": 0},
        {"period": 60, "tokens": -1},
        {"period": 60, "tokens": 1.5},
    ],
)
def test_reject_invalid_rate(resource_user_rate_limit_type, identity, rate):
    with pytest.raises(ValueError):
        PluginConfigYamlValidator().validate(
            PLUGIN_CODE, yaml_dumps({"rates": {identity: [rate]}}), resource_user_rate_limit_type.schema.schema
        )


@pytest.mark.parametrize(
    "config",
    [
        {"rates": []},
        {"rates": {"alice": {"period": 60, "tokens": 10}}},
        {"allow_degradation": "true"},
        {"show_limit_quota_header": 1},
        [],
    ],
)
def test_reject_invalid_config(resource_user_rate_limit_type, config):
    with pytest.raises(ValueError):
        PluginConfigYamlValidator().validate(
            PLUGIN_CODE, yaml_dumps(config), resource_user_rate_limit_type.schema.schema
        )


def test_native_config_round_trip_and_publish(
    request_view, fake_gateway, fake_resource, fake_stage, fake_backend, resource_user_rate_limit_type
):
    path_params = {
        "gateway_id": fake_gateway.id,
        "scope_type": "resource",
        "scope_id": fake_resource.id,
        "code": PLUGIN_CODE,
    }
    payload = "# Native APISIX configuration\nrates:\n  __default: [{period: 60, tokens: 100}]\n  alice: []"
    response = request_view(
        "POST",
        "plugins.config.create",
        gateway=fake_gateway,
        path_params=path_params,
        data={"type_id": resource_user_rate_limit_type.id, "name": "user quota", "yaml": payload},
    )
    assert response.status_code == 201
    plugin = PluginConfig.objects.get(type=resource_user_rate_limit_type)
    assert plugin.yaml == payload
    path_params["id"] = plugin.id
    response = request_view("GET", "plugins.config.details", gateway=fake_gateway, path_params=path_params)
    assert response.status_code == 200
    assert response.json()["data"]["yaml"] == payload

    payload += "\nallow_degradation: false\nshow_limit_quota_header: false"
    response = request_view(
        "PUT",
        "plugins.config.details",
        gateway=fake_gateway,
        path_params=path_params,
        data={"type_id": resource_user_rate_limit_type.id, "name": "user quota", "yaml": payload},
    )
    assert response.status_code == 200
    plugin.refresh_from_db()
    assert plugin.yaml == payload

    app_plugin = G(
        PluginConfig,
        gateway=fake_gateway,
        type=PluginType.objects.get(code="bk-rate-limit"),
        yaml="rates: {__default: [{period: 60, tokens: 200}]}",
    )
    G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=fake_resource.id, config=app_plugin)
    version = G(ResourceVersion, gateway=fake_gateway, schema_version=ResourceVersionSchemaEnum.V2.value)
    version.data = ResourceVersionHandler.make_version(fake_gateway)
    version.save()
    release = G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=version)
    release_data = ReleaseData(release)
    routes = RouteConvertor(
        release_data=release_data,
        backend_service_mapping={fake_backend.id: "test-service"},
        publish_id=0,
        apisix_version=DataPlaneApisixVersionEnum.V3_13.value,
    ).convert()
    assert len(routes) == 1
    plugins = routes[0].plugins
    assert plugins[PLUGIN_CODE].model_dump(exclude_none=True) == yaml_loads(payload)
    assert plugins["bk-resource-rate-limit"].model_dump(exclude_none=True) == app_plugin.config
    assert "bk-rate-limit" not in plugins
    assert PLUGIN_CODE not in {plugin.name for plugin in release_data.get_stage_plugins()}


@pytest.mark.parametrize("method", ["POST", "PUT"])
def test_invalid_config_is_not_saved(request_view, fake_gateway, fake_resource, resource_user_rate_limit_type, method):
    path_params = {
        "gateway_id": fake_gateway.id,
        "scope_type": "resource",
        "scope_id": fake_resource.id,
        "code": PLUGIN_CODE,
    }
    if method == "PUT":
        plugin = G(PluginConfig, gateway=fake_gateway, type=resource_user_rate_limit_type, yaml="{}")
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=fake_resource.id, config=plugin)
        path_params["id"] = plugin.id
    response = request_view(
        method,
        "plugins.config.create" if method == "POST" else "plugins.config.details",
        gateway=fake_gateway,
        path_params=path_params,
        data={
            "type_id": resource_user_rate_limit_type.id,
            "name": "invalid quota",
            "yaml": "rates: {__default: [{period: 0, tokens: 100}]}",
        },
    )
    assert response.status_code == 400
    configs = list(PluginConfig.objects.filter(type=resource_user_rate_limit_type).values_list("yaml", flat=True))
    assert configs == (["{}"] if method == "PUT" else [])
