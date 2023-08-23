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

from apigateway.controller.constants import NO_NEED_REPORT_EVENT_PUBLISH_ID
from apigateway.controller.tasks.syncing import revoke_release, rolling_update_release
from apigateway.core.models import MicroGateway

pytestmark = pytest.mark.django_db(transaction=True)


class TestRollingUpdateRelease:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.distributor = mocker.MagicMock()
        mocker.patch("apigateway.controller.tasks.syncing.CombineDistributor", return_value=self.distributor)

    def test_for_edge_gateway(self, edge_gateway, edge_release, micro_gateway):
        edge_micro_gateway = G(MicroGateway, is_shared=False)
        edge_release.stage.micro_gateway = edge_micro_gateway
        edge_release.stage.save()

        self.distributor.distribute.return_value = True, ""

        assert rolling_update_release(edge_gateway.pk, NO_NEED_REPORT_EVENT_PUBLISH_ID, edge_release.pk)

        self.distributor.distribute.assert_called()

    def test_for_shared_gateway(self, edge_gateway, edge_release, micro_gateway):
        edge_release.stage.micro_gateway = None
        edge_release.stage.save()

        self.distributor.distribute.return_value = True, ""

        assert rolling_update_release(edge_gateway.pk, NO_NEED_REPORT_EVENT_PUBLISH_ID, edge_release.pk)

        self.distributor.distribute.assert_called()

    def test_for_managed_shared_gateway(self, edge_gateway, edge_release, micro_gateway):
        assert micro_gateway.is_shared

        self.distributor.distribute.return_value = True, ""

        edge_release.stage.micro_gateway = micro_gateway
        edge_release.stage.save()

        assert rolling_update_release(edge_gateway.pk, NO_NEED_REPORT_EVENT_PUBLISH_ID, edge_release.pk)

        self.distributor.distribute.assert_called()


class TestRevokeRelease:
    def test_revoke(self, mocker, fake_release, fake_release_history, micro_gateway):
        self.distributor = mocker.MagicMock()
        self.distributor.revoke.return_value = True, ""
        mocker.patch("apigateway.controller.tasks.syncing.CombineDistributor", return_value=self.distributor)
        mocker.patch(
            "apigateway.controller.tasks.syncing.ReleaseProcedureLogger",
            return_value=mocker.MagicMock(release_task_id="12345abcdef"),
        )

        revoke_release(fake_release.pk, fake_release_history.pk)
        self.distributor.revoke.assert_called_once_with(
            fake_release, micro_gateway, "12345abcdef", publish_id=fake_release_history.pk
        )
