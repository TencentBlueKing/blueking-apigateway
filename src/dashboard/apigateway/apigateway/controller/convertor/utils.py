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
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional
from urllib.parse import urlparse


def truncate_string(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."


@dataclass
class UrlInfo:
    url: str
    scheme: str = field(init=False)
    domain: str = field(init=False)
    netloc: str = field(init=False)
    port: Optional[int] = field(init=False)
    path: str = field(init=False)
    query: str = field(init=False)
    # NOTE: currently not support grpc/grpcs here
    _default_ports: ClassVar[Dict[str, int]] = {"http": 80, "https": 443}

    def __post_init__(self):
        url_info = urlparse(self.url)
        self.scheme = url_info.scheme
        self.netloc = url_info.netloc
        self.path = url_info.path
        self.query = url_info.query

        host, _, port = url_info.netloc.partition(":")
        self.port = self._choose_port_by_scheme(port)
        self.domain = host

    def _choose_port_by_scheme(self, port: str) -> Optional[int]:
        if port.isdigit():
            return int(port)

        return self._default_ports.get(self.scheme, None)
