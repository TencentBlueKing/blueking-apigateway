#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
import json
from typing import ClassVar

import pytest
from ddf import G
from pytest import fixture

from apigateway.apps.plugin.models import PluginConfig, PluginType
from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.common.contexts import StageProxyHTTPContext
from apigateway.controller.crds.base import KubernetesResource
from apigateway.controller.crds.release_data.release_data import ReleaseData
from apigateway.controller.crds.v1beta1.convertor import CustomResourceConvertor
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor
from apigateway.controller.crds.v1beta1.convertors.gateway_config import GatewayConfigConvertor
from apigateway.controller.crds.v1beta1.convertors.plugin_metadata import PluginMetadataConvertor
from apigateway.controller.crds.v1beta1.convertors.resource import HttpResourceConvertor
from apigateway.controller.crds.v1beta1.convertors.service import ServiceConvertor
from apigateway.controller.crds.v1beta1.convertors.stage import StageConvertor
from apigateway.controller.registry.dict import DictRegistry
from apigateway.core.constants import APIHostingTypeEnum, StageStatusEnum
from apigateway.core.models import MicroGateway, Proxy, Release, ResourceVersion
from apigateway.utils.yaml import yaml_dumps


@fixture
def edge_gateway(fake_gateway):
    fake_gateway.hosting_type = APIHostingTypeEnum.MICRO.value
    fake_gateway.is_public = True
    fake_gateway.save()

    GatewayJWTHandler.create_jwt(fake_gateway)

    return fake_gateway


@fixture
def micro_gateway_http_domain(faker):
    return faker.domain_name()


@fixture
def micro_gateway_http_port(faker):
    return faker.pyint(min_value=1, max_value=65535)


@fixture
def micro_gateway_http_path(faker):
    return f"/{faker.word()}"


@fixture
def micro_gateway_http_url(micro_gateway_http_domain, micro_gateway_http_port, micro_gateway_http_path):
    return f"http://{micro_gateway_http_domain}:{micro_gateway_http_port}{micro_gateway_http_path}"


@fixture
def micro_gateway(faker, micro_gateway_http_url, micro_gateway_schema, settings):
    gateway = G(
        MicroGateway,
        name=faker.color_name(),
        schema=micro_gateway_schema,
        is_shared=True,
        _config=json.dumps(
            {
                "bcs": {
                    "project_id": faker.color_name(),
                    "project_name": faker.color_name(),
                    "cluster_id": faker.color_name(),
                    "namespace": faker.color_name(),
                    "chart_name": faker.color_name(),
                    "chart_version": "1.0.0",
                    "release_name": faker.color_name(),
                },
                "metadata": {
                    "is_managed": True,
                },
                "http": {
                    "http_url": micro_gateway_http_url,
                },
                "jwt_auth": {
                    "secret_key": faker.password(),
                },
            }
        ),
    )

    settings.DEFAULT_MICRO_GATEWAY_ID = gateway.id
    return gateway


@fixture
def backend_service_http_scheme(faker):
    return faker.random_element(["http", "https"])


@fixture
def backend_service_http_domain(faker):
    return faker.domain_name()


@fixture
def backend_service_http_port(faker):
    return faker.pyint(min_value=1, max_value=65535)


@fixture
def backend_service_http_host(backend_service_http_scheme, backend_service_http_domain, backend_service_http_port):
    return f"{backend_service_http_scheme}://{backend_service_http_domain}:{backend_service_http_port}"


@fixture
def edge_gateway_stage(fake_stage, micro_gateway):
    fake_stage.micro_gateway = micro_gateway
    fake_stage.status = StageStatusEnum.ACTIVE.value
    fake_stage.vars = {"stage_name": fake_stage.name}
    fake_stage.save()

    return fake_stage


@fixture
def edge_gateway_stage_context_proxy_http(faker, edge_gateway_stage, backend_service_http_host):
    context = StageProxyHTTPContext()
    instance, _ = context.save(
        edge_gateway_stage.id,
        {
            "timeout": faker.random_int(),
            "upstreams": {"loadbalance": "roundrobin", "hosts": [{"host": backend_service_http_host, "weight": 100}]},
            "transform_headers": {
                "set": {
                    "X-Set-By-Stage": edge_gateway_stage.name,
                },
                "delete": [
                    "X-Del-By-Stage",
                ],
            },
        },
    )
    return instance


@fixture
def edge_resource_overwrite_stage(fake_resource1):
    return fake_resource1


