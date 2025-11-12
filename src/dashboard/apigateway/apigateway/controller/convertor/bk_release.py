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

from typing import List

from apigateway.controller.models import BkRelease, GatewayApisixModel
from apigateway.controller.release_data import ReleaseData
from apigateway.utils.time import now_str

from .base import GatewayResourceConvertor


class BkReleaseConvertor(GatewayResourceConvertor):
    def __init__(self, release_data: ReleaseData, publish_id: int):
        super().__init__(release_data=release_data, publish_id=publish_id)

    def convert(self) -> List[GatewayApisixModel]:
        return [
            BkRelease(
                id=f"bk.release.{self.gateway_name}.{self.stage_name}",
                publish_id=self._publish_id,
                publish_time=now_str(),
                apisix_version=self._apisix_version,
                resource_version=self._release_data.resource_version.version,
                labels=self.get_labels(),
            )
        ]
