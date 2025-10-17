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
import hashlib
from abc import ABC, abstractmethod
from typing import List

from blue_krill.cubing_case import shortcuts

from apigateway.controller.models import ApisixModel
from apigateway.controller.release_data import ReleaseData


class BaseResourceConvertor(ABC):
    @abstractmethod
    def convert(self):
        return NotImplementedError()


class GlobalResourceConvertor(BaseResourceConvertor):
    pass


class GatewayResourceConvertor(BaseResourceConvertor):
    def __init__(
        self,
        release_data: ReleaseData,
    ):
        self._release_data = release_data

    @property
    def gateway(self):
        return self._release_data.gateway

    @property
    def gateway_id(self) -> int:
        return self._release_data.gateway.pk

    @property
    def gateway_name(self) -> str:
        return self._release_data.gateway.name

    @property
    def stage(self):
        return self._release_data.stage

    @property
    def stage_name(self) -> str:
        return self._release_data.stage.name

    @property
    def stage_id(self) -> int:
        return self._release_data.stage.pk

    @abstractmethod
    def convert(self) -> List[ApisixModel]:
        raise NotImplementedError()

    def common_labels(self):
        return {
            "gateway.bk.tencent.com/gateway": self.gateway_name,
            "gateway.bk.tencent.com/stage": self.stage_name,
        }

    # FIXME: is this necessary?
    # metadata.name 是在 operator 中有什么作用吗？
    def gen_unique_name(self, name: str) -> str:
        key = shortcuts.to_lower_dash_case(f"{self.gateway_name}-{self.stage_name}-{name}")
        if len(key) > 64:
            md5 = hashlib.md5(key[55:].encode())
            key = f"{key[:55]}.{md5.hexdigest()[:8]}"  # 55 + 1 + 8

        return key
