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

from apigateway.controller import tasks
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import Gateway, MicroGatewayReleaseHistory, ReleaseHistory


@pytest.fixture()
def release_history():
    return G(ReleaseHistory)


@pytest.fixture()
def micro_gateway_release_history():
    return G(MicroGatewayReleaseHistory)


class TestReleaseGaterwayByHelm:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.distributor = mocker.MagicMock()
        self.distributor_factory = mocker.patch("apigateway.controller.tasks.release.HelmDistributor")
        self.distributor_factory.return_value = self.distributor

        self.chart_helper = mocker.MagicMock()
        self.chart_helper_factory = mocker.patch("apigateway.controller.tasks.release.ChartHelper")
        self.chart_helper_factory.return_value = self.chart_helper

        self.release_helper = mocker.MagicMock()
        self.release_helper_factory = mocker.patch("apigateway.controller.tasks.release.ReleaseHelper")
        self.release_helper_factory.return_value = self.release_helper

    def test_micro_gateway_not_exist(self, edge_release, micro_gateway_release_history):
        edge_release.stage.micro_gateway.delete()

        assert not tasks.release_gateway_by_helm(
            edge_release.id, micro_gateway_release_history.id, "user", {"bk_ticket": "access_token"}
        )

    def test_success(self, mocker, edge_release, micro_gateway, micro_gateway_release_history):
        self.distributor.distribute.return_value = True, ""

        username = "user"
        access_token = "access_token"
        assert tasks.release_gateway_by_helm(
            edge_release.id, micro_gateway_release_history.id, username, {"bk_ticket": access_token}
        )

        self.chart_helper_factory.assert_called_once_with(user_credentials={"bk_ticket": access_token})
        self.release_helper_factory.assert_called_once_with(user_credentials={"bk_ticket": access_token})
        self.distributor_factory.assert_called_once_with(
            chart_helper=self.chart_helper,
            release_helper=self.release_helper,
            generate_chart=True,
            operator=username,
        )

        micro_gateway_release_history.refresh_from_db()
        micro_gateway_release_history.status = ReleaseStatusEnum.SUCCESS.value

    def test_fail(self, mocker, edge_release, micro_gateway, micro_gateway_release_history):
        self.distributor.distribute.return_value = False, "Fail"

        username = "user"
        access_token = "access_token"
        assert not tasks.release_gateway_by_helm(
            edge_release.id, micro_gateway_release_history.id, username, {"bk_ticket": access_token}
        )

        micro_gateway_release_history.refresh_from_db()
        micro_gateway_release_history.status = ReleaseStatusEnum.FAILURE.value


class TestReleaseGatewayByRegistry:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.distributor = mocker.MagicMock()
        self.distributor_factory = mocker.patch(
            "apigateway.controller.tasks.release.EtcdDistributor", return_value=self.distributor
        )

    def test_success_for_shared_gateway(
        self, mocker, edge_release, micro_gateway, micro_gateway_release_history, release_history
    ):
        edge_release.gateway = G(Gateway)
        edge_release.save()

        self.distributor.distribute.return_value = True, ""

        assert tasks.release_gateway_by_registry(
            micro_gateway.id, micro_gateway_release_history.id, release_history.id
        )

        self.distributor_factory.assert_called_once_with(include_gateway_global_config=False)

        micro_gateway_release_history.refresh_from_db()
        micro_gateway_release_history.status = ReleaseStatusEnum.SUCCESS.value

    def test_success_for_owned_gateway(
        self, mocker, edge_release, micro_gateway, micro_gateway_release_history, release_history
    ):
        edge_release.gateway = micro_gateway.gateway
        edge_release.save()

        self.distributor.distribute.return_value = True, ""

        assert tasks.release_gateway_by_registry(
            micro_gateway.id, micro_gateway_release_history.id, release_history.id
        )

        self.distributor_factory.assert_called_once_with(include_gateway_global_config=False)

        micro_gateway_release_history.refresh_from_db()
        micro_gateway_release_history.status = ReleaseStatusEnum.SUCCESS.value

    def test_fail(self, mocker, edge_release, micro_gateway, micro_gateway_release_history, release_history):
        self.distributor.distribute.return_value = False, "Fail"

        assert not tasks.release_gateway_by_registry(
            micro_gateway.id,
            micro_gateway_release_history.id,
            release_history.id,
        )

        micro_gateway_release_history.refresh_from_db()
        micro_gateway_release_history.status = ReleaseStatusEnum.FAILURE.value
