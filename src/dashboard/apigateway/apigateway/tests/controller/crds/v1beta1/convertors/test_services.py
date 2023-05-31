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
import pytest

from apigateway.controller.crds.constants import UpstreamTypeEnum
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Context


class TestServiceConvertor:
    def test_convert(
        self,
        edge_gateway,
        edge_gateway_stage,
        edge_gateway_stage_context_proxy_http,
        fake_service_convertor,
        backend_service_http_scheme,
        backend_service_http_domain,
    ):
        services = fake_service_convertor.convert()
        assert len(services) == 1

        service = services[0]
        assert service.spec.name.startswith("_")

        metadata = service.metadata
        assert 0 < len(metadata.name) <= 64

        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name

        spec = service.spec
        assert spec.description == edge_gateway_stage.description
        assert spec.upstream.type == UpstreamTypeEnum.ROUNDROBIN
        assert spec.upstream.scheme.value == backend_service_http_scheme

        config = edge_gateway_stage_context_proxy_http.config
        assert spec.upstream.timeout.connect == config["timeout"]
        assert spec.upstream.timeout.read == config["timeout"]
        assert spec.upstream.timeout.send == config["timeout"]

        assert len(spec.upstream.nodes) == 1
        node = spec.upstream.nodes[0]
        host = config["upstreams"]["hosts"][0]

        assert node.host == backend_service_http_domain
        assert node.weight == host["weight"]

    def test_convert__error(self, mocker, fake_service_convertor):
        fake_stage = fake_service_convertor._release_data.stage
        context = Context.objects.get(
            scope_id=fake_stage.pk,
            scope_type=ContextScopeTypeEnum.STAGE.value,
            type=ContextTypeEnum.STAGE_PROXY_HTTP.value,
        )
        context.config = {
            "upstreams": {
                "hosts": [{"host": "example.com"}],
                "loadbalance": "roundrobin",
            },
            "transform_headers": {},
            "timeout": 30,
        }
        context.save()

        with pytest.raises(ValueError):
            fake_service_convertor.convert()

    def test_convert_checks(
        self,
        edge_gateway,
        fake_service_convertor,
        settings,
    ):
        settings.MICRO_GATEWAY_STAGE_UPSTREAM_CHECKS = {
            edge_gateway.name: {
                "active": {
                    "type": "http",
                    "concurrency": 3,
                    "http_path": "/healthz",
                }
            }
        }
        services = fake_service_convertor.convert()

        assert len(services) == 1
        service = services[0]

        spec = service.spec
        assert spec.upstream.checks.active.type.value == "http"
        assert spec.upstream.checks.active.concurrency == 3
        assert spec.upstream.checks.active.http_path == "/healthz"
