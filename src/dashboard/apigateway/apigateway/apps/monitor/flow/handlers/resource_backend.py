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
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel

from apigateway.apps.monitor.constants import AlarmStatusEnum, ResourceBackendAlarmSubTypeEnum
from apigateway.apps.monitor.flow.handlers.base import Alerter
from apigateway.apps.monitor.flow.helpers import AlertHandler, MonitorEvent
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.utils import time as time_utils
from apigateway.utils.string import truncate_string


class ResourceBackendDimension(BaseModel):
    # NOTE: 数据层面的 api_id, 暂时无法直接修改成 gateway_id
    api_id: int
    resource_id: int
    code_name: str = ""


class ResourceBackendAlarmStrategyEnabledFilter(AlertHandler):
    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        dimension = ResourceBackendDimension.parse_obj(event.event_dimensions)

        alarm_strategies = AlarmStrategy.objects.get_resource_alarm_strategy(
            dimension.api_id,
            dimension.resource_id,
            event.alarm_subtype,
        )

        if not self._is_alarm_enabled(alarm_strategies):
            # 网关监控未开启，过滤，并存储当前的策略
            AlarmRecord.objects.update_alarm(
                event.alarm_record_id,
                alarm_strategies=alarm_strategies,
                status=AlarmStatusEnum.SKIPPED.value,
                comment="网关监控未开启",
            )
            return None

        # 网关监控开启
        enabled_strategies = self._get_enabled_strategies(alarm_strategies)
        event.update_extend_fields(
            {
                "alarm_strategies": enabled_strategies,
            }
        )

        # 告警开启，存储可用的告警策略
        AlarmRecord.objects.update_alarm(
            event.alarm_record_id,
            alarm_strategies=enabled_strategies,
        )
        return event

    def _is_alarm_enabled(self, alarm_strategies: List[AlarmStrategy]) -> bool:
        """
        资源监控告警开启判定规则
        - 策略不存在，默认开启
        """
        if not alarm_strategies:
            return True

        return len(self._get_enabled_strategies(alarm_strategies)) > 0

    def _get_enabled_strategies(self, alarm_strategies: List[AlarmStrategy]) -> List[AlarmStrategy]:
        return [strategy for strategy in alarm_strategies if strategy.enabled]


class ResourceBackendAlerter(Alerter):
    def get_receivers(self, event: MonitorEvent):
        alarm_strategies = event.extend["alarm_strategies"]
        if not alarm_strategies:
            return event.extend["api"].maintainers

        receivers = set()
        for strategy in alarm_strategies:
            receivers.update(strategy.notice_receivers)

        return list(receivers)

    def get_message(self, event: MonitorEvent):
        log_records = event.extend["log_records"]
        record_source = log_records[0]["_source"]

        template = """
        [蓝鲸 API Gateway 告警]

        网关请求后端接口出现错误

        网关名称: {{api_name}}
        部署环境: {{stage}}
        请求信息: {{backend_method}} {{backend_url}}
        错误信息：{{alarm_subtype_label}}
        错误请求次数: {{log_records_count}} 次

        响应状态码: {{status}}
        响应内容:
        {{response_body|safe}}
        请求ID: {{request_id}}

        首次异常时间：{{event_begin_time}}
        事件产生时间：{{event_create_time}}
        您能收到此告警，因为您是该网关负责人，如有疑问，请联系 BK助手(蓝鲸助手)！
        """
        return self.render_template(
            template,
            api_name=record_source["api_name"],
            stage=record_source["stage"],
            backend_method=record_source["backend_method"],
            backend_url=self._get_backend_url(record_source),
            alarm_subtype_label=self._get_alarm_subtype_label(event),
            log_records_count=len(log_records),
            status=record_source["status"],
            response_body=truncate_string(record_source["response_body"] or "", 200) + "...",
            request_id=record_source["request_id"],
            event_begin_time=time_utils.format(event.event_begin_time),
            event_create_time=time_utils.format(event.event_create_time),
        )

    def _get_alarm_subtype_label(self, event: MonitorEvent) -> str:
        label = ResourceBackendAlarmSubTypeEnum.get_choice_label(event.alarm_subtype)
        if label:
            return label

        dimension = ResourceBackendDimension.parse_obj(event.event_dimensions)
        return dimension.code_name or "网关请求后端接口错误"

    def _get_backend_url(self, record_source: Dict[str, Any]) -> str:
        parsed_path = urlparse(record_source["backend_path"])
        path_without_querystring = urlunparse((parsed_path.scheme, parsed_path.netloc, parsed_path.path, "", "", ""))

        return f"{record_source['backend_scheme']}://{record_source['backend_host']}{path_without_querystring}"
