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
from apigateway.controller.tasks.release import clear_unreleased_resource
from apigateway.core.models import (
    Gateway,
    Release,
    ReleasedResource,
    ReleaseHistory,
    ResourceVersion,
)


@pytest.fixture()
def release_history():
    return G(ReleaseHistory)


class TestReleaseGatewayByRegistry:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.distributor = mocker.MagicMock()
        self.distributor_factory = mocker.patch(
            "apigateway.controller.tasks.release.EtcdDistributor", return_value=self.distributor
        )

    def test_success_for_shared_gateway(self, mocker, edge_release, micro_gateway, release_history):
        edge_release.gateway = G(Gateway)
        edge_release.save()

        self.distributor.distribute.return_value = True, ""

        assert tasks.release_gateway_by_registry(micro_gateway.id, release_history.id)

        self.distributor_factory.assert_called_once_with(include_gateway_global_config=False)

    def test_success_for_owned_gateway(self, mocker, edge_release, micro_gateway, release_history):
        edge_release.gateway = micro_gateway.gateway
        edge_release.save()

        self.distributor.distribute.return_value = True, ""

        assert tasks.release_gateway_by_registry(micro_gateway.id, release_history.id)

        self.distributor_factory.assert_called_once_with(include_gateway_global_config=False)

    def test_fail(self, mocker, edge_release, micro_gateway, release_history):
        self.distributor.distribute.return_value = False, "Fail"

        assert not tasks.release_gateway_by_registry(
            micro_gateway.id,
            release_history.id,
        )

    def test_clear_unreleased_resource(self, fake_gateway, fake_stage):
        rv1 = G(ResourceVersion, gateway=fake_gateway)
        rv2 = G(ResourceVersion, gateway=fake_gateway)

        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv1)

        G(ReleasedResource, gateway=fake_gateway, resource_version_id=rv1.id, data={})
        G(ReleasedResource, gateway=fake_gateway, resource_version_id=rv2.id, data={})

        clear_unreleased_resource(fake_gateway.id)

        assert ReleasedResource.objects.filter(resource_version_id=rv1.id).exists()
        assert not ReleasedResource.objects.filter(resource_version_id=rv2.id).exists()
