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

from apigateway.controller.tasks.micro_gateway import deploy_micro_gateway
from apigateway.core.constants import MicroGatewayStatusEnum
from apigateway.core.micro_gateway_config import MicroGatewayBcsInfo


@pytest.fixture()
def release_helper(mocker):
    helper = mocker.MagicMock()
    mocker.patch("apigateway.controller.tasks.micro_gateway.ReleaseHelper", return_value=helper)
    return helper


class TestDeployMicroGateway:
    def test_not_managed(self, micro_gateway, release_helper):
        micro_gateway.is_managed = False
        micro_gateway.save()

        deploy_micro_gateway(micro_gateway.id, "access_token", "")

        micro_gateway.refresh_from_db()
        assert micro_gateway.status == MicroGatewayStatusEnum.UPDATED.value

        release_helper.ensure_release.assert_not_called()

    def test_managed(self, mocker, faker, micro_gateway, release_helper, settings):
        bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(micro_gateway.config)
        assert micro_gateway.is_managed

        revision = faker.pyint()
        release_helper.ensure_release.return_value = mocker.MagicMock(revision=revision)
        username = faker.pystr()

        deploy_micro_gateway(micro_gateway.id, "access_token", username)

        micro_gateway.refresh_from_db()
        assert micro_gateway.status == MicroGatewayStatusEnum.INSTALLED.value
        release_helper.ensure_release.assert_called_once_with(
            project_id=bcs_info.project_name,
            repository=settings.BCS_PUBLIC_CHART_REPOSITORY,
            chart_name=settings.BCS_MICRO_GATEWAY_CHART_NAME,
            chart_version=bcs_info.chart_version,
            release_name=bcs_info.release_name,
            namespace=bcs_info.namespace,
            cluster_id=bcs_info.cluster_id,
            operator=username,
            values=mocker.ANY,
        )

        bcs_info = MicroGatewayBcsInfo.from_micro_gateway_config(micro_gateway.config)
        assert bcs_info.release_revision == revision

    def test_release_fail(self, micro_gateway, release_helper):
        release_helper.ensure_release.side_effect = ValueError("testing")

        deploy_micro_gateway(micro_gateway.id, "access_token", "")

        micro_gateway.refresh_from_db()
        assert micro_gateway.status == MicroGatewayStatusEnum.ABNORMAL.value
