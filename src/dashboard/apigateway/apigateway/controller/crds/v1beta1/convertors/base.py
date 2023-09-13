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
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Optional
from urllib.parse import urlparse

from blue_krill.cubing_case import shortcuts

from apigateway.controller.crds.base import KubernetesResourceMetadata
from apigateway.controller.crds.release_data.release_data import ReleaseData
from apigateway.core.models import MicroGateway


@dataclass
class UrlInfo:
    url: str
    scheme: str = field(init=False)
    domain: str = field(init=False)
    netloc: str = field(init=False)
    port: Optional[int] = field(init=False)
    path: str = field(init=False)
    query: str = field(init=False)
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


class BaseConvertor(ABC):
    def __init__(self, release_data: ReleaseData, micro_gateway: MicroGateway):
        self._release_data = release_data
        self._micro_gateway = micro_gateway

    @abstractmethod
    def convert(self):
        return NotImplementedError()

    def _common_metadata(self, name: str, labels: Optional[Dict[str, str]] = None) -> KubernetesResourceMetadata:
        gateway = self._release_data.gateway.name
        stage = self._release_data.stage.name
        metadata = KubernetesResourceMetadata()

        labels = labels or {}
        labels.update(
            {
                "gateway": gateway,
                "stage": stage,
            }
        )
        metadata.add_labels(labels)

        key = shortcuts.to_lower_dash_case(f"{gateway}-{stage}-{name}")
        if len(key) > 64:
            md5 = hashlib.md5(key[55:].encode())
            key = f"{key[:55]}.{md5.hexdigest()[:8]}"  # 55 + 1 + 8

        metadata.name = key

        return metadata

    def _convert_http_rewrite_headers(self, transform_headers: Optional[Dict[str, Any]]) -> Dict[str, str]:
        headers: Dict[str, str] = {}

        if transform_headers:
            headers.update(transform_headers.get("set") or {})
            # 为空表示删除
            headers.update(dict.fromkeys(transform_headers.get("delete") or [], ""))

        return headers
