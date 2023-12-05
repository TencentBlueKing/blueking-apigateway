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

from apigateway.apps.micro_gateway.handlers import NeedDeployMicroGatewayHandler, RelateDeployedMicroGatewayHandler
from apigateway.core.constants import MicroGatewayStatusEnum
from apigateway.utils.user_credentials import UserCredentials

pytestmark = pytest.mark.django_db(transaction=True)


class TestNeedDeployMicroGateway:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.handler = NeedDeployMicroGatewayHandler()

    def test_deploy(self, mocker, faker):
        mock_deploy_micro_gateway = mocker.patch(
            "apigateway.apps.micro_gateway.handlers.deploy_micro_gateway.apply_async"
        )

        micro_gateway_id = faker.pyint()
        self.handler.deploy(micro_gateway_id, user_credentials=UserCredentials(credentials="access_token"))

        mock_deploy_micro_gateway.assert_called_once_with(
            args=(micro_gateway_id, {"bk_token": "access_token"}, ""), ignore_result=True, kwargs={}
        )

    def test_get_initial_status(self):
        assert self.handler.get_initial_status() == MicroGatewayStatusEnum.PENDING

    def test_get_bcs_info(self, settings):
        settings.BCS_MICRO_GATEWAY_CHART_NAME = "foo"
        settings.BCS_MICRO_GATEWAY_CHART_VERSION = "0.0.2"

        result = self.handler.get_initial_bcs_info()
        assert result == {
            "chart_name": "foo",
            "chart_version": "0.0.2",
        }


class TestRelateDeployedMicroGatewayHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.handler = RelateDeployedMicroGatewayHandler()

    def test_deploy(self, faker):
        assert self.handler.deploy(faker.pyint(), user_credentials=UserCredentials(credentials="access_token")) is None

    def test_get_initial_status(self):
        assert self.handler.get_initial_status() == MicroGatewayStatusEnum.INSTALLED

    def test_get_initial_bcs_info(self):
        assert self.handler.get_initial_bcs_info() == {}
