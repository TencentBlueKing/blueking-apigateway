#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
import datetime

import pytest
from ddf import G

from apigateway.apps.programmable_gateway.models import ProgrammableGatewayDeployHistory
from apigateway.biz.programmable import ProgrammableGatewayReleaser
from apigateway.biz.programmable.releaser import _paas_status_cache
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.core.constants import PublishSourceEnum, ReleaseHistoryStatusEnum
from apigateway.core.models import Gateway, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import dummy_time

pytestmark = pytest.mark.django_db


class TestProgrammableGatewayReleaser:
    def test_filter_deploy_history(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, gateway=gateway, name="prod")
        stage_test = G(Stage, gateway=gateway, name="test")

        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage_prod, version="1.0.0")
        G(
            ProgrammableGatewayDeployHistory,
            gateway=gateway,
            stage=stage_prod,
            version="1.0.1",
            created_by="admin",
        )
        G(
            ProgrammableGatewayDeployHistory,
            gateway=gateway,
            stage=stage_prod,
            version="1.0.2",
            created_time=dummy_time.time,
        )
        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage_test, version="2.0.0")

        data = [
            {
                "params": {
                    "query": "prod",
                },
                "expected": {
                    "count": 3,
                },
            },
            {
                "params": {
                    "stage_id": stage_prod.id,
                },
                "expected": {
                    "count": 3,
                },
            },
            {
                "params": {
                    "created_by": "adm",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "created_by": "adm",
                },
                "fuzzy": False,
                "expected": {
                    "count": 0,
                },
            },
            {
                "params": {
                    "created_by": "admin",
                },
                "fuzzy": False,
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "query": "prod",
                },
                "fuzzy": False,
                "expected": {
                    "count": 4,
                },
            },
            {
                "params": {
                    "time_start": dummy_time.time - datetime.timedelta(hours=1),
                    "time_end": dummy_time.time + datetime.timedelta(hours=1),
                },
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            result = ProgrammableGatewayReleaser.filter_deploy_history(
                gateway, fuzzy=test.get("fuzzy", True), **test["params"]
            )
            assert result.count() == test["expected"]["count"]

    def test_get_stage_deploy_status_without_deploy_history_when_stage_released(self):
        """从开发者中心发布后，网关侧可能只有 Release 而没有 DeployHistory。"""
        gateway = G(Gateway)
        stage = G(Stage, gateway=gateway, status=1)
        resource_version = G(ResourceVersion, gateway=gateway, version="1.0.0")
        G(Release, gateway=gateway, stage=stage, resource_version=resource_version)
        user_credentials = UserCredentials(credentials="token", tenant_id="default")

        result = ProgrammableGatewayReleaser.get_stage_deploy_status(gateway, stage.id, user_credentials)

        assert result["latest_publish_status"] == ""
        assert result["last_publish_status"] == ""
        assert result["latest_history_id"] == 0
        assert result["last_deploy_history"] is not None
        assert result["last_deploy_history"].pk is None
        assert result["latest_deploy_history"] is not None
        assert result["latest_deploy_history"].pk is None

    def test_get_stage_deploy_status_skips_paas_when_deploy_is_stable(self, mocker):
        mock_paas_result = mocker.patch("apigateway.biz.programmable.releaser.get_paas_deployment_result")
        mocker.patch("apigateway.biz.programmable.releaser.ReleaseHandler.get_release_status", return_value="success")
        gateway = G(Gateway)
        stage = G(Stage, gateway=gateway, status=1)
        resource_version = G(ResourceVersion, gateway=gateway, version="1.0.0")
        G(Release, gateway=gateway, stage=stage, resource_version=resource_version)
        G(ReleaseHistory, gateway=gateway, stage=stage, resource_version=resource_version)
        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage, version="1.0.0")
        user_credentials = UserCredentials(credentials="token", tenant_id="default")

        result = ProgrammableGatewayReleaser.get_stage_deploy_status(gateway, stage.id, user_credentials)

        mock_paas_result.assert_not_called()
        assert result["latest_publish_status"] == ""
        assert result["last_publish_status"] == ReleaseHistoryStatusEnum.SUCCESS.value

    def test_get_stage_deploy_status_reads_paas_when_upgrade_failed(self, mocker):
        mocker.patch(
            "apigateway.biz.programmable.releaser.get_paas_deployment_result",
            return_value={"status": "failed"},
        )
        mocker.patch("apigateway.biz.programmable.releaser.ReleaseHandler.get_release_status", return_value="success")
        gateway = G(Gateway)
        stage = G(Stage, gateway=gateway, status=1)
        resource_version = G(ResourceVersion, gateway=gateway, version="1.0.0")
        G(Release, gateway=gateway, stage=stage, resource_version=resource_version)
        G(ReleaseHistory, gateway=gateway, stage=stage, resource_version=resource_version)
        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage, version="2.0.0", publish_id=None)
        user_credentials = UserCredentials(credentials="token", tenant_id="default")

        result = ProgrammableGatewayReleaser.get_stage_deploy_status(gateway, stage.id, user_credentials)

        assert result["latest_publish_status"] == ReleaseHistoryStatusEnum.FAILURE.value
        assert result["last_publish_status"] == ReleaseHistoryStatusEnum.SUCCESS.value

    def test_get_stage_deploy_status_reads_paas_when_first_publish_failed(self, mocker):
        mocker.patch(
            "apigateway.biz.programmable.releaser.get_paas_deployment_result",
            return_value={"status": "failed"},
        )
        gateway = G(Gateway)
        stage = G(Stage, gateway=gateway, status=1)
        G(ProgrammableGatewayDeployHistory, gateway=gateway, stage=stage, version="1.0.0")
        user_credentials = UserCredentials(credentials="token", tenant_id="default")

        result = ProgrammableGatewayReleaser.get_stage_deploy_status(gateway, stage.id, user_credentials)

        assert result["last_publish_status"] == ReleaseHistoryStatusEnum.FAILURE.value


