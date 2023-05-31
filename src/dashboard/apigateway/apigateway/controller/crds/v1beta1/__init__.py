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
from typing import TYPE_CHECKING, List, Type

from apigateway.controller.crds.v1beta1.models.gateway_config import BkGatewayConfig
from apigateway.controller.crds.v1beta1.models.gateway_discovery import Endpoint, Operator
from apigateway.controller.crds.v1beta1.models.gateway_plugin_metadata import BkGatewayPluginMetadata
from apigateway.controller.crds.v1beta1.models.gateway_resource import BkGatewayResource
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService
from apigateway.controller.crds.v1beta1.models.gateway_stage import BkGatewayStage
from apigateway.controller.crds.v1beta1.models.gateway_tls import BkGatewayTLS

if TYPE_CHECKING:
    from apigateway.controller.crds.v1beta1.models.base import GatewayCustomResource

__all__ = ["custom_resources"]
custom_resources: List[Type["GatewayCustomResource"]] = [
    BkGatewayConfig,
    BkGatewayResource,
    BkGatewayService,
    BkGatewayStage,
    BkGatewayPluginMetadata,
    Operator,
    Endpoint,
    BkGatewayTLS,
]
