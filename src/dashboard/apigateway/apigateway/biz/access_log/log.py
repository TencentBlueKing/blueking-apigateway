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

from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from .data_scrubber import DataScrubber
from .log_search import LogSearchClient


class LogHandler:
    @staticmethod
    def add_or_refine_fields(logs: List[Dict]):
        """为日志添加扩展字段"""
        for log in logs:
            if log.get("error"):
                log["response_desc"] = _("网关未请求或请求后端接口异常，响应内容由网关提供。")
            else:
                log["response_desc"] = _("网关已请求后端接口，并将其响应原样返回。")

            if log.get("status") == 200 and log.get("response_body") == "":
                log["response_body"] = _("当状态码为 200 时，不记录响应正文")

        return logs

    @staticmethod
    def search_logs_by_request_id(request_id: str) -> Tuple[int, List[Dict]]:
        """
        根据 request_id 查询日志
        """
        client = LogSearchClient(request_id=request_id)

        total_count, logs = client.search_logs()
        # 去除 params、body 中的敏感数据
        logs = DataScrubber().scrub_sensitive_data(logs)
        logs = LogHandler.add_or_refine_fields(logs)

        return total_count, logs