class TestGetPaasDeployStatusCache:
    @pytest.fixture(autouse=True)
    def clear_paas_status_cache(self):
        _paas_status_cache.clear()
        yield
        _paas_status_cache.clear()

    @staticmethod
    def _get_status(
        tenant_id="default", app_code="demo", source=PublishSourceEnum.VERSION_PUBLISH.value, deploy_id="deploy-1"
    ):
        return ProgrammableGatewayReleaser._get_paas_deploy_status(
            Gateway(name=app_code),
            ProgrammableGatewayDeployHistory(source=source, deploy_id=deploy_id),
            UserCredentials(credentials="token", tenant_id=tenant_id),
        )

    @pytest.mark.parametrize("paas_status", ["successful", "failed", "interrupted"])
    def test_finished_status_is_cached(self, mocker, paas_status):
        mock_result = mocker.patch.object(
            ProgrammableGatewayReleaser, "_get_paas_deploy_result", return_value={"status": paas_status}
        )

        assert self._get_status() == paas_status
        assert self._get_status() == paas_status
        mock_result.assert_called_once()

    @pytest.mark.parametrize("paas_result", [{"status": "pending"}, {}])
    def test_unfinished_status_is_not_cached(self, mocker, paas_result):
        mock_result = mocker.patch.object(
            ProgrammableGatewayReleaser, "_get_paas_deploy_result", return_value=paas_result
        )

        self._get_status()
        self._get_status()

        assert mock_result.call_count == 2

    @pytest.mark.parametrize(
        "other_scope",
        [
            {"tenant_id": "other"},
            {"app_code": "other"},
            {"source": PublishSourceEnum.STAGE_DISABLE.value},
            {"deploy_id": "deploy-2"},
        ],
    )
    def test_cache_is_scoped(self, mocker, other_scope):
        mock_result = mocker.patch.object(
            ProgrammableGatewayReleaser, "_get_paas_deploy_result", return_value={"status": "failed"}
        )

        self._get_status()
        self._get_status(**other_scope)

        assert mock_result.call_count == 2
