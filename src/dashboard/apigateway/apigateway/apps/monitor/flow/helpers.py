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
import copy
import datetime
from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from apigateway.apps.monitor.constants import ERROR_CODE_NAME_TO_ALARM_SUBTYPE, AlarmTypeEnum
from apigateway.utils import time as time_utils


@dataclass
class MonitorEvent:
    alarm_type: AlarmTypeEnum
    raw: InitVar[Dict[str, Any]]
    alarm_record_id: Optional[int] = None
    _extend: Dict[str, Any] = field(init=False)

    def __post_init__(self, raw: Dict[str, Any]):
        self._raw = raw
        self._extend = {}

    @property
    def should_alert(self):
        """只有发生告警时通知"""
        return self._raw["type"] == "ANOMALY_NOTICE"

    @property
    def extend(self):
        return copy.copy(self._extend)

    @property
    def id(self) -> str:
        return str(self._raw["event"]["id"])

    @property
    def event_dimensions(self) -> Dict[str, Any]:
        # {"code_name": "RATE_LIMIT_RESTRICTION", "resource_id": 100028, "app_code": "abc", "api_id": 190, "stage": "prod"}
        return self._raw["event"]["dimensions"]

    @property
    def event_begin_time(self) -> datetime.datetime:
        return time_utils.utctime(self._raw["event"]["begin_time"]).datetime

    @property
    def event_create_time(self) -> datetime.datetime:
        return time_utils.utctime(self._raw["event"]["create_time"]).datetime

    @property
    def strategy_id(self) -> int:
        return self._raw["strategy"]["id"]

    @property
    def alarm_subtype(self) -> str:
        code_name = self.event_dimensions.get("code_name", "")
        return ERROR_CODE_NAME_TO_ALARM_SUBTYPE.get(code_name, "")

    def update_extend_fields(self, data: Dict[str, Any]):
        self._extend.update(data)


class AlertHandler:
    def handle(self, events: Iterable[MonitorEvent]) -> List[MonitorEvent]:
        new_events = []
        for event in events:
            new_event = self._do(event)
            if new_event:
                new_events.append(new_event)

        return new_events

    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        raise NotImplementedError


@dataclass
class AlertFlow:
    _handlers: List[AlertHandler] = field(default_factory=list)

    def run(self, events: Optional[List[MonitorEvent]] = None):
        for handler in self._handlers:
            if not events:
                break

            events = handler.handle(events)

    def append(self, handler: AlertHandler):
        self._handlers.append(handler)
