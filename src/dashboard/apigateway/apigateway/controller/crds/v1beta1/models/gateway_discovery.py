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
from typing import Any, ClassVar, Dict, List

from pydantic import Field

from apigateway.controller.crds.v1beta1.models.base import (
    GatewayCustomResource,
    GatewayCustomResourceSpec,
    UpstreamNode,
)


class OperatorSpec(GatewayCustomResourceSpec):

    discovery_type: str = Field(default="", alias="discoveryType", description="插件类型")
    config_schema: Dict[str, Any] = Field(
        default_factory=dict,
        alias="configSchema",
        description="服务发现配置 json schema，用于描述 BkGatewayService.externalDiscoveryConfig 的格式，由控制面进行校验",
        helm_value=True,
    )


class Operator(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayOperator"

    spec: OperatorSpec


class EndpointSpec(GatewayCustomResourceSpec):
    nodes: List[UpstreamNode] = Field(default_factory=list, description="URL")


class Endpoint(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayEndpoint"

    spec: EndpointSpec
