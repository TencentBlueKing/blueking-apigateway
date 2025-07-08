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
from dataclasses import asdict, dataclass
from typing import Any, Dict, Type, TypeVar
from urllib.parse import urlparse

from django.utils.functional import cached_property


class MicroGatewayConfigStructureMixin:
    _micro_gateway_config_key: str

    @classmethod
    def from_micro_gateway_config(cls: Type["T"], config: Dict[str, Any]) -> "T":
        data = config.get(cls._micro_gateway_config_key) or {}
        return cls(**data)

    def to_micro_gateway_config(self) -> Dict[str, Any]:
        return {self._micro_gateway_config_key: asdict(self)}  # type: ignore


T = TypeVar("T", bound=MicroGatewayConfigStructureMixin)


@dataclass
class MicroGatewayJWTAuth(MicroGatewayConfigStructureMixin):
    """微网关实例配置中的 jwt 认证配置"""

    _micro_gateway_config_key = "jwt_auth"

    secret_key: str = ""


@dataclass
class MicroGatewayHTTPInfo(MicroGatewayConfigStructureMixin):
    """微网关实例配置中的 http 配置"""

    _micro_gateway_config_key = "http"

    http_url: str = ""

    @cached_property
    def http_url_info(self):
        return urlparse(self.http_url)
