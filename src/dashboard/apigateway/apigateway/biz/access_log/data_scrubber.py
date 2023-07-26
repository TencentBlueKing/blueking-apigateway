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
from typing import Dict, List
from urllib.parse import parse_qs, urlencode

from django.utils.translation import gettext as _

from apigateway.biz.access_log.constants import (
    SENSITIVE_KEYS,
    SENSITIVE_KEYS_MATCH_PATTERN,
    SENSITIVE_KEYS_PART_MATCH_PATTERN,
)
from apigateway.biz.access_log.exceptions import NotScrubbedException

logger = logging.getLogger(__name__)


class DataScrubber:
    """日志中敏感信息擦除"""

    def scrub_sensitive_data(self, logs: List[Dict]) -> List[Dict]:
        for log in logs:
            if "params" in log and self._contains_sensitive_data(log["params"]):
                try:
                    log["params"] = self._scrub_urlencoded_data(log["params"])
                except NotScrubbedException:
                    log["params"] = _("因数据截断或未知数据格式，敏感数据未能过滤，数据暂不展示。")

            if "body" in log and self._contains_sensitive_data(log["body"]):
                try:
                    log["body"] = self._scrub_body(log["body"])
                except NotScrubbedException:
                    log["body"] = _("因数据截断或未知数据格式，敏感数据未能过滤，数据暂不展示。")

        return logs

    def _contains_sensitive_data(self, content: str) -> bool:
        if not content:
            return False

        if SENSITIVE_KEYS_MATCH_PATTERN.search(content) or SENSITIVE_KEYS_PART_MATCH_PATTERN.search(content):
            return True

        return False

    def _scrub_body(self, body: str) -> str:
        body = body.strip()
        # json 数据
        if body.startswith("{"):
            return self._scrub_json_data(body)

        # urlencoded 数据
        if body.find("=") >= 0 and len(body.splitlines()) == 1:
            return self._scrub_urlencoded_data(body)

        raise NotScrubbedException()

    def _scrub_urlencoded_data(self, content: str) -> str:
        try:
            parsed_qs = parse_qs(content, keep_blank_values=True, strict_parsing=True)
        except Exception:
            raise NotScrubbedException()

        scrubbed_content = self._scrub_by_keys(parsed_qs)
        return urlencode(scrubbed_content, doseq=True)

    def _scrub_json_data(self, content: str) -> str:
        try:
            data = json.loads(content)
        except Exception:
            raise NotScrubbedException()

        scrubbed_data = self._scrub_by_keys(data)
        return json.dumps(scrubbed_data)

    def _scrub_by_keys(self, data: Dict) -> Dict:
        scrubbed_data = {}
        for key, value in data.items():
            if value and (key in SENSITIVE_KEYS or SENSITIVE_KEYS_PART_MATCH_PATTERN.search(key)):
                scrubbed_data[key] = "***"
            else:
                scrubbed_data[key] = value
        return scrubbed_data
