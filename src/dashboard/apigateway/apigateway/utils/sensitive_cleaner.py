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
import copy
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SensitiveCleaner:
    """
    处理敏感信息
    """

    sensitive_keys: List[str]

    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = copy.deepcopy(data)
        self._clean(data)
        return data

    def _clean(self, data: Dict[str, Any]):
        for key, value in data.items():
            if isinstance(value, dict):
                self._clean(value)

            elif isinstance(value, list):
                for item in value:
                    self._clean(item)

            elif key in self.sensitive_keys and value:
                data[key] = "***"
