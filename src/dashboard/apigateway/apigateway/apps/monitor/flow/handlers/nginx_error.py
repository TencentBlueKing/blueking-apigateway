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
import re
from typing import Any, Dict, List

from django.conf import settings

from apigateway.apps.monitor.flow.handlers.base import Alerter
from apigateway.apps.monitor.flow.helpers import MonitorEvent


class NginxErrorAlerter(Alerter):
    def get_receivers(self, event: MonitorEvent) -> List[str]:
        return settings.APIGW_MANAGERS

    def get_message(self, event: MonitorEvent) -> str:
        log_records = event.extend["log_records"]
        record_source = log_records[0]["_source"]
        line_log = record_source["log"]
        parsed_log = self._parse_log(line_log)
        server = parsed_log.get("server", "")

        template = """
        [蓝鲸 API Gateway 告警]

        API Gateway nginx 5 分钟内出现 10 次以上 error 日志，请关注
        接入层域名：{{server}}
        错误消息：
        {{line_log|safe}}
        """
        return self.render_template(
            template,
            server=server,
            line_log=line_log,
        )

    def _parse_log(self, line_log: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        # 去除日志中的双引号
        log_items = line_log.replace('"', "").split(",")

        # 解析前半段的时间，日志级别，消息内容
        matched = re.match(r"(?P<time>.*) \[(?P<level>.*)\] (?P<msg>.*)", log_items[0])
        if matched:
            result.update(matched.groupdict())

        # 解析后半段的 key:value 数据
        for item in log_items[1:]:
            key, _, value = item.partition(":")
            result[key.strip()] = value.strip()

        return result
