#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from apigateway.core.models import BackendConfig


class TestServiceConvertor:
    def test_convert(
        self,
        edge_gateway,
        edge_gateway_stage,
        fake_backend,
        fake_service_convertor,
        backend_service_http_scheme,
    ):
        services = fake_service_convertor.convert()
        assert len(services) == 1

        service = services[0]

        stage_id = edge_gateway_stage.id
        stage_name = edge_gateway_stage.name
        backend_id = fake_backend.id

        # assert metadata
        metadata = service.metadata
        assert 0 < len(metadata.name) <= 64

        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name
        assert metadata.get_label("service-type") == "stage-backend"
        assert metadata.get_label("backend-id") == str(backend_id)

        # assert spec
        spec = service.spec
        assert spec.name == f"_stage_service_{stage_name}_{backend_id}"
        assert spec.id == f"{stage_id}-{backend_id}"
        assert spec.description.startswith(f"{stage_name}/{stage_id}" + ": " + edge_gateway_stage.description[:32])

        assert spec.upstream.type == UpstreamTypeEnum.ROUNDROBIN
        assert spec.upstream.scheme.value == backend_service_http_scheme
        assert len(spec.upstream.nodes) == 1

        backend_config_obj = BackendConfig.objects.get(
            gateway=edge_gateway,
            backend=fake_backend,
            stage=edge_gateway_stage,
        )
        backend_config = backend_config_obj.config

        assert spec.upstream.timeout.connect == backend_config["timeout"]
        assert spec.upstream.timeout.read == backend_config["timeout"]
        assert spec.upstream.timeout.send == backend_config["timeout"]

        node = spec.upstream.nodes[0]
        assert node.host == backend_config["hosts"][0]["host"]
        assert node.weight == backend_config["hosts"][0]["weight"]

    def test_convert_no_backend_config(self, edge_gateway, edge_gateway_stage, fake_backend, fake_service_convertor):
        # drop the backend config
        BackendConfig.objects.get(
            gateway=edge_gateway,
            backend=fake_backend,
            stage=edge_gateway_stage,
        ).delete()

        services = fake_service_convertor.convert()
        assert len(services) == 0

    def test_convert_no_hosts(self, edge_gateway, edge_gateway_stage, fake_backend, fake_service_convertor):
        # drop the hosts
        bc = BackendConfig.objects.get(
            gateway=edge_gateway,
            backend=fake_backend,
            stage=edge_gateway_stage,
        )
        bc.config["hosts"] = []
        bc.save()

        with pytest.raises(ValueError):
            fake_service_convertor.convert()
