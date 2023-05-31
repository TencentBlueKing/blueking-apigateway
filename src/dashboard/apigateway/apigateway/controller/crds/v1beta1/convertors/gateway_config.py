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
from apigateway.controller.crds.config_controller import create_config_controller
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor
from apigateway.controller.crds.v1beta1.models.gateway_config import BkGatewayConfig, BkGatewayConfigSpec


class GatewayConfigConvertor(BaseConvertor):
    def convert(self) -> BkGatewayConfig:
        return BkGatewayConfig(
            metadata=self._common_metadata(f"bkapi-{self._release_data.gateway.name}"),
            spec=BkGatewayConfigSpec(
                name=self._release_data.gateway.name,
                instance_id=self._micro_gateway.instance_id,
                controller=create_config_controller(self._micro_gateway),
            ),
        )
