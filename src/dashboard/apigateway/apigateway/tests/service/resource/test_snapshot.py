#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from ddf import G

from apigateway.core.constants import ResourceKindEnum
from apigateway.core.models import Proxy, Resource, Stage, StageResourceDisabled
from apigateway.service.resource import (
    filter_disabled_stages_by_gateway,
    get_last_resource_updated_time,
    get_resource_id_to_proxy_snapshot,
    get_resource_updated_time,
    get_resource_url_tmpl,
    get_resource_use_stage_vars,
    snapshot_resource,
)


def test_filter_disabled_stages_by_gateway(fake_gateway):
    resource1 = G(Resource, gateway=fake_gateway)
    resource2 = G(Resource, gateway=fake_gateway)
    stage_prod = G(Stage, gateway=fake_gateway, name="prod")
    stage_test = G(Stage, gateway=fake_gateway, name="test")

    G(StageResourceDisabled, resource=resource1, stage=stage_prod)
    G(StageResourceDisabled, resource=resource2, stage=stage_prod)
    G(StageResourceDisabled, resource=resource1, stage=stage_test)

    assert filter_disabled_stages_by_gateway(fake_gateway) == {
        resource1.id: [
            {"id": stage_prod.id, "name": stage_prod.name},
            {"id": stage_test.id, "name": stage_test.name},
        ],
        resource2.id: [
            {"id": stage_prod.id, "name": stage_prod.name},
        ],
    }


def test_get_resource_id_to_proxy_snapshot(fake_resource):
    result = get_resource_id_to_proxy_snapshot([fake_resource.id])

    assert fake_resource.id in result
    assert result[fake_resource.id]["type"] == "http"


def test_get_resource_use_stage_vars():
    assert get_resource_use_stage_vars(
        {
            "proxy": {
                "config": (
                    '{"path": "/users/{env.region}/", "upstreams": '
                    '{"hosts": [{"host": "api-{env.region}.example.com"}]}}'
                )
            }
        }
    ) == {
        "in_path": ["region"],
        "in_host": ["region"],
    }


def test_snapshot_resource(fake_resource):
    snapshot = snapshot_resource(fake_resource, as_dict=True)

    assert snapshot["id"] == fake_resource.id
    assert snapshot["kind"] == ResourceKindEnum.STANDARD.value
    assert snapshot["proxy"]["type"] == "http"
    assert "contexts" in snapshot


def test_snapshot_ai_resource_does_not_parse_standard_proxy_path(fake_resource):
    fake_resource.kind = ResourceKindEnum.AI.value
    fake_resource.save(update_fields=["kind"])
    proxy = Proxy.objects.get(resource=fake_resource)
    proxy._config = "{}"
    proxy.save(update_fields=["_config"])

    snapshot = snapshot_resource(fake_resource, as_dict=True)

    assert snapshot["kind"] == ResourceKindEnum.AI.value
    assert "stage_vars" not in snapshot


def test_get_last_resource_updated_time(fake_resource):
    assert get_last_resource_updated_time(fake_resource.gateway_id) == fake_resource.updated_time


def test_get_resource_updated_time(fake_resource):
    assert get_resource_updated_time(fake_resource.gateway_id, fake_resource.name)


def test_get_resource_updated_time_returns_empty_for_missing_resource(fake_gateway):
    assert get_resource_updated_time(fake_gateway.id, "missing") == ""


def test_get_resource_url_tmpl(settings):
    settings.API_RESOURCE_URL_TMPL = "http://bkapi.example.com/{api_name}/{stage_name}{resource_path}"

    assert get_resource_url_tmpl() == "http://bkapi.example.com/{api_name}/{stage_name}{resource_path}"
