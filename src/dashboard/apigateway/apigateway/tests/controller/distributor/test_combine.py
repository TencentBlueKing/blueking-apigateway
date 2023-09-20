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
from ddf import G

from apigateway.controller.distributor.combine import CombineDistributor
from apigateway.core.models import MicroGateway


class TestDistributor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, mocker):
        self.helm_distributor = mocker.MagicMock()
        self.helm_distributor_type = mocker.MagicMock(return_value=self.helm_distributor)
        self.etcd_distributor = mocker.MagicMock()
        self.etcd_distributor_type = mocker.MagicMock(return_value=self.etcd_distributor)
        self.distributor = CombineDistributor(
            helm_distributor_type=self.helm_distributor_type,
            etcd_distributor_type=self.etcd_distributor_type,
        )

    def check_foreach_distributor_orders(self, stage, micro_gateway, orders):
        def callback(distributor, micro_gateway):
            assert (distributor, micro_gateway) == orders.pop(0)

        self.distributor.foreach_distributor(stage, micro_gateway, callback)
        assert not orders

    def test_foreach_distributor_for_managed_edge_gateway(self, mocker, edge_gateway_stage, micro_gateway):
        edge_gateway_stage.micro_gateway = G(
            MicroGateway,
            is_shared=False,
            is_managed=True,
        )
        edge_gateway_stage.save()

        callback = mocker.MagicMock()
        self.distributor.foreach_distributor(edge_gateway_stage, micro_gateway, callback)

        assert callback.call_count == 1
        # callback.assert_any_call(self.etcd_distributor, micro_gateway)
        callback.assert_any_call(self.helm_distributor, edge_gateway_stage.micro_gateway)

        self.helm_distributor_type.assert_called_once_with(generate_chart=False)
        # self.etcd_distributor_type.assert_called_once_with(include_gateway_global_config=False)

    def test_foreach_distributor_managed_shared_gateway(self, mocker, edge_gateway_stage, micro_gateway):
        assert edge_gateway_stage.micro_gateway == micro_gateway

        callback = mocker.MagicMock()
        self.distributor.foreach_distributor(edge_gateway_stage, micro_gateway, callback)

        callback.assert_called_once_with(self.etcd_distributor, micro_gateway)

        self.etcd_distributor_type.assert_called_once_with(include_gateway_global_config=True)

    def test_foreach_distributor_shared_gateway(self, mocker, fake_stage, micro_gateway):
        assert fake_stage.micro_gateway is None

        callback = mocker.MagicMock()
        self.distributor.foreach_distributor(fake_stage, micro_gateway, callback)

        callback.assert_called_once_with(self.etcd_distributor, micro_gateway)

        self.etcd_distributor_type.assert_called_once_with(include_gateway_global_config=False)
