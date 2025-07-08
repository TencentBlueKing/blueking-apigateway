# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.core.models import Gateway, Resource
from apigateway.service.alert_flow.handlers import resource_backend

pytestmark = pytest.mark.django_db


class TestResourceBackendAlarmStrategyEnabledFilter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.filter = resource_backend.ResourceBackendAlarmStrategyEnabledFilter()

    def test_do(self, mocker, faker, mock_event):
        mocker.patch(
            "apigateway.service.alert_flow.handlers.resource_backend.ResourceBackendAlarmStrategyEnabledFilter._get_resource_alarm_strategy",
            return_value=[],
        )
        mocker.patch(
            "apigateway.service.alert_flow.handlers.resource_backend.AlarmRecord.objects.update_alarm",
            return_value=None,
        )

        mocker.patch(
            (
                "apigateway.service.alert_flow.handlers.resource_backend."
                "ResourceBackendAlarmStrategyEnabledFilter._is_alarm_enabled"
            ),
            return_value=False,
        )
        result = self.filter._do(mock_event)
        assert result is None

        mocker.patch(
            (
                "apigateway.service.alert_flow.handlers.resource_backend."
                "ResourceBackendAlarmStrategyEnabledFilter._is_alarm_enabled"
            ),
            return_value=True,
        )
        mocker.patch(
            (
                "apigateway.service.alert_flow.handlers.resource_backend.ResourceBackendAlarmStrategyEnabledFilter."
                "_get_enabled_strategies"
            ),
            return_value=[],
        )
        result = self.filter._do(mock_event)
        assert result == mock_event

    def test__is_alarm_enabled(self, mocker):
        result = self.filter._is_alarm_enabled([], "prod")
        assert result is False

        strategy = G(AlarmStrategy, enabled=True)
        result = self.filter._is_alarm_enabled([strategy], "prod")
        assert result is True

        strategy.enabled = False
        result = self.filter._is_alarm_enabled([strategy], "prod")
        assert result is False

    def test_get_enabled_strategies(self):
        # Test with no strategies
        result = self.filter._get_enabled_strategies([], "prod")
        assert result == []

        # Test with enabled strategy and matching stage
        strategy = G(AlarmStrategy, enabled=True, _effective_stages="prod")
        result = self.filter._get_enabled_strategies([strategy], "prod")
        assert result == [strategy]

        # Test with enabled strategy but non-matching stage
        strategy = G(AlarmStrategy, enabled=True, _effective_stages="test")
        result = self.filter._get_enabled_strategies([strategy], "prod")
        assert result == []

        # Test with disabled strategy
        strategy = G(AlarmStrategy, enabled=False, _effective_stages="prod")
        result = self.filter._get_enabled_strategies([strategy], "prod")
        assert result == []

    def test_get_resource_alarm_strategy(self):
        gateway_1 = G(Gateway)
        gateway_2 = G(Gateway)
        resource_1 = G(Resource, gateway=gateway_2)
        resource_2 = G(Resource, gateway=gateway_2)

        api_label = G(APILabel, gateway=gateway_2)
        G(ResourceLabel, resource=resource_1, api_label=api_label)

        alarm_strategy = G(
            AlarmStrategy,
            gateway=gateway_2,
            enabled=True,
            alarm_subtype="status_code_5xx",
        )
        alarm_strategy.api_labels.set([api_label.id])

        alarm_strategy_2 = G(
            AlarmStrategy,
            gateway=gateway_2,
            enabled=True,
            alarm_subtype="status_code_5xx",
        )

        data = [
            # gateway alarm-strategy not exist
            {
                "gateway_id": gateway_1.id,
                "resource_id": 1,
                "expected": [],
            },
            {
                "gateway_id": gateway_2.id,
                "resource_id": resource_1.id,
                "expected": [alarm_strategy, alarm_strategy_2],
            },
            {
                "gateway_id": gateway_2.id,
                "resource_id": resource_2.id,
                "expected": [alarm_strategy_2],
            },
        ]
        for test in data:
            result = self.filter._get_resource_alarm_strategy(
                test["gateway_id"],
                test["resource_id"],
                "status_code_5xx",
            )
            assert result == test["expected"]


class TestResourceBackendAlerter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.alerter = resource_backend.ResourceBackendAlerter(notice_ways=[])

    def test_get_receivers(self, mocker, mock_event):
        gateway = G(Gateway, _maintainers="admin1")

        mock_event.extend = {
            "alarm_strategies": [],
            "gateway": gateway,
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

    @pytest.mark.parametrize(
        "record_source, expected",
        [
            (
                {
                    "backend_scheme": "http",
                    "backend_host": "bkapi.example.com",
                    "backend_path": "/",
                },
                "http://bkapi.example.com/",
            ),
            (
                {
                    "backend_scheme": "https",
                    "backend_host": "bkapi.example.com",
                    "backend_path": "/foo",
                },
                "https://bkapi.example.com/foo",
            ),
            (
                {
                    "backend_scheme": "https",
                    "backend_host": "bkapi.example.com",
                    "backend_path": "/foo?color=red&size=large",
                },
                "https://bkapi.example.com/foo",
            ),
        ],
    )
    def test_get_backend_url(self, record_source, expected):
        result = self.alerter._get_backend_url(record_source)
        assert result == expected