@fixture
def edge_resource_overwrite_stage_proxy(faker, edge_resource_overwrite_stage, backend_service_http_host):
    proxy = Proxy.objects.get(resource=edge_resource_overwrite_stage)
    proxy.config = {
        "method": faker.http_method(),
        "path": faker.uri_path(),
        "match_subpath": False,
        "timeout": faker.random_int(),
        "upstreams": {
            "loadbalance": "roundrobin",
            "hosts": [{"host": backend_service_http_host, "weight": 100}],
        },
        "transform_headers": {
            "set": {
                "X-Set-By-Resource": edge_resource_overwrite_stage.name,
            },
            "delete": [
                "X-Del-By-Resource",
            ],
        },
    }
    proxy.save()
    return proxy


@fixture
def edge_resource_inherit_stage(fake_resource2):
    return fake_resource2


@fixture
def edge_resource_inherit_stage_proxy(faker, edge_resource_inherit_stage):
    proxy = Proxy.objects.get(resource=edge_resource_inherit_stage)
    proxy.config = {
        "method": faker.http_method(),
        "path": faker.uri_path(),
        "match_subpath": False,
        "timeout": 0,
        "upstreams": {},
        "transform_headers": {
            "set": {},
            "delete": [],
        },
    }
    proxy.save()
    return proxy


@fixture
def edge_resources(
    faker,
    edge_gateway_stage_context_proxy_http,
    edge_resource_overwrite_stage,
    edge_resource_overwrite_stage_proxy,
    edge_resource_inherit_stage,
    edge_resource_inherit_stage_proxy,
):
    return {
        "overwrite_stage_hosts": edge_resource_overwrite_stage,
        "use_stage_hosts": edge_resource_inherit_stage,
    }


@fixture
def edge_resource_version(faker, edge_gateway, edge_resources):
    return G(
        ResourceVersion,
        name=faker.color_name(),
        title=faker.numerify("v!.!.%"),
        gateway=edge_gateway,
        _data=json.dumps(ResourceVersionHandler.make_version(edge_gateway)),
    )


@fixture
def edge_resource_overwrite_stage_snapshot(edge_resource_version, edge_resource_overwrite_stage):
    for i in edge_resource_version.data:
        if i["id"] == edge_resource_overwrite_stage.id:
            return i
    return None


@fixture
def edge_resource_inherit_stage_snapshot(edge_resource_version, edge_resource_inherit_stage):
    for i in edge_resource_version.data:
        if i["id"] == edge_resource_inherit_stage.id:
            return i
    return None


@fixture
def edge_release(faker, edge_gateway, edge_gateway_stage, edge_resource_version):
    return Release.objects.save_release(
        edge_gateway,
        edge_gateway_stage,
        edge_resource_version,
        faker.bothify("comment: ????"),
        faker.user_name(),
    )


@fixture
def fake_release_data(edge_release):
    return ReleaseData(edge_release)


class DummyConvertor(BaseConvertor):
    def convert(self):
        pass


@fixture
def fake_base_convertor(fake_release_data, micro_gateway):
    return DummyConvertor(fake_release_data, micro_gateway)


@fixture
def fake_gateway_config_convertor(fake_release_data, micro_gateway):
    return GatewayConfigConvertor(fake_release_data, micro_gateway)


@fixture
def fake_stage_convertor(fake_release_data, micro_gateway):
    return StageConvertor(fake_release_data, micro_gateway)


@fixture
def fake_service_convertor(fake_release_data, micro_gateway):
    return ServiceConvertor(fake_release_data, micro_gateway)


@fixture
def fake_plugin_metadata_convertor(fake_release_data, micro_gateway):
    return PluginMetadataConvertor(fake_release_data, micro_gateway)


@fixture
def edge_custom_release_convertor(edge_release, micro_gateway):
    return CustomResourceConvertor(release=edge_release, micro_gateway=micro_gateway)


@fixture
def fake_http_resource_convertor(fake_release_data, micro_gateway, fake_service_convertor):
    return HttpResourceConvertor(fake_release_data, micro_gateway, fake_service_convertor.convert())


class TestingCustomResource(KubernetesResource):
    kind: ClassVar[str] = "TestingCustomResource"
    value: str


@fixture
def resource_type():
    return TestingCustomResource


@fixture
def fake_custom_resource(faker, resource_type):
    return resource_type(metadata={"name": faker.pystr()}, value=faker.pystr())


@fixture
def dict_registry():
    return DictRegistry(namespace="")


@fixture
def mock_etcd_registry(mocker):
    registry = DictRegistry(namespace="")
    mocker.patch("apigateway.controller.registry.etcd.EtcdRegistry", return_value=registry)

    return registry


@pytest.fixture
def edge_plugin_type():
    return G(PluginType, schema=None)


@fixture
def edge_plugin_config(edge_gateway, edge_plugin_type):
    return G(
        PluginConfig,
        gateway=edge_gateway,
        type=edge_plugin_type,
        yaml=yaml_dumps({"rates": {"__default": [{"period": 60, "tokens": 100}]}}),
    )
