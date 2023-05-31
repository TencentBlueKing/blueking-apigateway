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
import datetime

from apigateway.apps.monitor.constants import AlarmTypeEnum
from apigateway.apps.monitor.flow.helpers import MonitorEvent


class TestMonitorEvent:
    def test_init(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"api_id": 1})
        assert event.alarm_type == AlarmTypeEnum.APP_REQUEST
        assert event._raw == {"api_id": 1}
        assert event._extend == {}

    def test_should_alert(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"type": "ANOMALY_NOTICE"})
        assert event.should_alert is True

        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"type": "test"})
        assert event.should_alert is False

    def test_extend(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={})
        event._extend = {"api_id": 1}
        assert event.extend == {"api_id": 1}

    def test_id(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"event": {"id": 123}})
        assert event.id == "123"

    def test_event_dimensions(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"event": {"dimensions": {"api_id": 1}}})
        assert event.event_dimensions == {"api_id": 1}

    def test_event_begin_time(self):
        event = MonitorEvent(
            alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"event": {"begin_time": "1999-10-10 12:00:00"}}
        )
        assert isinstance(event.event_begin_time, datetime.datetime)

    def test_strategy_id(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={"strategy": {"id": 123}})
        assert event.strategy_id == 123

    def test_alarm_subtype(self):
        event = MonitorEvent(
            alarm_type=AlarmTypeEnum.APP_REQUEST,
            raw={"event": {"dimensions": {"code_name": "ERROR_REQUESTING_RESOURCE"}}},
        )
        assert event.alarm_subtype == "bad_gateway"

    def test_update_extend_fields(self):
        event = MonitorEvent(alarm_type=AlarmTypeEnum.APP_REQUEST, raw={})
        event.update_extend_fields({"color": "green"})
        assert event.extend == {"color": "green"}
