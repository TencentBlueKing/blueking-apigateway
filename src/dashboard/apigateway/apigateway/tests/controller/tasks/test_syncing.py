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

from apigateway.apps.release.validators import ReleaseValidationError
from apigateway.controller.tasks.syncing import release_updated_check, revoke_release_by_stage, rolling_update_release
from apigateway.core.constants import APIHostingTypeEnum
from apigateway.core.models import MicroGateway
from apigateway.utils.redis_utils import get_redis_key

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture()
def revision_update_key(settings):
    return get_redis_key(settings.APIGW_REVERSION_UPDATE_SET_KEY)


class TestRollingUpdateRelease:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.distributor = mocker.MagicMock()
        mocker.patch("apigateway.controller.tasks.syncing.CombineDistributor", return_value=self.distributor)

    def test_for_default_hosting_type(self, edge_gateway, edge_release):
        edge_gateway.hosting_type = APIHostingTypeEnum.DEFAULT.value
        edge_gateway.save()

        assert not rolling_update_release(edge_gateway.pk)

        self.distributor.distribute.assert_not_called()

    def test_for_edge_gateway(self, edge_gateway, edge_release, micro_gateway):
        edge_micro_gateway = G(MicroGateway, is_shared=False)
        edge_release.stage.micro_gateway = edge_micro_gateway
        edge_release.stage.save()

        assert rolling_update_release(edge_gateway.pk)

        self.distributor.distribute.assert_called()

    def test_for_shared_gateway(self, edge_gateway, edge_release, micro_gateway):
        edge_release.stage.micro_gateway = None
        edge_release.stage.save()

        assert rolling_update_release(edge_gateway.pk)

        self.distributor.distribute.assert_called()

    def test_for_managed_shared_gateway(self, edge_gateway, edge_release, micro_gateway):
        assert micro_gateway.is_shared

        edge_release.stage.micro_gateway = micro_gateway
        edge_release.stage.save()

        assert rolling_update_release(edge_gateway.pk)

        self.distributor.distribute.assert_called()

    def test_validate_failed(self, mocker, edge_gateway, edge_release, micro_gateway):
        mocker.patch(
            "apigateway.controller.tasks.syncing.ReleaseValidator.validate", side_effect=ReleaseValidationError()
        )
        edge_release.stage.micro_gateway = None
        edge_release.stage.save()

        assert not rolling_update_release(edge_gateway.pk)

        self.distributor.distribute.assert_not_called()


class TestReleaseUpdatedChecker:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.rolling_update_release = mocker.patch("apigateway.controller.tasks.syncing.rolling_update_release")

    def test_when_key_not_exists(self, default_redis):
        assert not release_updated_check()

    def test_for_default_hosting_type(self, fake_gateway, default_redis, revision_update_key):
        fake_gateway.hosting_type = APIHostingTypeEnum.DEFAULT.value
        fake_gateway.save()

        default_redis.sadd(revision_update_key, fake_gateway.pk)

        assert not release_updated_check()

    def test_api_not_exists(self, default_redis, revision_update_key):
        default_redis.sadd(revision_update_key, 0)

        assert not release_updated_check()

    def test_dispatch_task(self, edge_gateway, default_redis, revision_update_key):
        default_redis.sadd(revision_update_key, edge_gateway.pk)

        assert release_updated_check()
        self.rolling_update_release.apply_async.assert_any_call(args=(edge_gateway.pk,), ignore_result=True, kwargs={})


class TestRevokeRelease:
    def test_revoke(self, mocker, fake_stage, micro_gateway):
        self.distributor = mocker.MagicMock()
        mocker.patch("apigateway.controller.tasks.syncing.CombineDistributor", return_value=self.distributor)
        mocker.patch(
            "apigateway.controller.tasks.syncing.ReleaseProcedureLogger",
            return_value=mocker.MagicMock(release_task_id="12345abcdef"),
        )

        revoke_release_by_stage(fake_stage.pk)
        self.distributor.revoke.assert_called_once_with(fake_stage, micro_gateway, "12345abcdef")
