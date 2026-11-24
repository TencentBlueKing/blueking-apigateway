#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from typing import Dict, List

from apigateway.utils.log_scrubber import (
    SENSITIVE_KEYS_MATCH_PATTERN,
    SENSITIVE_KEYS_PART_MATCH_PATTERN,
    LogDataScrubber,
)

from .exceptions import NotScrubbedException


class DataScrubber:
    """Compatibility facade for the shared access/MCP log scrubber."""

    def __init__(self):
        self._scrubber = LogDataScrubber()

    def scrub_sensitive_data(self, logs: List[Dict]) -> List[Dict]:
        return [self._scrubber.scrub_log(log) for log in logs]

    def _contains_sensitive_data(self, content: str) -> bool:
        return bool(
            content
            and (SENSITIVE_KEYS_MATCH_PATTERN.search(content) or SENSITIVE_KEYS_PART_MATCH_PATTERN.search(content))
        )

    def _scrub_body(self, body: str) -> str:
        try:
            return self._scrubber.scrub_body(body)
        except ValueError, TypeError, RecursionError:
            raise NotScrubbedException() from None

    def _scrub_urlencoded_data(self, content: str) -> str:
        try:
            return self._scrubber.scrub_form(content)
        except ValueError, TypeError, RecursionError:
            raise NotScrubbedException() from None

    def _scrub_by_keys(self, data: Dict) -> Dict:
        return self._scrubber.scrub_structure(data)
