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
import json
import logging
import textwrap
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.template import Context, Template

from apigateway.apps.monitor.clients.bk_log import LogSearchClient
from apigateway.apps.monitor.constants import DEFAULT_SENDER, AlarmStatusEnum, AlarmTypeEnum
from apigateway.apps.monitor.flow.helpers import AlertHandler, MonitorEvent
from apigateway.apps.monitor.flow.matcher import Matcher
from apigateway.apps.monitor.flow.notice import NoticeWay
from apigateway.apps.monitor.models import AlarmFilterConfig, AlarmRecord
from apigateway.core.models import Gateway
from apigateway.utils import time as time_utils

logger = logging.getLogger(__name__)


class AlarmRecordCreator(AlertHandler):
    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        """创建监控告警记录"""
        if not event.should_alert:
            logger.warning(
                "monitor event should not be alerted, event_id=%s, strategy_id=%s",
                event.id,
                event.strategy_id,
            )
            return None

        record = AlarmRecord.objects.create(
            alarm_id=event.id,
            alarm_attr_id=event.strategy_id,
            source_time=event.event_begin_time,
            match_dimension=json.dumps(event.event_dimensions),
            status=AlarmStatusEnum.RECEIVED.value,
            comment="创建告警记录",
        )
        event.alarm_record_id = record.id

        return event


class APIExistFilter(AlertHandler):
    """网关必须存在"""

    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        gateway_id = int(event.event_dimensions["api_id"])

        gateway = Gateway.objects.filter(id=gateway_id).first()
        if not gateway:
            AlarmRecord.objects.update_alarm(
                event.alarm_record_id,
                status=AlarmStatusEnum.SKIPPED.value,
                comment=f"网关[id={gateway_id}]不存在",
            )
            return None

        AlarmRecord.objects.update_alarm(event.alarm_record_id, gateway=gateway)
        event.update_extend_fields({"gateway": gateway})
        return event


class RelatedLogRecordsFetcher(AlertHandler):
    def __init__(self, es_index: str, output_fields: List[str]):
        self.es_index = es_index
        self.output_fields = output_fields

    def _get_request_log_records(self, event: MonitorEvent):
        client = LogSearchClient(self.es_index, self.output_fields)
        # source_time 按分钟聚合，不包含秒信息
        return client.search(time_utils.timestamp(event.event_begin_time), event.event_dimensions)

    def _filter_request_log_records(self, alarm_type: AlarmTypeEnum, records: Iterable[Dict[str, Any]]) -> list:
        return [record for record in records if self._is_record_need_alert(alarm_type, record["_source"])]

    def _is_record_need_alert(self, alarm_type: AlarmTypeEnum, record_source: dict):
        filter_conditions = AlarmFilterConfig.objects.get_filter_config(alarm_type.value)
        if Matcher().is_match(record_source, filter_conditions):
            return False
        return True

    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        ok, message, records = self._get_request_log_records(event)
        if not ok:
            logger.error(
                "get monitor events failed. source_time: %s, match_dimension: %s",
                event.event_begin_time,
                event.event_dimensions,
            )
            AlarmRecord.objects.update_alarm(
                event.alarm_record_id,
                status=AlarmStatusEnum.SKIPPED.value,
                comment=f"获取告警事件源记录失败，{message}",
            )
            return None

        filtered_records = self._filter_request_log_records(event.alarm_type, records)
        if not filtered_records:
            AlarmRecord.objects.update_alarm(
                event.alarm_record_id,
                status=AlarmStatusEnum.SKIPPED.value,
                comment="所有告警源记录被过滤，此告警不需要发送告警通知",
            )
            return None

        event.update_extend_fields({"log_records": filtered_records})
        return event


class Alerter(AlertHandler):
    def __init__(
        self,
        notice_ways,
        sender=None,
        receivers=None,
    ):
        self.notice_ways = notice_ways
        self.sender = sender
        self.receivers = receivers

    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        status, comment, message = self._alert(event)
        self._update_status(event, status, comment, message)
        return None

    def _alert(self, event: MonitorEvent) -> Tuple[str, str, str]:
        sender = self.get_sender(event)
        receivers = self.get_receivers(event)
        message = self.get_message(event)

        if not receivers:
            return AlarmStatusEnum.FAILURE.value, "告警接收人为空", message

        status = AlarmStatusEnum.SUCCESS.value
        result_messages = []

        for notice_way in self.notice_ways:
            ok, result_message = NoticeWay.send_notice(notice_way, sender, receivers, message)
            result_messages.append(f"{notice_way}: {result_message}")
            if not ok:
                status = AlarmStatusEnum.FAILURE.value

        return status, "\n".join(result_messages), message

    def _update_status(self, event: MonitorEvent, status: str, comment: str = "", message: str = ""):
        AlarmRecord.objects.update_alarm(
            event.alarm_record_id,
            status=status,
            comment=comment,
            message=message,
        )

    def get_sender(self, event: MonitorEvent) -> str:
        return self.sender or DEFAULT_SENDER

    def get_receivers(self, event: MonitorEvent) -> List[str]:
        return self.receivers or []

    def get_message(self, event: MonitorEvent) -> str:
        raise NotImplementedError

    def render_template(self, template: str, **kwargs) -> str:
        return Template(textwrap.dedent(template).strip()).render(Context(kwargs))
