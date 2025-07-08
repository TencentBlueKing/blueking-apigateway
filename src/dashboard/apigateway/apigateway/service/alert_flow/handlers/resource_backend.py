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
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from django.utils.translation import gettext as _
from pydantic import BaseModel

from apigateway.apps.label.models import ResourceLabel
from apigateway.apps.monitor.constants import AlarmStatusEnum, ResourceBackendAlarmSubTypeEnum
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.common.tenant.request import get_tenant_id_for_gateway_maintainers
from apigateway.service.alert_flow.helpers import AlertHandler, MonitorEvent
from apigateway.utils import time as time_utils
from apigateway.utils.string import truncate_string

from .base import Alerter


class ResourceBackendDimension(BaseModel):
    # NOTE: 数据层面的 api_id, 暂时无法直接修改成 gateway_id
    api_id: int
    resource_id: int
    code_name: str = ""


class ResourceBackendAlarmStrategyEnabledFilter(AlertHandler):
    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        dimension = ResourceBackendDimension.model_validate(event.event_dimensions)

        alarm_strategies = self._get_resource_alarm_strategy(
            gateway_id=dimension.api_id,
            resource_id=dimension.resource_id,
            alarm_subtype=event.alarm_subtype,
        )

        # get the stage of the event, to check if the stage is in the alarm_strategies
        event_stage = event.event_dimensions["stage"]

        if not self._is_alarm_enabled(alarm_strategies, event_stage):
            # 网关监控未开启，过滤，并存储当前的策略
            AlarmRecord.objects.update_alarm(
                event.alarm_record_id,
                alarm_strategies=alarm_strategies,
                status=AlarmStatusEnum.SKIPPED.value,
                comment=_("网关监控未开启 或 事件 stage 未在策略的生效环境列表中"),
            )
            return None

        # 网关监控开启
        enabled_strategies = self._get_enabled_strategies(alarm_strategies, event_stage)
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

    def _is_alarm_enabled(self, alarm_strategies: List[AlarmStrategy], event_stage: str) -> bool:
        """
        资源监控告警开启判定规则
        """
        # legacy 策略不存在，默认开启 True => 2025-04-22 1.16 update to False
        if not alarm_strategies:
            return False

        return len(self._get_enabled_strategies(alarm_strategies, event_stage)) > 0

    def _get_enabled_strategies(self, alarm_strategies: List[AlarmStrategy], event_stage: str) -> List[AlarmStrategy]:
        # condition:
        # 1. the strategy is enabled
        # 2. the event_stage is in the effective_stages
        return [
            strategy for strategy in alarm_strategies if strategy.enabled and strategy.is_effective_stage(event_stage)
        ]

    def _get_resource_alarm_strategy(
        self, gateway_id: int, resource_id: int, alarm_subtype: str
    ) -> List[AlarmStrategy]:
        """
        获取资源绑定的告警策略
        """
        strategies = AlarmStrategy.objects.filter(gateway_id=gateway_id, alarm_subtype=alarm_subtype)
        if not strategies.exists():
            return []

        gateway_label_ids = set(
            (ResourceLabel.objects.filter(resource_id=resource_id).values_list("api_label_id", flat=True))
        )
        matched_strategies = []

        for strategy in strategies:
            strategy_gateway_label_ids = strategy.gateway_label_ids
            if not strategy_gateway_label_ids or set(strategy_gateway_label_ids) & gateway_label_ids:
                matched_strategies.append(strategy)

        return matched_strategies


class ResourceBackendAlerter(Alerter):
    def get_receivers(self, event: MonitorEvent):
        alarm_strategies = event.extend["alarm_strategies"]
        if not alarm_strategies:
            return event.extend["gateway"].maintainers

        receivers = set()
        for strategy in alarm_strategies:
            receivers.update(strategy.notice_receivers)

        return list(receivers)

    def get_tenant_id(self, event: MonitorEvent):
        return get_tenant_id_for_gateway_maintainers(
            event.extend["gateway"].tenant_mode, event.extend["gateway"].tenant_id
        )

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

        status = (
            int(float(record_source["status"]))
            if isinstance(record_source["status"], (int, float))
            else record_source["status"]
        )

        return self.render_template(
            template,
            api_name=record_source["api_name"],
            stage=record_source["stage"],
            backend_method=record_source["backend_method"],
            backend_url=self._get_backend_url(record_source),
            alarm_subtype_label=self._get_alarm_subtype_label(event),
            log_records_count=len(log_records),
            status=status,
            response_body=truncate_string(record_source["response_body"] or "", 256) + "...",
            request_id=record_source["request_id"],
            event_begin_time=time_utils.format(event.event_begin_time),
            event_create_time=time_utils.format(event.event_create_time),
        )

    def _get_alarm_subtype_label(self, event: MonitorEvent) -> str:
        label = ResourceBackendAlarmSubTypeEnum.get_choice_label(event.alarm_subtype)
        if label:
            return label

        dimension = ResourceBackendDimension.model_validate(event.event_dimensions)
        return dimension.code_name or "网关请求后端接口错误"

    def _get_backend_url(self, record_source: Dict[str, Any]) -> str:
        parsed_path = urlparse(record_source["backend_path"])
        path_without_querystring = urlunparse((parsed_path.scheme, parsed_path.netloc, parsed_path.path, "", "", ""))

        return f"{record_source['backend_scheme']}://{record_source['backend_host']}{path_without_querystring}"
