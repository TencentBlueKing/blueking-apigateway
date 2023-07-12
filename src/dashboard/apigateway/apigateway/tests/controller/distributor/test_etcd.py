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

from apigateway.controller.crds.v1beta1.models.gateway_config import BkGatewayConfig
from apigateway.controller.crds.v1beta1.models.gateway_plugin_metadata import BkGatewayPluginMetadata
from apigateway.controller.crds.v1beta1.models.gateway_resource import BkGatewayResource
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService
from apigateway.controller.crds.v1beta1.models.gateway_stage import BkGatewayStage
from apigateway.controller.distributor.etcd import EtcdDistributor
from apigateway.controller.registry.dict import DictRegistry


class TestEtcdDistributor:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.registry = DictRegistry()
        mocker.patch(
            "apigateway.controller.crds.v1beta1.convertors.resource.HttpResourceConvertor._save_resource_header_rewrite_plugin",
            return_value=None,
        )

    @pytest.mark.parametrize(
        "include_gateway_global_config, ignored_models, distributed_models",
        [
            [
                True,
                [],
                [BkGatewayConfig, BkGatewayPluginMetadata, BkGatewayStage, BkGatewayService, BkGatewayResource],
            ],
            [
                False,
                [BkGatewayConfig, BkGatewayPluginMetadata],
                [BkGatewayStage, BkGatewayService, BkGatewayResource],
            ],
        ],
    )
    def test_distribute(
        self, mocker, include_gateway_global_config, ignored_models, distributed_models, edge_release, micro_gateway
    ):
        distributor = EtcdDistributor(include_gateway_global_config=include_gateway_global_config)
        mocker.patch.object(distributor, "_get_registry", return_value=self.registry)
        assert distributor.distribute(
            release=edge_release,
            micro_gateway=micro_gateway,
        )

        for m in ignored_models:
            assert len(list(self.registry.iter_by_type(m))) == 0

        for m in distributed_models:
            assert len(list(self.registry.iter_by_type(m))) > 0

    @pytest.mark.parametrize(
        "include_gateway_global_config, ignored_models, revoked_models",
        [
            [
                True,
                [],
                [
                    BkGatewayConfig(metadata={"name": "gateway"}, spec={}),
                    BkGatewayPluginMetadata(metadata={"name": "metadata"}, spec={}),
                    BkGatewayStage(metadata={"name": "prod"}, spec={}),
                    BkGatewayService(metadata={"name": "service"}, spec={}),
                    BkGatewayResource(metadata={"name": "resource"}, spec={}),
                ],
            ],
            [
                False,
                [
                    BkGatewayConfig(metadata={"name": "gateway"}, spec={}),
                    BkGatewayPluginMetadata(metadata={"name": "metadata"}, spec={}),
                ],
                [
                    BkGatewayStage(metadata={"name": "prod"}, spec={}),
                    BkGatewayService(metadata={"name": "service"}, spec={}),
                    BkGatewayResource(metadata={"name": "resource"}, spec={}),
                ],
            ],
        ],
    )
    def test_revoke(
        self,
        faker,
        mocker,
        include_gateway_global_config,
        ignored_models,
        revoked_models,
        fake_gateway,
        fake_stage,
        micro_gateway,
    ):
        for resource in ignored_models + revoked_models:
            self.registry.apply_resource(resource)

        distributor = EtcdDistributor(include_gateway_global_config=include_gateway_global_config)
        mocker.patch.object(distributor, "_get_registry", return_value=self.registry)

        assert distributor.revoke(stage=fake_stage, micro_gateway=micro_gateway)

        for m in ignored_models:
            assert len(list(self.registry.iter_by_type(type(m)))) == 0

        for m in revoked_models:
            assert len(list(self.registry.iter_by_type(type(m)))) == 0
