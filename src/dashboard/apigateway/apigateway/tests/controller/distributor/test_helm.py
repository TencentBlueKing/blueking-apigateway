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

from apigateway.controller.distributor.helm import HelmDistributor
from apigateway.controller.helm.release import ReleaseInfo
from apigateway.controller.micro_gateway_config import MicroGatewayBcsInfo


class TestHelmDistributor:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        mocker,
    ):
        self.chart_helper = mocker.MagicMock()

        self.release_helper = mocker.MagicMock()
        self.release_helper.ensure_release.return_value = True, ReleaseInfo.from_api({})

    def test_distribute_with_generate_chart(self, mocker, faker, edge_release, micro_gateway):
        distributor = HelmDistributor(
            generate_chart=True,
            operator=faker.user_name(),
            chart_helper=self.chart_helper,
            release_helper=self.release_helper,
        )

        bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(micro_gateway.config)
        is_success, err_msg = distributor.distribute(release=edge_release, micro_gateway=micro_gateway)

        assert is_success
        assert err_msg == ""
        self.chart_helper.get_project_repo_info.assert_called_once_with(bcs_info.project_name)

        repo_info = self.chart_helper.get_project_repo_info()
        self.chart_helper.push_chart.assert_called_once_with(mocker.ANY, repo_info)

        self.release_helper.ensure_release.assert_called_once_with(
            chart_name=mocker.ANY,
            chart_version=mocker.ANY,
            release_name=mocker.ANY,
            values=mocker.ANY,
            namespace=bcs_info.namespace,
            cluster_id=bcs_info.cluster_id,
            project_id=bcs_info.project_name,
            repository=bcs_info.project_name,
            operator=distributor.operator,
        )

    def test_distribute_without_generate_chart(self, mocker, faker, edge_release, micro_gateway):
        distributor = HelmDistributor(
            generate_chart=False,
            operator=faker.user_name(),
            chart_helper=self.chart_helper,
            release_helper=self.release_helper,
        )

        bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(micro_gateway.config)
        is_success, err_msg = distributor.distribute(release=edge_release, micro_gateway=micro_gateway)
        assert is_success
        assert err_msg == ""
        self.chart_helper.push_chart.assert_not_called()

        self.release_helper.ensure_release.assert_called_once_with(
            chart_name=mocker.ANY,
            chart_version=mocker.ANY,
            release_name=mocker.ANY,
            values=mocker.ANY,
            namespace=bcs_info.namespace,
            cluster_id=bcs_info.cluster_id,
            project_id=bcs_info.project_name,
            repository=bcs_info.project_name,
            operator=distributor.operator,
        )
