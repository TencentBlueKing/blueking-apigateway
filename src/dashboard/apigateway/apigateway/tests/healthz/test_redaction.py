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
import pytest

from apigateway.healthz.views import CheckError, HealthzView
from apigateway.tests.utils.testing import create_request, get_response_json


class TestHealthzView:
    def test_get_check_error_response_uses_redacted_message(self, mocker):
        mocker.patch.object(HealthzView, "_check_settings")
        mocker.patch.object(HealthzView, "_check_database", side_effect=CheckError("check database failed"))
        mocker.patch.object(HealthzView, "_check_redis")

        response = HealthzView.as_view()(create_request())

        result = get_response_json(response)
        assert response.status_code == 500
        assert result["error"]["message"] == "check database failed"

    def test_check_database_logs_detail_and_raises_redacted_error(self, mocker):
        log_exception = mocker.patch("apigateway.healthz.views.logger.exception")
        mocker.patch("apigateway.core.models.Gateway.objects.exists", side_effect=Exception("database password"))

        with pytest.raises(CheckError, match="check database failed"):
            HealthzView()._check_database()

        log_exception.assert_called_once_with("healthz database check failed")

    def test_check_redis_logs_detail_and_raises_redacted_error(self, mocker):
        client = mocker.MagicMock()
        client.ping.side_effect = Exception("redis://user:password@example.com:6379")
        log_exception = mocker.patch("apigateway.healthz.views.logger.exception")

        mocker.patch("apigateway.healthz.views.get_redis_pool", return_value=object())
        mocker.patch("apigateway.healthz.views.redis.Redis", return_value=client)

        with pytest.raises(CheckError, match="check redis failed"):
            HealthzView()._check_redis()

        log_exception.assert_called_once_with("healthz redis check failed")
