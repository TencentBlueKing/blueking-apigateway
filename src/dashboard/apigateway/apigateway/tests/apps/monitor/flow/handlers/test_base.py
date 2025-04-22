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

from apigateway.apps.monitor.constants import AlarmTypeEnum
from apigateway.apps.monitor.flow.handlers import base as base_handlers
from apigateway.apps.monitor.models import AlarmRecord
from apigateway.core.models import Gateway

pytestmark = [pytest.mark.django_db]


class TestAlarmRecordCreator:
    def test_do(self, mocker, faker, mock_event):
        record_creator = base_handlers.AlarmRecordCreator()
        result = record_creator._do(mock_event)
        assert result.alarm_record_id != 0
        assert AlarmRecord.objects.filter(id=result.alarm_record_id).exists()


class TestAPIExistFilter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.filter = base_handlers.GatewayExistFilter()

    def test_do_with_api_exist(self, faker, mocker):
        gateway = G(Gateway)

        event = mocker.MagicMock(alarm_record_id=1, event_dimensions={"api_id": gateway.id})
        mock_update_alarm = mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.AlarmRecord.objects.update_alarm",
            return_value=None,
        )

        result = self.filter._do(event)
        assert result == event
        mock_update_alarm.assert_called_once_with(1, gateway=gateway)
        event.update_extend_fields.assert_called_once_with({"gateway": gateway})

    def test_do_with_api_not_exist(self, faker, mocker):
        event = mocker.MagicMock(alarm_record_id=1, event_dimensions={"api_id": 0})
        mock_update_alarm = mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.AlarmRecord.objects.update_alarm",
            return_value=None,
        )

        result = self.filter._do(event)
        assert result is None
        mock_update_alarm.assert_called_once_with(1, status="skipped", comment="网关[id=0]不存在")


class TestRelatedLogRecordsFetcher:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.fetcher = base_handlers.RelatedLogRecordsFetcher("", [])

    def test_get_request_log_records(self, faker, mocker, mock_event):
        mocker.patch("apigateway.apps.monitor.flow.handlers.base.LogSearchClient.search", return_value=[{"api_id": 1}])
        result = self.fetcher._get_request_log_records(mock_event)
        assert result == [{"api_id": 1}]

    def test_filter_request_log_records(self, mocker):
        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.RelatedLogRecordsFetcher._is_record_need_alert",
            side_effect=[True, False, True],
        )
        records = [{"_source": {}}, {"_source": {}}, {"_source": {}}]
        result = self.fetcher._filter_request_log_records(AlarmTypeEnum.APP_REQUEST, records)

        assert len(result) == 2

    def test_is_record_need_alert(self, mocker):
        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.AlarmFilterConfig.objects.get_filter_config",
            return_value={},
        )

        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.Matcher.is_match",
            side_effect=[True, False],
        )
        result = self.fetcher._is_record_need_alert(AlarmTypeEnum.APP_REQUEST, {})
        assert result is False

        result = self.fetcher._is_record_need_alert(AlarmTypeEnum.APP_REQUEST, {})
        assert result is True

    def test_do(self, mocker, faker, mock_event):
        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.RelatedLogRecordsFetcher._get_request_log_records",
            return_value=(False, "", []),
        )
        result = self.fetcher._do(mock_event)
        assert result is None

        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.RelatedLogRecordsFetcher._get_request_log_records",
            return_value=(True, "", []),
        )
        result = self.fetcher._do(mock_event)
        assert result is None

        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.RelatedLogRecordsFetcher._get_request_log_records",
            return_value=(True, "", []),
        )
        mocker.patch(
            "apigateway.apps.monitor.flow.handlers.base.RelatedLogRecordsFetcher._filter_request_log_records",
            return_value=[{"api_id": 1}],
        )
        result = self.fetcher._do(mock_event)
        assert result == mock_event


class TestAlerter:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.alerter = base_handlers.Alerter(notice_ways=[])

    def test_do(self, mocker, mock_event):
        mocker.patch("apigateway.apps.monitor.flow.handlers.base.Alerter._alert", return_value=(True, "", ""))
        mocker.patch("apigateway.apps.monitor.flow.handlers.base.Alerter._update_status", return_value=None)

        assert self.alerter._do(mock_event) is None

    def test_alert(self, mocker, mock_event):
        mocker.patch("apigateway.apps.monitor.flow.handlers.base.Alerter.get_message", return_value="message")

        mocker.patch("apigateway.apps.monitor.flow.handlers.base.Alerter.get_receivers", return_value=[])
        status, _, _ = self.alerter._alert(mock_event)
        assert status == "failure"

        mocker.patch("apigateway.apps.monitor.flow.handlers.base.Alerter.get_receivers", return_value=["admin"])
        status, _, _ = self.alerter._alert(mock_event)
        assert status == "success"

    def test_update_status(self, mocker, mock_event):
        record = G(AlarmRecord)
        mock_event.alarm_record_id = record.id
        self.alerter._update_status(mock_event, "success", "", "")
        record = AlarmRecord.objects.get(id=record.id)
        assert record.status == "success"

    def test_render_template(self):
        template = "It is {{color}}"
        result = self.alerter.render_template(template, color="green")
        assert result == "It is green"
