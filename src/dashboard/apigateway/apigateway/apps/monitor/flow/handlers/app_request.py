# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

from apigateway.apps.monitor.constants import AlarmStatusEnum
from apigateway.apps.monitor.flow.handlers.base import Alerter
from apigateway.apps.monitor.flow.helpers import AlertHandler, MonitorEvent
from apigateway.apps.monitor.models import AlarmRecord
from apigateway.apps.monitor.utils import get_app_maintainers
from apigateway.utils import time as time_utils


class AppRequestDimension(BaseModel):
    # NOTE: 数据层面的 api_id, 暂时无法直接修改成 gateway_id
    api_id: int
    resource_id: int
    stage: str
    app_code: str


# NOTE: 这里是蓝鲸应用请求网关报错，告警给蓝鲸应用负责人，被动，无法配置/忽略
# FIXME: 理论上，只应该告警 prod 的？其他环境的不告警？
# 或者应该提供一个入口让开发者可以配置？


class AppRequestAppCodeRequiredFilter(AlertHandler):
    def _do(self, event: MonitorEvent) -> Optional[MonitorEvent]:
        dimension = AppRequestDimension.parse_obj(event.event_dimensions)

        # app_code 非空，不过滤
        if dimension.app_code:
            return event

        # app_code 为空，过滤
        AlarmRecord.objects.update_alarm(
            event.alarm_record_id,
            status=AlarmStatusEnum.SKIPPED.value,
            comment="app_code 为空",
        )
        return None


class AppRequestAlerter(Alerter):
    def get_receivers(self, event: MonitorEvent) -> List[str]:
        dimension = AppRequestDimension.parse_obj(event.event_dimensions)
        return get_app_maintainers(dimension.app_code)

    def get_message(self, event: MonitorEvent) -> str:
        log_records = event.extend["log_records"]
        record_source = log_records[0]["_source"]

        template = """
        [蓝鲸 API Gateway 告警]

        蓝鲸应用访问网关 API 出现错误

        网关名称：{{api_name}}
        部署环境：{{stage}}
        请求来源：蓝鲸应用【{{app_code}}】
        请求信息：{{request_info}}
        错误信息：
        {{error|safe}}
        请求来源 IP: {{client_ip}}
        请求 ID: {{request_id}}

        首次异常时间：{{event_begin_time}}
        事件产生时间：{{event_create_time}}
        您能收到此告警，因为您是该应用负责人，如有疑问，请联系 BK助手！
        """
        return self.render_template(
            template,
            app_code=record_source["app_code"],
            api_name=record_source["api_name"],
            stage=record_source["stage"],
            request_info=self._get_request_info(record_source),
            client_ip=record_source["client_ip"],
            error=record_source["error"],
            request_id=record_source["request_id"],
            event_begin_time=time_utils.format(event.event_begin_time),
            event_create_time=time_utils.format(event.event_create_time),
        )

    def _get_request_info(self, record_source: Dict[str, Any]) -> str:
        parsed_path = urlparse(record_source["http_path"])
        path_without_querystring = urlunparse((parsed_path.scheme, parsed_path.netloc, parsed_path.path, "", "", ""))

        return "{}, {}, {}".format(
            record_source["method"],
            record_source["http_host"],
            path_without_querystring,
        )
