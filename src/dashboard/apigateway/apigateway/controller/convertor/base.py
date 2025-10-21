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
from abc import ABC, abstractmethod
from typing import List

from apigateway.controller.models import ApisixModel, Labels
from apigateway.controller.release_data import ReleaseData

from .constants import DEFAULT_APISIX_VERSION, LABEL_KEY_APISIX_VERSION, LABEL_KEY_GATEWAY, LABEL_KEY_STAGE


class BaseResourceConvertor(ABC):
    @abstractmethod
    def convert(self):
        raise NotImplementedError()


class GlobalResourceConvertor(BaseResourceConvertor):
    pass


class GatewayResourceConvertor(BaseResourceConvertor):
    def __init__(
        self,
        release_data: ReleaseData,
        apisix_version: str = DEFAULT_APISIX_VERSION,
    ):
        self._release_data = release_data
        self._apisix_version = apisix_version

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

    def get_gateway_resource_labels(self) -> Labels:
        return Labels(
            **{
                LABEL_KEY_GATEWAY: self.gateway_name,
                LABEL_KEY_STAGE: self.stage_name,
                LABEL_KEY_APISIX_VERSION: self._apisix_version,
            }
        )
