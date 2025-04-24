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
from __future__ import absolute_import, unicode_literals

import logging
from typing import Any, Dict

import arrow
from celery import shared_task

from apigateway.apps.monitor.constants import (
    ALARM_RECORD_RETENTION_DAYS,
    API_ERRORLOG_OUTPUT_FIELDS,
    NGINX_ERROR_OUTPUT_FIELDS,
    AlarmTypeEnum,
    NoticeWayEnum,
)
from apigateway.apps.monitor.flow.handlers.app_request import AppRequestAlerter, AppRequestAppCodeRequiredFilter
from apigateway.apps.monitor.flow.handlers.base import AlarmRecordCreator, GatewayExistFilter, RelatedLogRecordsFetcher
from apigateway.apps.monitor.flow.handlers.nginx_error import NginxErrorAlerter
from apigateway.apps.monitor.flow.handlers.resource_backend import (
    ResourceBackendAlarmStrategyEnabledFilter,
    ResourceBackendAlerter,
)
from apigateway.apps.monitor.flow.helpers import AlertFlow, MonitorEvent
from apigateway.apps.monitor.models import AlarmRecord
from apigateway.apps.monitor.utils import get_es_index

logger = logging.getLogger(__name__)


@shared_task(name="apigateway.apps.monitor.tasks.monitor_resource_backend")
def monitor_resource_backend(event_data: Dict[str, Any]):
    """
    监控 API Gateway 请求后端接口的错误，发送告警给网关资源负责人
    """
    alarm_type = AlarmTypeEnum.RESOURCE_BACKEND
    event = MonitorEvent(alarm_type=alarm_type, raw=event_data)

    flow = AlertFlow()
    flow.append(AlarmRecordCreator())
    flow.append(GatewayExistFilter())
    flow.append(ResourceBackendAlarmStrategyEnabledFilter())
    flow.append(RelatedLogRecordsFetcher(es_index=get_es_index(alarm_type), output_fields=API_ERRORLOG_OUTPUT_FIELDS))
    # FIXME: the notice_way should be from the alarm_strategy
    flow.append(ResourceBackendAlerter(notice_ways=[NoticeWayEnum.IM.value, NoticeWayEnum.WECHAT.value]))

    flow.run(events=[event])


@shared_task(name="apigateway.apps.monitor.tasks.monitor_app_request")
def monitor_app_request(event_data: Dict[str, Any]):
    """
    监控蓝鲸应用请求 API Gateway 的错误，发送告警给蓝鲸应用负责人
    """
    alarm_type = AlarmTypeEnum.APP_REQUEST
    event = MonitorEvent(alarm_type=alarm_type, raw=event_data)

    flow = AlertFlow()
    flow.append(AlarmRecordCreator())
    flow.append(GatewayExistFilter())
    flow.append(AppRequestAppCodeRequiredFilter())
    flow.append(RelatedLogRecordsFetcher(es_index=get_es_index(alarm_type), output_fields=API_ERRORLOG_OUTPUT_FIELDS))
    # FIXME: the notice_way should be from the alarm_strategy
    flow.append(AppRequestAlerter(notice_ways=[NoticeWayEnum.IM.value, NoticeWayEnum.WECHAT.value]))

    flow.run(events=[event])


@shared_task(name="apigateway.apps.monitor.tasks.monitor_nginx_error")
def monitor_nginx_error(event_data: Dict[str, Any]):
    """
    通过 Nginx 错误日志，监控 Nginx 到 API Gateway 的错误请求，
    发送告警给 API Gateway 系统管理员
    """
    alarm_type = AlarmTypeEnum.NGINX_ERROR
    event = MonitorEvent(alarm_type=alarm_type, raw=event_data)

    flow = AlertFlow()
    flow.append(AlarmRecordCreator())
    flow.append(RelatedLogRecordsFetcher(es_index=get_es_index(alarm_type), output_fields=NGINX_ERROR_OUTPUT_FIELDS))
    flow.append(NginxErrorAlerter(notice_ways=[NoticeWayEnum.IM.value, NoticeWayEnum.WECHAT.value]))

    flow.run(events=[event])


@shared_task(name="apigateway.apps.monitor.tasks.clear_history_alerts")
def clear_history_alerts():
    """
    清理 X 天前的告警记录
    """
    clear_time = arrow.utcnow().replace(days=-ALARM_RECORD_RETENTION_DAYS)
    AlarmRecord.objects.filter(created_time__lte=clear_time.datetime).delete()


@shared_task(name="apigateway.apps.monitor.tasks.add")
def add():
    logger.info("1 + 1 = 2")
