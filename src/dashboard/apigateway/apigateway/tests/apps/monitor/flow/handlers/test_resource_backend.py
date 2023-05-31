# -*- coding: utf-8 -*-
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

from apigateway.apps.monitor.flow.handlers import resource_backend
from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestesourceBackendAlarmStrategyEnabledFilter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.filter = resource_backend.ResourceBackendAlarmStrategyEnabledFilter()

    def test_do(self, mocker, faker, mock_event):
        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.resource_backend.AlarmStrategy.objects.get_resource_alarm_strategy",
            return_value=[],
        )
        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.resource_backend.AlarmRecord.objects.update_alarm",
            return_value=None,
        )

        mocker.patch(
            (
                "apigateway.apps.monitor.flow.handlers.resource_backend."
                "ResourceBackendAlarmStrategyEnabledFilter._is_alarm_enabled"
            ),
            return_value=False,
        )
        result = self.filter._do(mock_event)
        assert result is None

        mocker.patch(
            (
                "apigateway.apps.monitor.flow.handlers.resource_backend."
                "ResourceBackendAlarmStrategyEnabledFilter._is_alarm_enabled"
            ),
            return_value=True,
        )
        mocker.patch(
            (
                "apigateway.apps.monitor.flow.handlers.resource_backend.ResourceBackendAlarmStrategyEnabledFilter."
                "_get_enabled_strategies"
            ),
            return_value=[],
        )
        result = self.filter._do(mock_event)
        assert result == mock_event

    def _is_alarm_enabled(self, mocker):
        result = self.filter._is_alarm_enabled([])
        assert result is True

        strategy = G(AlarmStrategy, enabled=True)
        result = self.filter._is_alarm_enabled([strategy])
        assert result is True

        strategy.enabled = False
        result = self.filter._is_alarm_enabled([strategy])
        assert result is False


class TestResourceBackendAlerter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.alerter = resource_backend.ResourceBackendAlerter(notice_ways=[])

    def test_get_receivers(self, mocker, mock_event):
        api = G(Gateway, _maintainers="admin1")

        mock_event.extend = {
            "alarm_strategies": [],
            "api": api,
        }
        result = self.alerter.get_receivers(mock_event)
        assert result == ["admin1"]

        mocker.patch.object(
            AlarmStrategy,
            "notice_receivers",
            new_callable=mocker.PropertyMock(return_value=["admin2"]),
        )
        strategy = G(AlarmStrategy)
        mock_event.extend = {
            "alarm_strategies": [strategy],
        }
        result = self.alerter.get_receivers(mock_event)
        assert result == ["admin2"]

    def test_get_message(self, faker, mock_event):
        mock_event.extend = {
            "log_records": [
                {
                    "_source": {
                        "api_name": faker.pystr(),
                        "stage": faker.pystr(),
                        "backend_method": faker.http_method(),
                        "status": faker.pystr(),
                        "response_body": faker.pystr(),
                        "request_id": faker.pystr(),
                        "time": faker.pystr(),
                        "backend_scheme": faker.pystr(),
                        "backend_host": faker.pystr(),
                        "backend_path": faker.pystr(),
                    }
                }
            ]
        }
        result = self.alerter.get_message(mock_event)
        assert result != ""
