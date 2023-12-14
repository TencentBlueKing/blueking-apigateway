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

from apigateway.apps.monitor.flow.handlers import app_request


class TestAppRequestAppCodeRequiredFilter:
    @pytest.mark.parametrize(
        "event, expected_none",
        [
            (
                {
                    "alarm_record_id": 1,
                    "event_dimensions": {
                        "api_id": 2,
                        "resource_id": 3,
                        "stage": "prod",
                        "app_code": "test",
                    },
                },
                False,
            ),
            (
                {
                    "alarm_record_id": 1,
                    "event_dimensions": {
                        "api_id": 2,
                        "resource_id": 3,
                        "stage": "prod",
                        "app_code": "",
                    },
                },
                True,
            ),
        ],
    )
    def test_do(self, mocker, event, expected_none):
        event = mocker.MagicMock(**event)
        mock_update_alarm = mocker.patch(
            "apigateway.apps.monitor.flow.handlers.app_request.AlarmRecord.objects.update_alarm",
            return_value=None,
        )

        filter = app_request.AppRequestAppCodeRequiredFilter()
        result = filter._do(event)

        if expected_none:
            assert result is None
            mock_update_alarm.assert_called_once_with(1, status="skipped", comment="app_code 为空")
        else:
            assert result == event
            mock_update_alarm.assert_not_called()


class TestAppRequestAlerter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.alerter = app_request.AppRequestAlerter(notice_ways=[])

    def test_get_receivers(self, mocker, faker, mock_event):
        mocker.patch("apigateway.apps.monitor.flow.handlers.app_request.get_app_maintainers", return_value=["admin"])

        result = self.alerter.get_receivers(mock_event)
        assert result == ["admin"]

    def test_get_message(self, mocker, faker):
        event = mocker.MagicMock(
            extend={
                "log_records": [
                    {
                        "_source": {
                            "app_code": faker.pystr(),
                            "api_name": faker.pystr(),
                            "stage": faker.pystr(),
                            "client_ip": faker.ipv4(),
                            "error": faker.pystr(),
                            "request_id": faker.pystr(),
                            "time": faker.pystr(),
                            "method": faker.http_method(),
                            "http_host": faker.hostname(),
                            "http_path": faker.pystr(),
                        }
                    }
                ]
            },
            event_begin_time=faker.date_time(),
            event_create_time=faker.date_time(),
        )
        result = self.alerter.get_message(event)
        assert result != ""

    @pytest.mark.parametrize(
        "record_source, expected",
        [
            (
                {
                    "method": "GET",
                    "http_host": "bkapi.example.com",
                    "http_path": "/",
                },
                "GET, bkapi.example.com, /",
            ),
            (
                {
                    "method": "GET",
                    "http_host": "bkapi.example.com",
                    "http_path": "/foo",
                },
                "GET, bkapi.example.com, /foo",
            ),
            (
                {
                    "method": "GET",
                    "http_host": "bkapi.example.com",
                    "http_path": "/foo?color=red&size=large",
                },
                "GET, bkapi.example.com, /foo",
            ),
        ],
    )
    def test_get_request_info(self, record_source, expected):
        result = self.alerter._get_request_info(record_source)
        assert result == expected
